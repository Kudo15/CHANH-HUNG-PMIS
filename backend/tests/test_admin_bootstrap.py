import base64
import hashlib
import json
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.bootstrap_admins import (
    BootstrapError,
    bootstrap_initial_admins,
    create_canonical_payload,
)
from app.auth.models import AdminBootstrapReceipt, User, UserRole
from app.database import Base


def generate_ed25519_keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv, pub, base64.b64encode(pub_bytes).decode("ascii")


def sign_payload(private_key: Ed25519PrivateKey, payload: bytes) -> str:
    signature = private_key.sign(payload)
    return base64.b64encode(signature).decode("ascii")


def get_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal, engine


def create_user(db, sub: str, is_active: bool = True) -> User:
    user = User(
        id=str(uuid.uuid4()),
        sub=sub,
        email=f"{sub}@example.com",
        name=f"User {sub}",
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_canonical_payload_format():
    payload1 = create_canonical_payload("local", ["sub-a", "sub-b"])
    payload2 = create_canonical_payload("local", ["sub-a", "sub-b"])
    assert payload1 == payload2
    data = json.loads(payload1.decode("utf-8"))
    assert data["environment"] == "local"
    assert data["target_subs"] == ["sub-a", "sub-b"]


def test_bootstrap_success():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            u1 = create_user(db, "kc-user-1")
            u2 = create_user(db, "kc-user-2")

            po_priv, po_pub, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, sr_pub, sr_pub_b64 = generate_ed25519_keypair()

            env = "development"
            targets = ["kc-user-1", "kc-user-2"]
            payload = create_canonical_payload(env, targets)

            po_sig_b64 = sign_payload(po_priv, payload)
            sr_sig_b64 = sign_payload(sr_priv, payload)

            receipt = bootstrap_initial_admins(
                db,
                environment=env,
                target_subs=targets,
                approvals={
                    "project_owner": po_sig_b64,
                    "security_reviewer": sr_sig_b64,
                },
                approver_public_keys={
                    "project_owner": po_pub_b64,
                    "security_reviewer": sr_pub_b64,
                },
            )

            assert receipt is not None
            assert receipt.environment == env
            assert receipt.target_sub1 == "kc-user-1"
            assert receipt.target_sub2 == "kc-user-2"
            assert receipt.target_user1_id == u1.id
            assert receipt.target_user2_id == u2.id
            assert receipt.consumed is True

            # Verify no secrets in receipt
            assert po_sig_b64 not in receipt.payload_digest
            assert sr_sig_b64 not in receipt.payload_digest
            expected_digest = hashlib.sha256(payload).hexdigest()
            assert receipt.payload_digest == expected_digest

            # Verify UserRole entries
            roles = db.query(UserRole).all()
            assert len(roles) == 2
            role_map = {r.user_id: r for r in roles}
            assert u1.id in role_map
            assert u2.id in role_map
            for r in roles:
                assert r.role == "System Admin"
                assert r.granted_by is None
                assert r.second_admin_id is None
                assert r.bootstrap_receipt_id == receipt.id
    finally:
        engine.dispose()


def test_bootstrap_rejects_wrong_target_count():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            with pytest.raises(BootstrapError, match="exactly two"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1"],
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_duplicate_targets():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            _, _, po_pub_b64 = generate_ed25519_keypair()
            _, _, sr_pub_b64 = generate_ed25519_keypair()

            with pytest.raises(BootstrapError, match="distinct"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-1"],
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_nonexistent_or_inactive_user():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1", is_active=False)
            create_user(db, "kc-user-2", is_active=True)
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            payload = create_canonical_payload("local", ["kc-user-1", "kc-user-2"])
            po_sig = sign_payload(po_priv, payload)
            sr_sig = sign_payload(sr_priv, payload)

            # Inactive user
            with pytest.raises(BootstrapError, match="inactive"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )

            # Nonexistent user
            with pytest.raises(BootstrapError, match="not found"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-2", "kc-user-nonexistent"],
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_preexisting_admin():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            u3 = create_user(db, "kc-user-3")

            # Insert an existing System Admin
            existing_role = UserRole(
                user_id=u3.id,
                role="System Admin",
                granted_by=u3.id,
            )
            db.add(existing_role)
            db.commit()

            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()
            payload = create_canonical_payload("local", ["kc-user-1", "kc-user-2"])

            with pytest.raises(BootstrapError, match="System Admin already exists"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={
                        "project_owner": sign_payload(po_priv, payload),
                        "security_reviewer": sign_payload(sr_priv, payload),
                    },
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_same_person_approver_keys():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            priv, _, pub_b64 = generate_ed25519_keypair()

            payload = create_canonical_payload("local", ["kc-user-1", "kc-user-2"])
            sig = sign_payload(priv, payload)

            with pytest.raises(BootstrapError, match="distinct"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={"project_owner": sig, "security_reviewer": sig},
                    approver_public_keys={
                        "project_owner": pub_b64,
                        "security_reviewer": pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_invalid_signature():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            payload = create_canonical_payload("local", ["kc-user-1", "kc-user-2"])
            po_sig = sign_payload(po_priv, payload)

            # Corrupted SR signature
            bad_sig = base64.b64encode(b"corrupted-signature-bytes-12345678").decode("ascii")

            with pytest.raises(BootstrapError, match="signature"):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={"project_owner": po_sig, "security_reviewer": bad_sig},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_mismatched_payload_environment():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            # Sign for "staging", but execute for "development"
            payload_staging = create_canonical_payload("staging", ["kc-user-1", "kc-user-2"])
            po_sig = sign_payload(po_priv, payload_staging)
            sr_sig = sign_payload(sr_priv, payload_staging)

            with pytest.raises(BootstrapError, match="signature"):
                bootstrap_initial_admins(
                    db,
                    environment="development",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_replay_rejection():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            payload = create_canonical_payload("local", ["kc-user-1", "kc-user-2"])
            po_sig = sign_payload(po_priv, payload)
            sr_sig = sign_payload(sr_priv, payload)

            # First run succeeds
            receipt = bootstrap_initial_admins(
                db,
                environment="local",
                target_subs=["kc-user-1", "kc-user-2"],
                approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                approver_public_keys={
                    "project_owner": po_pub_b64,
                    "security_reviewer": sr_pub_b64,
                },
            )
            assert receipt is not None

            # Second run fails on zero-admin / receipt lock
            with pytest.raises(BootstrapError):
                bootstrap_initial_admins(
                    db,
                    environment="local",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )
    finally:
        engine.dispose()


def test_bootstrap_cli_rejection_nonzero_exit():
    from app.auth.bootstrap_admins import main

    # Missing arguments -> exits 2 via argparse
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_bootstrap_atomic_rollback_on_fault_injection():
    """Verify atomicity: injected failure after flush but before commit rolls back all changes.

    Database dialect: SQLite in-memory (StaticPool). Note: SQLite test evidence
    demonstrates the application transaction boundary and rollback handling,
    but does not prove PostgreSQL-specific concurrent locking or behavior.
    """
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            u1 = create_user(db, "kc-user-1")
            u2 = create_user(db, "kc-user-2")
            u1_id = u1.id
            u2_id = u2.id
            po_priv, _, po_pub_b64 = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64 = generate_ed25519_keypair()

            env = "development"
            targets = ["kc-user-1", "kc-user-2"]
            payload = create_canonical_payload(env, targets)
            po_sig_b64 = sign_payload(po_priv, payload)
            sr_sig_b64 = sign_payload(sr_priv, payload)

            injection_reached = False

            def faulty_commit():
                nonlocal injection_reached
                # 1. Prove at least one bootstrap write (the receipt)
                # has flushed to the active transaction
                flushed_receipts = db.query(AdminBootstrapReceipt).all()
                assert len(flushed_receipts) == 1
                assert flushed_receipts[0].target_sub1 == "kc-user-1"
                assert flushed_receipts[0].target_sub2 == "kc-user-2"
                assert flushed_receipts[0].single_bootstrap_lock == "BOOTSTRAP_LOCK"
                assert flushed_receipts[0].id is not None

                # 2. Mark injection point reached and raise simulated mid-transaction failure
                injection_reached = True
                raise RuntimeError("Injected database failure after flush but before commit")

            # Inject the fault into the active session
            db.commit = faulty_commit

            with pytest.raises(
                BootstrapError, match="Atomic bootstrap transaction failed"
            ) as exc_info:
                bootstrap_initial_admins(
                    db,
                    environment=env,
                    target_subs=targets,
                    approvals={
                        "project_owner": po_sig_b64,
                        "security_reviewer": sr_sig_b64,
                    },
                    approver_public_keys={
                        "project_owner": po_pub_b64,
                        "security_reviewer": sr_pub_b64,
                    },
                )

            # Prove the injection point and exception were actually reached
            assert injection_reached is True
            assert "Injected database failure after flush but before commit" in str(exc_info.value)

        # 3. Verify via a fresh session that rollback was clean and complete
        with SessionLocal() as fresh_db:
            # Neither receipt nor System Admin roles persisted
            persisted_receipts = fresh_db.query(AdminBootstrapReceipt).all()
            assert len(persisted_receipts) == 0

            persisted_admin_roles = (
                fresh_db.query(UserRole).filter(UserRole.role == "System Admin").all()
            )
            assert len(persisted_admin_roles) == 0

            total_roles = fresh_db.query(UserRole).all()
            assert len(total_roles) == 0

            # Target users still exist and were not corrupted
            user1 = fresh_db.query(User).filter_by(sub="kc-user-1").first()
            user2 = fresh_db.query(User).filter_by(sub="kc-user-2").first()
            assert user1 is not None and user1.id == u1_id
            assert user2 is not None and user2.id == u2_id
    finally:
        engine.dispose()
