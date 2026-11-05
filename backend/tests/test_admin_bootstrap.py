import base64
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.bootstrap_admins import (
    MAX_STDIN_BYTES,
    REG_BINARY,
    REGISTRY_NAMESPACE_PATH,
    REGISTRY_ROOT_PATH,
    REGISTRY_TRUST_KEY_PATH,
    VAL_PROJECT_OWNER,
    VAL_SECURITY_REVIEWER,
    BootstrapError,
    SyntheticRegistryBackend,
    bootstrap_initial_admins,
    create_canonical_payload,
    get_or_create_instance_state,
    parse_iso_utc,
    run_bootstrap_from_stdin,
)
from app.auth.models import (
    AdminBootstrapInstanceState,
    AdminBootstrapReceipt,
    User,
    UserRole,
)
from app.auth.policy import Role
from app.database import Base


def generate_ed25519_keypair():
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv, pub, base64.b64encode(pub_bytes).decode("ascii"), pub_bytes


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


def make_valid_synthetic_registry(po_bytes: bytes, sr_bytes: bytes) -> SyntheticRegistryBackend:
    from app.auth.bootstrap_admins import (
        APPROVED_TASK_KEY_SDDL,
        KEY_ALL_ACCESS,
        KEY_READ,
        SID_BUILTIN_ADMINISTRATORS,
        SID_BUILTIN_USERS,
        SID_LOCAL_SYSTEM,
    )

    valid_aces = [
        {
            "type": "ACCESS_ALLOWED",
            "flags": 0,
            "mask": KEY_ALL_ACCESS,
            "trustee_sid": SID_LOCAL_SYSTEM,
        },
        {
            "type": "ACCESS_ALLOWED",
            "flags": 0,
            "mask": KEY_ALL_ACCESS,
            "trustee_sid": SID_BUILTIN_ADMINISTRATORS,
        },
        {
            "type": "ACCESS_ALLOWED",
            "flags": 0,
            "mask": KEY_READ,
            "trustee_sid": SID_BUILTIN_USERS,
        },
    ]

    keys = {
        REGISTRY_ROOT_PATH: {
            "dacl_present": True,
            "dacl_protected": False,
            "prohibited_rights_granted": False,
        },
        REGISTRY_NAMESPACE_PATH: {
            "dacl_present": True,
            "dacl_protected": True,
            "owner_sid": SID_BUILTIN_ADMINISTRATORS,
            "dacl_aces": [dict(ace) for ace in valid_aces],
            "sddl": APPROVED_TASK_KEY_SDDL,
            "prohibited_rights_granted": False,
        },
        REGISTRY_TRUST_KEY_PATH: {
            "dacl_present": True,
            "dacl_protected": True,
            "owner_sid": SID_BUILTIN_ADMINISTRATORS,
            "dacl_aces": [dict(ace) for ace in valid_aces],
            "sddl": APPROVED_TASK_KEY_SDDL,
            "prohibited_rights_granted": False,
            "values": {
                VAL_PROJECT_OWNER: (REG_BINARY, po_bytes),
                VAL_SECURITY_REVIEWER: (REG_BINARY, sr_bytes),
            },
        },
    }
    return SyntheticRegistryBackend(is_windows=True, keys=keys)


def make_valid_payload_data(
    instance_id: str,
    *,
    environment: str = "development",
    target_subs: list[str] | None = None,
    now: datetime | None = None,
) -> dict:
    if now is None:
        now = datetime.now(timezone.utc)
    issued_dt = now - timedelta(hours=1)
    expires_dt = now + timedelta(hours=5)

    return {
        "action": "bootstrap_initial_admins",
        "environment": environment,
        "target_subs": target_subs or ["kc-user-1", "kc-user-2"],
        "instance_id": instance_id,
        "request_id": str(uuid.uuid4()),
        "operator_id": "synthetic-operator-1",
        "issued_at": issued_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------------------
# Tests: Canonical Payload Formatting & Parsing
# ---------------------------------------------------------------------------
def test_canonical_payload_format():
    now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    p1 = create_canonical_payload(
        "local",
        ["sub-a", "sub-b"],
        instance_id="inst-1",
        request_id="req-1",
        operator_id="op-1",
        issued_at=now,
        expires_at=now + timedelta(hours=2),
    )
    p2 = create_canonical_payload(
        "local",
        ["sub-a", "sub-b"],
        instance_id="inst-1",
        request_id="req-1",
        operator_id="op-1",
        issued_at="2026-10-31T12:00:00Z",
        expires_at="2026-10-31T14:00:00Z",
    )
    assert p1 == p2
    data = json.loads(p1.decode("utf-8"))
    assert data["action"] == "bootstrap_initial_admins"
    assert data["environment"] == "local"
    assert data["target_subs"] == ["sub-a", "sub-b"]
    assert data["instance_id"] == "inst-1"
    assert data["request_id"] == "req-1"
    assert data["operator_id"] == "op-1"
    assert data["issued_at"] == "2026-10-31T12:00:00Z"
    assert data["expires_at"] == "2026-10-31T14:00:00Z"


def test_parse_iso_utc():
    # Valid Z
    dt = parse_iso_utc("2026-10-31T12:00:00Z")
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 12

    # Valid +00:00
    dt2 = parse_iso_utc("2026-10-31T12:00:00+00:00")
    assert dt2.tzinfo == timezone.utc

    # Reject non-UTC or missing timezone
    with pytest.raises(BootstrapError, match="explicit UTC format"):
        parse_iso_utc("2026-10-31T12:00:00")

    with pytest.raises(BootstrapError, match="explicit UTC format"):
        parse_iso_utc("2026-10-31T12:00:00+07:00")


def test_canonical_payload_validations():
    now = datetime.now(timezone.utc)
    # Reject > 24 hours validity
    with pytest.raises(BootstrapError, match="exceeds 24 hours"):
        create_canonical_payload(
            "local",
            ["sub-1", "sub-2"],
            instance_id="inst-1",
            request_id="req-1",
            operator_id="op-1",
            issued_at=now,
            expires_at=now + timedelta(hours=25),
        )

    # Reject expires_at <= issued_at
    with pytest.raises(BootstrapError, match="strictly greater"):
        create_canonical_payload(
            "local",
            ["sub-1", "sub-2"],
            instance_id="inst-1",
            request_id="req-1",
            operator_id="op-1",
            issued_at=now,
            expires_at=now - timedelta(minutes=1),
        )

    # Reject duplicate target subs
    with pytest.raises(BootstrapError, match="distinct"):
        create_canonical_payload(
            "local",
            ["sub-1", "sub-1"],
            instance_id="inst-1",
            request_id="req-1",
            operator_id="op-1",
            issued_at=now,
            expires_at=now + timedelta(hours=2),
        )


# ---------------------------------------------------------------------------
# Tests: Instance State Persistence
# ---------------------------------------------------------------------------
def test_instance_state_singleton():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            s1 = get_or_create_instance_state(db)
            assert s1.instance_id is not None
            assert s1.singleton_lock == "INSTANCE_LOCK"

            # Querying again returns the exact same row and instance_id
            s2 = get_or_create_instance_state(db)
            assert s2.instance_id == s1.instance_id
            assert s2.id == s1.id

            count = db.query(AdminBootstrapInstanceState).count()
            assert count == 1
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Successful Bootstrap with Synthetic Registry
# ---------------------------------------------------------------------------
def test_bootstrap_success():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            u1 = create_user(db, "kc-user-1")
            u2 = create_user(db, "kc-user-2")

            po_priv, _, po_pub_b64, po_bytes = generate_ed25519_keypair()
            sr_priv, _, sr_pub_b64, sr_bytes = generate_ed25519_keypair()

            inst = get_or_create_instance_state(db)
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)

            receipt = bootstrap_initial_admins(
                db,
                payload_data=payload_data,
                approvals={
                    "project_owner": po_sig,
                    "security_reviewer": sr_sig,
                },
                now=now,
                _registry_backend=backend,
            )

            assert receipt is not None
            assert receipt.environment == "development"
            assert receipt.target_sub1 == "kc-user-1"
            assert receipt.target_sub2 == "kc-user-2"
            assert receipt.target_user1_id == u1.id
            assert receipt.target_user2_id == u2.id
            assert receipt.instance_id == inst.instance_id
            assert receipt.request_id == payload_data["request_id"]
            assert receipt.operator_id == "synthetic-operator-1"
            assert receipt.consumed is True

            # Verify no secrets in receipt
            assert po_sig not in receipt.payload_digest
            assert sr_sig not in receipt.payload_digest
            expected_digest = hashlib.sha256(canonical_bytes).hexdigest()
            assert receipt.payload_digest == expected_digest

            # Verify UserRole entries
            roles = db.query(UserRole).all()
            assert len(roles) == 2
            role_map = {r.user_id: r for r in roles}
            assert u1.id in role_map
            assert u2.id in role_map
            for r in roles:
                assert r.role == Role.SYSTEM_ADMIN.value
                assert r.role == "system_admin"
                assert r.granted_by is None
                assert r.second_admin_id is None
                assert r.bootstrap_receipt_id == receipt.id
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Registry Trust Source Fail-Closed Checks
# ---------------------------------------------------------------------------
def test_registry_fails_closed_on_non_windows():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            backend = SyntheticRegistryBackend(is_windows=False)
            with pytest.raises(BootstrapError, match="supported only on Windows"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_missing_key():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            backend = SyntheticRegistryBackend(is_windows=True, keys={})
            with pytest.raises(BootstrapError, match="key not found"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_wrong_value_count():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, po_bytes)
            # Remove security reviewer key so count is 1
            del backend.keys[REGISTRY_TRUST_KEY_PATH]["values"][VAL_SECURITY_REVIEWER]

            with pytest.raises(BootstrapError, match="exactly 2 values"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_unexpected_value_name():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, po_bytes)
            backend.keys[REGISTRY_TRUST_KEY_PATH]["values"]["UnexpectedKey"] = (
                REG_BINARY,
                po_bytes,
            )
            del backend.keys[REGISTRY_TRUST_KEY_PATH]["values"][VAL_SECURITY_REVIEWER]

            with pytest.raises(BootstrapError, match="Unexpected value names"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_wrong_value_type():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            # Set type to REG_SZ (1) instead of REG_BINARY (3)
            backend.keys[REGISTRY_TRUST_KEY_PATH]["values"][VAL_PROJECT_OWNER] = (1, po_bytes)

            with pytest.raises(BootstrapError, match="REG_BINARY"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_wrong_key_length():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(b"short-key", sr_bytes)

            with pytest.raises(BootstrapError, match="exactly 32 bytes"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_same_person_approver_keys():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            # Identical bytes for both approver keys
            backend = make_valid_synthetic_registry(po_bytes, po_bytes)

            with pytest.raises(BootstrapError, match="distinct"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_unprotected_dacl():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            # Make task-created namespace unprotected
            backend.keys[REGISTRY_NAMESPACE_PATH]["dacl_protected"] = False

            with pytest.raises(BootstrapError, match="protected DACL"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_missing_dacl():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_present"] = False

            with pytest.raises(BootstrapError, match="no DACL"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_prohibited_rights():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            # Simulate token has write / modify rights on trust key
            backend.keys[REGISTRY_TRUST_KEY_PATH]["prohibited_rights_granted"] = True

            with pytest.raises(BootstrapError, match="prohibited right"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_token_duplicate_failure():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            backend.token_duplicate_fails = True

            with pytest.raises(BootstrapError, match="duplicate process token"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_registry_rejects_access_check_error():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)
            payload_data = make_valid_payload_data(inst.instance_id)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
            backend.keys[REGISTRY_TRUST_KEY_PATH]["access_check_error"] = "Simulated API failure"

            with pytest.raises(BootstrapError, match="AccessCheck failed"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Instance and Time Boundary Validation
# ---------------------------------------------------------------------------
def test_bootstrap_rejects_instance_id_mismatch():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            get_or_create_instance_state(db)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            # Different instance_id in payload
            payload_data = make_valid_payload_data("mismatched-instance-uuid")

            with pytest.raises(BootstrapError, match="does not match authoritative"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_future_issued_at():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
            # issued_at is 1 hour in the future relative to `now`
            payload_data = make_valid_payload_data(inst.instance_id)
            payload_data["issued_at"] = "2026-10-31T13:00:00Z"
            payload_data["expires_at"] = "2026-10-31T15:00:00Z"

            with pytest.raises(BootstrapError, match="future"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_expired_approval():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime(2026, 10, 31, 16, 0, 0, tzinfo=timezone.utc)
            # expired at 15:00:00Z
            payload_data = make_valid_payload_data(inst.instance_id)
            payload_data["issued_at"] = "2026-10-31T12:00:00Z"
            payload_data["expires_at"] = "2026-10-31T15:00:00Z"

            with pytest.raises(BootstrapError, match="expired"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Target Validation, Pre-existing Admin, Replay
# ---------------------------------------------------------------------------
def test_bootstrap_rejects_wrong_target_count():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            inst = get_or_create_instance_state(db)
            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            payload_data = make_valid_payload_data(inst.instance_id, target_subs=["kc-user-1"])
            with pytest.raises(BootstrapError, match="exactly two"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_duplicate_targets():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            inst = get_or_create_instance_state(db)
            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            payload_data = make_valid_payload_data(
                inst.instance_id, target_subs=["kc-user-1", "kc-user-1"]
            )
            with pytest.raises(BootstrapError, match="distinct"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_nonexistent_or_inactive_user():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1", is_active=False)
            create_user(db, "kc-user-2", is_active=True)
            inst = get_or_create_instance_state(db)

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            payload_data = make_valid_payload_data(inst.instance_id)

            # Inactive user
            with pytest.raises(BootstrapError, match="inactive"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )

            # Nonexistent user
            payload_data["target_subs"] = ["kc-user-2", "kc-user-nonexistent"]
            with pytest.raises(BootstrapError, match="not found"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_preexisting_legacy_display_value_admin():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            u3 = create_user(db, "kc-user-3")
            inst = get_or_create_instance_state(db)

            # Insert an inert legacy display-value System Admin row
            existing_role = UserRole(
                user_id=u3.id,
                role="System Admin",
                granted_by=u3.id,
            )
            db.add(existing_role)
            db.commit()

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            payload_data = make_valid_payload_data(inst.instance_id)
            with pytest.raises(BootstrapError, match="System Admin already exists"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_preexisting_canonical_admin():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            u3 = create_user(db, "kc-user-3")
            inst = get_or_create_instance_state(db)

            # Insert an existing canonical System Admin row
            existing_role = UserRole(
                user_id=u3.id,
                role=Role.SYSTEM_ADMIN.value,
                granted_by=u3.id,
            )
            db.add(existing_role)
            db.commit()

            _, _, _, po_bytes = generate_ed25519_keypair()
            _, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            payload_data = make_valid_payload_data(inst.instance_id)
            with pytest.raises(BootstrapError, match="System Admin already exists"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": "sig", "security_reviewer": "sig"},
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_invalid_signature():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            # Corrupted SR signature
            bad_sig = base64.b64encode(b"corrupted-signature-bytes-12345678").decode("ascii")

            with pytest.raises(BootstrapError, match="signature"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": po_sig, "security_reviewer": bad_sig},
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_rejects_mismatched_payload_environment():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, environment="staging", now=now)
            canonical_staging = create_canonical_payload(
                "staging",
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )
            po_sig = sign_payload(po_priv, canonical_staging)
            sr_sig = sign_payload(sr_priv, canonical_staging)

            # Change environment in payload to development after signing
            payload_data["environment"] = "development"
            with pytest.raises(BootstrapError, match="signature"):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


def test_bootstrap_replay_rejection():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)

            # First run succeeds
            receipt = bootstrap_initial_admins(
                db,
                payload_data=payload_data,
                approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                now=now,
                _registry_backend=backend,
            )
            assert receipt is not None

            # Second run fails on zero-admin / receipt lock
            with pytest.raises(BootstrapError):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                    now=now,
                    _registry_backend=backend,
                )
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Stdin Bounded Ingestion
# ---------------------------------------------------------------------------
def test_bootstrap_stdin_ingestion_success():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)

            input_data = json.dumps(
                {
                    "payload": payload_data,
                    "signatures": {
                        "project_owner": po_sig,
                        "security_reviewer": sr_sig,
                    },
                }
            )

            receipt = run_bootstrap_from_stdin(db, input_data, now=now, _registry_backend=backend)
            assert receipt is not None
            assert receipt.target_sub1 == "kc-user-1"
            assert receipt.target_sub2 == "kc-user-2"
    finally:
        engine.dispose()


def test_bootstrap_stdin_ingestion_size_limit():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            large_input = " " * (MAX_STDIN_BYTES + 10)
            with pytest.raises(BootstrapError, match="maximum allowed size"):
                run_bootstrap_from_stdin(db, large_input)
    finally:
        engine.dispose()


def test_bootstrap_stdin_ingestion_malformed_json():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            with pytest.raises(BootstrapError, match="Invalid JSON"):
                run_bootstrap_from_stdin(db, "not valid json { [")
    finally:
        engine.dispose()


def test_bootstrap_stdin_ingestion_missing_sections():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            with pytest.raises(BootstrapError, match="Missing 'payload'"):
                run_bootstrap_from_stdin(db, json.dumps({"signatures": {}}))

            with pytest.raises(BootstrapError, match="Missing 'signatures'"):
                run_bootstrap_from_stdin(db, json.dumps({"payload": {}}))
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: DB-Level Receipt Protection (Trigger)
# ---------------------------------------------------------------------------
def test_bootstrap_receipt_immutability_at_db_level():
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            # Install SQLite triggers mimicking migration 0006 for dialect SQLite
            db.execute(
                text(
                    """
                    CREATE TRIGGER trg_protect_admin_bootstrap_receipts_update
                    BEFORE UPDATE ON admin_bootstrap_receipts
                    BEGIN
                        SELECT RAISE(ABORT, 'admin_bootstrap_receipts rows are immutable');
                    END;
                    """
                )
            )
            db.execute(
                text(
                    """
                    CREATE TRIGGER trg_protect_admin_bootstrap_receipts_delete
                    BEFORE DELETE ON admin_bootstrap_receipts
                    BEGIN
                        SELECT RAISE(ABORT, 'admin_bootstrap_receipts rows are immutable');
                    END;
                    """
                )
            )
            db.commit()

            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)

            receipt = bootstrap_initial_admins(
                db,
                payload_data=payload_data,
                approvals={"project_owner": po_sig, "security_reviewer": sr_sig},
                now=now,
                _registry_backend=backend,
            )
            assert receipt is not None

            # Attempt direct UPDATE on receipt
            receipt.environment = "mutated-env"
            with pytest.raises(Exception, match="immutable"):
                db.commit()
            db.rollback()

            # Attempt direct DELETE on receipt
            with pytest.raises(Exception, match="immutable"):
                db.execute(text(f"DELETE FROM admin_bootstrap_receipts WHERE id = '{receipt.id}'"))
                db.commit()
            db.rollback()
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Atomic Rollback on Injected Fault
# ---------------------------------------------------------------------------
def test_bootstrap_atomic_rollback_on_fault_injection():
    """Verify atomicity: injected failure after flush but before commit rolls back all changes."""
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            u1 = create_user(db, "kc-user-1")
            u2 = create_user(db, "kc-user-2")
            u1_id = u1.id
            u2_id = u2.id
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)

            injection_reached = False

            def faulty_commit():
                nonlocal injection_reached
                # Prove at least one bootstrap write (the receipt)
                # has flushed to the active transaction
                flushed_receipts = db.query(AdminBootstrapReceipt).all()
                assert len(flushed_receipts) == 1
                assert flushed_receipts[0].target_sub1 == "kc-user-1"
                assert flushed_receipts[0].target_sub2 == "kc-user-2"
                assert flushed_receipts[0].single_bootstrap_lock == "BOOTSTRAP_LOCK"
                assert flushed_receipts[0].id is not None

                injection_reached = True
                raise RuntimeError("Injected database failure after flush but before commit")

            # Inject the fault into the active session
            db.commit = faulty_commit

            with pytest.raises(
                BootstrapError, match="Atomic bootstrap transaction failed"
            ) as exc_info:
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals={
                        "project_owner": po_sig,
                        "security_reviewer": sr_sig,
                    },
                    now=now,
                    _registry_backend=backend,
                )

            assert injection_reached is True
            assert "Injected database failure after flush but before commit" in str(exc_info.value)

        # Verify via fresh session that rollback was clean and complete
        with SessionLocal() as fresh_db:
            persisted_receipts = fresh_db.query(AdminBootstrapReceipt).all()
            assert len(persisted_receipts) == 0

            persisted_admin_roles = (
                fresh_db.query(UserRole)
                .filter(UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"]))
                .all()
            )
            assert len(persisted_admin_roles) == 0

            total_roles = fresh_db.query(UserRole).all()
            assert len(total_roles) == 0

            user1 = fresh_db.query(User).filter_by(sub="kc-user-1").first()
            user2 = fresh_db.query(User).filter_by(sub="kc-user-2").first()
            assert user1 is not None and user1.id == u1_id
            assert user2 is not None and user2.id == u2_id
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Caller-Selected Keys / Legacy Parameters Rejection (CHPMIS-016)
# ---------------------------------------------------------------------------
def test_bootstrap_rejects_caller_selected_keys_or_legacy_parameters():
    """Verify that caller-selected approver keys and legacy invocation parameters are rejected."""
    SessionLocal, engine = get_test_db()
    try:
        with SessionLocal() as db:
            create_user(db, "kc-user-1")
            create_user(db, "kc-user-2")
            inst = get_or_create_instance_state(db)

            po_priv, _, _, po_bytes = generate_ed25519_keypair()
            sr_priv, _, _, sr_bytes = generate_ed25519_keypair()
            backend = make_valid_synthetic_registry(po_bytes, sr_bytes)

            now = datetime.now(timezone.utc)
            payload_data = make_valid_payload_data(inst.instance_id, now=now)
            canonical_bytes = create_canonical_payload(
                payload_data["environment"],
                payload_data["target_subs"],
                instance_id=payload_data["instance_id"],
                request_id=payload_data["request_id"],
                operator_id=payload_data["operator_id"],
                issued_at=payload_data["issued_at"],
                expires_at=payload_data["expires_at"],
            )

            po_sig = sign_payload(po_priv, canonical_bytes)
            sr_sig = sign_payload(sr_priv, canonical_bytes)
            approvals = {"project_owner": po_sig, "security_reviewer": sr_sig}

            # 1. Reject explicit caller-selected approver_public_keys
            with pytest.raises(
                BootstrapError,
                match="Caller-selected parameters or trust material rejected",
            ):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals=approvals,
                    now=now,
                    _registry_backend=backend,
                    approver_public_keys={
                        "project_owner": po_bytes,
                        "security_reviewer": sr_bytes,
                    },
                )

            # 2. Reject legacy parameters (environment + target_subs without payload_data)
            with pytest.raises(
                BootstrapError,
                match="Caller-selected parameters or trust material rejected",
            ):
                bootstrap_initial_admins(
                    db,
                    environment="development",
                    target_subs=["kc-user-1", "kc-user-2"],
                    approvals=approvals,
                    now=now,
                    _registry_backend=backend,
                    approver_public_keys={
                        "project_owner": po_bytes,
                        "security_reviewer": sr_bytes,
                    },
                )

            # 3. Reject unexpected arbitrary caller arguments
            with pytest.raises(
                BootstrapError,
                match="Caller-selected parameters or trust material rejected",
            ):
                bootstrap_initial_admins(
                    db,
                    payload_data=payload_data,
                    approvals=approvals,
                    now=now,
                    _registry_backend=backend,
                    untrusted_key_source="arbitrary",
                )
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# Tests: Migration 0006 Preservation and Immutability
# ---------------------------------------------------------------------------
def test_migration_0006_preserves_0005_and_receipt_immutability():
    """Verify migration 0006 chain and downgrade refusal."""
    import importlib.util
    from pathlib import Path

    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0006_bootstrap_trust_boundary.py"
    )
    assert migration_path.is_file(), f"Migration file not found at {migration_path}"

    spec = importlib.util.spec_from_file_location(
        "migration_0006_bootstrap_trust_boundary", migration_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "0006_bootstrap_trust_boundary"
    assert mod.down_revision == "0005_initial_admin_bootstrap"

    with pytest.raises(RuntimeError, match="Downgrade of 0006_bootstrap_trust_boundary is refused"):
        mod.downgrade()


# ---------------------------------------------------------------------------
# Tests: CHPMIS-016-F2 Owner SID, Exact DACL/ACE, and Win32 ctypes
# ---------------------------------------------------------------------------
def test_registry_rejects_missing_or_invalid_owner_sid_on_task_created_keys():
    """Verify task-created keys require BUILTIN\\Administrators owner SID.

    The shared root key gets no owner allowlist.
    """
    from app.auth import bootstrap_admins as ba

    _, _, _, po_bytes = generate_ed25519_keypair()
    _, _, _, sr_bytes = generate_ed25519_keypair()

    # 1. Missing owner on task namespace key
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_NAMESPACE_PATH].pop("owner_sid", None)
    backend.keys[REGISTRY_NAMESPACE_PATH].pop("sddl", None)
    with pytest.raises(ba.BootstrapError, match="owner SID"):
        backend.read_trusted_keys()

    # 2. Invalid owner SID on task namespace key (e.g. Users SID instead of BA)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_NAMESPACE_PATH]["owner_sid"] = "S-1-5-32-545"
    with pytest.raises(ba.BootstrapError, match=r"BUILTIN\\Administrators"):
        backend.read_trusted_keys()

    # 3. Missing owner on task trust leaf key
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH].pop("owner_sid", None)
    backend.keys[REGISTRY_TRUST_KEY_PATH].pop("sddl", None)
    with pytest.raises(ba.BootstrapError, match="owner SID"):
        backend.read_trusted_keys()

    # 4. Invalid owner SID on task trust leaf key
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["owner_sid"] = "S-1-5-21-123-456-789-500"
    with pytest.raises(ba.BootstrapError, match=r"BUILTIN\\Administrators"):
        backend.read_trusted_keys()

    # 5. Shared root HKLM\\SOFTWARE gets NO owner allowlist or task-key SDDL
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_ROOT_PATH]["owner_sid"] = (
        "S-1-5-80-956008885-3418522649-1831038044-1853292636-4146059445"
    )
    res = backend.read_trusted_keys()
    assert res["project_owner"] == po_bytes
    assert res["security_reviewer"] == sr_bytes


def test_registry_exact_dacl_and_ace_validation_on_task_created_keys():
    """Verify task-created keys strictly enforce approved exact DACL and ACEs."""
    from app.auth import bootstrap_admins as ba

    _, _, _, po_bytes = generate_ed25519_keypair()
    _, _, _, sr_bytes = generate_ed25519_keypair()

    # 1. Missing DACL/ACE evidence on task key
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH].pop("dacl_aces", None)
    backend.keys[REGISTRY_TRUST_KEY_PATH].pop("sddl", None)
    with pytest.raises(ba.BootstrapError, match="DACL/ACE evidence"):
        backend.read_trusted_keys()

    # 2. Extra unexpected grant ACE (4th ACE for Everyone)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    extra_ace = {
        "type": "ACCESS_ALLOWED",
        "flags": 0,
        "mask": ba.KEY_READ,
        "trustee_sid": "S-1-1-0",
    }
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"].append(extra_ace)
    with pytest.raises(ba.BootstrapError, match="exactly 3 ACEs"):
        backend.read_trusted_keys()

    # 3. Unexpected Deny ACE
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    deny_ace = {
        "type": "ACCESS_DENIED",
        "flags": 0,
        "mask": ba.KEY_WRITE,
        "trustee_sid": "S-1-5-32-545",
    }
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2] = deny_ace
    with pytest.raises(ba.BootstrapError, match="Unexpected ACE type"):
        backend.read_trusted_keys()

    # 4. Inherited ACE (non-zero flags)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    inherited_ace = {
        "type": "ACCESS_ALLOWED",
        "flags": ba.INHERITED_ACE,
        "mask": ba.KEY_READ,
        "trustee_sid": "S-1-5-32-545",
    }
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2] = inherited_ace
    with pytest.raises(ba.BootstrapError, match="Unexpected ACE flags"):
        backend.read_trusted_keys()

    # 5. Missing required grant (only 2 ACEs)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"] = backend.keys[REGISTRY_TRUST_KEY_PATH][
        "dacl_aces"
    ][:2]
    with pytest.raises(ba.BootstrapError, match="exactly 3 ACEs"):
        backend.read_trusted_keys()

    # 6. Wrong access mask (e.g. KEY_ALL_ACCESS for BU instead of KEY_READ)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2]["mask"] = ba.KEY_ALL_ACCESS
    with pytest.raises(ba.BootstrapError, match="Incorrect access mask"):
        backend.read_trusted_keys()

    # 7. Wrong trustee SID (e.g. S-1-5-32-546 Guests instead of BU)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2]["trustee_sid"] = "S-1-5-32-546"
    with pytest.raises(ba.BootstrapError, match="Unexpected trustee SID"):
        backend.read_trusted_keys()

    # 8. Duplicate trustee SID (e.g. two BA ACEs)
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2]["trustee_sid"] = (
        ba.SID_BUILTIN_ADMINISTRATORS
    )
    backend.keys[REGISTRY_TRUST_KEY_PATH]["dacl_aces"][2]["mask"] = ba.KEY_ALL_ACCESS
    with pytest.raises(ba.BootstrapError, match="Duplicate trustee"):
        backend.read_trusted_keys()

    # 9. Valid SDDL representation accepted
    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH].pop("dacl_aces", None)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["sddl"] = ba.APPROVED_TASK_KEY_SDDL
    res = backend.read_trusted_keys()
    assert res["project_owner"] == po_bytes


def test_win32_registry_generic_masks_mapped_before_access_check():
    """Verify registry generic mapping maps GENERIC masks to specific rights."""
    import ctypes
    from ctypes import wintypes

    from app.auth import bootstrap_admins as ba

    if ba.sys.platform != "win32":
        pytest.skip("Win32 ctypes/registry tests run in windows-backend CI job")

    gm = ba.GENERIC_MAPPING()
    gm.GenericRead = ba.KEY_READ
    gm.GenericWrite = ba.KEY_WRITE
    gm.GenericExecute = ba.KEY_EXECUTE
    gm.GenericAll = ba.KEY_ALL_ACCESS

    # Map GENERIC_WRITE (0x40000000)
    desired = wintypes.DWORD(0x40000000)
    ctypes.windll.advapi32.MapGenericMask(ctypes.byref(desired), ctypes.byref(gm))
    assert desired.value == ba.KEY_WRITE

    # Map GENERIC_ALL (0x10000000)
    desired = wintypes.DWORD(0x10000000)
    ctypes.windll.advapi32.MapGenericMask(ctypes.byref(desired), ctypes.byref(gm))
    assert desired.value == ba.KEY_ALL_ACCESS


def test_win32_ctypes_prototype_declarations():
    """Verify Win32 ctypes function bindings have explicit argtypes and restype."""
    import ctypes
    from ctypes import wintypes

    from app.auth import bootstrap_admins as ba

    if ba.sys.platform != "win32":
        pytest.skip("Win32 ctypes/registry tests run in windows-backend CI job")

    # Verify HKEY_LOCAL_MACHINE sign-extension
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        assert ba.HKEY_LOCAL_MACHINE == 0xFFFFFFFF80000002
    else:
        assert ba.HKEY_LOCAL_MACHINE == 0x80000002

    # Verify configure_win32_prototypes sets explicit argtypes and restype
    assert hasattr(ba, "configure_win32_prototypes")
    ba.configure_win32_prototypes()

    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    assert kernel32.GetCurrentProcess.restype == wintypes.HANDLE
    assert kernel32.GetLastError.restype == wintypes.DWORD
    assert kernel32.CloseHandle.argtypes == [wintypes.HANDLE]
    assert kernel32.CloseHandle.restype == wintypes.BOOL
    assert kernel32.LocalFree.argtypes == [ctypes.c_void_p]
    assert kernel32.LocalFree.restype == ctypes.c_void_p

    assert advapi32.OpenProcessToken.argtypes == [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    assert advapi32.OpenProcessToken.restype == wintypes.BOOL
    assert advapi32.DuplicateToken.argtypes == [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    assert advapi32.DuplicateToken.restype == wintypes.BOOL
    assert advapi32.RegOpenKeyExW.restype == wintypes.LONG
    assert advapi32.RegCloseKey.argtypes == [wintypes.HKEY]
    assert advapi32.RegCloseKey.restype == wintypes.LONG
    assert advapi32.GetSecurityInfo.restype == wintypes.DWORD
    assert advapi32.GetSecurityDescriptorControl.restype == wintypes.BOOL
    assert advapi32.GetSecurityDescriptorOwner.restype == wintypes.BOOL
    assert advapi32.GetSecurityDescriptorDacl.restype == wintypes.BOOL
    assert advapi32.GetAclInformation.restype == wintypes.BOOL
    assert advapi32.GetAce.restype == wintypes.BOOL
    assert advapi32.ConvertSidToStringSidW.restype == wintypes.BOOL
    assert advapi32.MapGenericMask.restype is None
    assert advapi32.AccessCheck.restype == wintypes.BOOL
    assert advapi32.RegQueryInfoKeyW.restype == wintypes.LONG
    assert advapi32.RegEnumValueW.restype == wintypes.LONG


def test_registry_error_handling_on_api_failure():
    """Verify registry backend raises BootstrapError on simulated API failure."""
    from app.auth import bootstrap_admins as ba

    _, _, _, po_bytes = generate_ed25519_keypair()
    _, _, _, sr_bytes = generate_ed25519_keypair()

    backend = make_valid_synthetic_registry(po_bytes, sr_bytes)
    backend.keys[REGISTRY_TRUST_KEY_PATH]["access_check_error"] = "PrivilegeNotHeld"
    with pytest.raises(ba.BootstrapError, match="AccessCheck failed"):
        backend.read_trusted_keys()


def test_windows_registry_backend_null_pointers_and_cleanup_on_error():
    """Verify WindowsRegistryBackend handles null pointers and cleans up resources on error."""
    from unittest.mock import MagicMock

    from app.auth import bootstrap_admins as ba

    if ba.sys.platform != "win32":
        pytest.skip("Win32 ctypes/registry tests run in windows-backend CI job")

    fake_kernel32 = MagicMock()
    fake_advapi32 = MagicMock()

    # Successful process token and duplication
    fake_kernel32.GetCurrentProcess.return_value = 1
    fake_advapi32.OpenProcessToken.return_value = 1
    fake_advapi32.DuplicateToken.return_value = 1

    # Successful RegOpenKeyExW and GetSecurityInfo
    fake_advapi32.RegOpenKeyExW.return_value = 0
    fake_advapi32.GetSecurityInfo.return_value = 0

    # GetSecurityDescriptorControl: present and protected
    def fake_control(p_sd, p_ctrl, p_rev):
        p_ctrl._obj.value = ba.SE_DACL_PRESENT | ba.SE_DACL_PROTECTED
        return 1

    fake_advapi32.GetSecurityDescriptorControl.side_effect = fake_control

    # 1. Null owner pointer simulation on task key (software\\chpmis011localsynthetic)
    def fake_get_owner_null(p_sd, p_owner, p_defaulted):
        p_owner._obj.value = None
        return 1

    fake_advapi32.GetSecurityDescriptorOwner.side_effect = fake_get_owner_null

    backend = ba.WindowsRegistryBackend(advapi32=fake_advapi32, kernel32=fake_kernel32)
    with pytest.raises(ba.BootstrapError, match="extract owner SID"):
        backend.read_trusted_keys()

    # Verify resource cleanup occurred
    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called
    assert fake_kernel32.CloseHandle.called

    # 2. Null DACL pointer simulation
    fake_kernel32.reset_mock()
    fake_advapi32.reset_mock()
    fake_advapi32.RegOpenKeyExW.return_value = 0
    fake_advapi32.GetSecurityInfo.return_value = 0
    fake_advapi32.GetSecurityDescriptorControl.side_effect = fake_control

    def fake_get_owner_valid(p_sd, p_owner, p_defaulted):
        p_owner._obj.value = 1234
        return 1

    def fake_convert_sid_owner(p_sid, p_str):
        p_str._obj.value = ba.SID_BUILTIN_ADMINISTRATORS
        return 1

    def fake_get_dacl_null(p_sd, p_present, p_dacl, p_defaulted):
        p_present._obj.value = 1
        p_dacl._obj.value = None
        return 1

    fake_advapi32.GetSecurityDescriptorOwner.side_effect = fake_get_owner_valid
    fake_advapi32.ConvertSidToStringSidW.side_effect = fake_convert_sid_owner
    fake_advapi32.GetSecurityDescriptorDacl.side_effect = fake_get_dacl_null

    with pytest.raises(ba.BootstrapError, match="Failed to get DACL"):
        backend.read_trusted_keys()

    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called
    assert fake_kernel32.CloseHandle.called


def test_windows_registry_backend_non_windows_platform_guard(monkeypatch):
    """Verify WindowsRegistryBackend rejects non-Windows execution fail-closed."""
    from app.auth import bootstrap_admins as ba

    backend = ba.WindowsRegistryBackend()
    monkeypatch.setattr(backend, "is_windows", lambda: False)
    with pytest.raises(
        ba.BootstrapError,
        match=r"Registry trust boundary is supported only on Windows \(win32\)",
    ):
        backend.read_trusted_keys()


def _make_mock_win32_backend(po_bytes: bytes, sr_bytes: bytes):
    import ctypes
    from ctypes import wintypes
    from unittest.mock import MagicMock

    from app.auth import bootstrap_admins as ba

    fake_kernel32 = MagicMock()
    fake_advapi32 = MagicMock()

    fake_kernel32.GetCurrentProcess.return_value = 1
    fake_advapi32.OpenProcessToken.return_value = 1
    fake_advapi32.DuplicateToken.return_value = 1
    fake_kernel32.CloseHandle.return_value = 1
    fake_kernel32.LocalFree.return_value = None

    fake_advapi32.RegOpenKeyExW.return_value = 0
    fake_advapi32.RegCloseKey.return_value = 0
    fake_advapi32.GetSecurityInfo.return_value = 0

    def fake_control(p_sd, p_ctrl, p_rev):
        p_ctrl._obj.value = ba.SE_DACL_PRESENT | ba.SE_DACL_PROTECTED
        return 1

    fake_advapi32.GetSecurityDescriptorControl.side_effect = fake_control

    def fake_owner(p_sd, p_owner, p_defaulted):
        p_owner._obj.value = 1234
        if p_defaulted:
            p_defaulted._obj.value = 0
        return 1

    fake_advapi32.GetSecurityDescriptorOwner.side_effect = fake_owner

    ace_specs = [
        (ba.SID_LOCAL_SYSTEM, ba.KEY_ALL_ACCESS),
        (ba.SID_BUILTIN_ADMINISTRATORS, ba.KEY_ALL_ACCESS),
        (ba.SID_BUILTIN_USERS, ba.KEY_READ),
    ]
    aces = []
    sid_ptrs = {}
    for sid_str, mask in ace_specs:
        ace = ba.ACCESS_ALLOWED_ACE()
        ace.Header.AceType = ba.ACCESS_ALLOWED_ACE_TYPE
        ace.Header.AceFlags = 0
        ace.Header.AceSize = ctypes.sizeof(ba.ACCESS_ALLOWED_ACE)
        ace.Mask = mask
        aces.append(ace)
        sid_offset = ctypes.sizeof(ba.ACE_HEADER) + ctypes.sizeof(wintypes.DWORD)
        sid_ptrs[ctypes.addressof(ace) + sid_offset] = sid_str

    def fake_dacl(p_sd, p_present, p_dacl, p_defaulted):
        p_present._obj.value = 1
        p_dacl._obj.value = 5678
        if p_defaulted:
            p_defaulted._obj.value = 0
        return 1

    fake_advapi32.GetSecurityDescriptorDacl.side_effect = fake_dacl

    def fake_acl_info(p_dacl, p_info, info_len, info_class):
        p_info._obj.AceCount = 3
        return 1

    fake_advapi32.GetAclInformation.side_effect = fake_acl_info

    def fake_get_ace(p_dacl, idx, p_ace):
        p_ace._obj.value = ctypes.addressof(aces[idx])
        return 1

    fake_advapi32.GetAce.side_effect = fake_get_ace

    def fake_convert_sid(p_sid, p_str):
        val = p_sid.value if hasattr(p_sid, "value") else p_sid
        if val in sid_ptrs:
            p_str._obj.value = sid_ptrs[val]
        else:
            p_str._obj.value = ba.SID_BUILTIN_ADMINISTRATORS
        return 1

    fake_advapi32.ConvertSidToStringSidW.side_effect = fake_convert_sid

    def fake_access_check(p_sd, token, access, p_gm, p_ps, p_ps_len, p_granted, p_status):
        p_status._obj.value = 0
        return 1

    fake_advapi32.AccessCheck.side_effect = fake_access_check

    def fake_query_info_key(leaf_key, *args):
        c_values = args[6]
        c_values._obj.value = 2
        return 0

    fake_advapi32.RegQueryInfoKeyW.side_effect = fake_query_info_key

    def fake_enum_value(
        leaf_key, idx, val_name_buf, cch_val_name, reserved, val_type, data_buf, cb_data
    ):
        if idx == 0:
            val_name_buf.value = ba.VAL_PROJECT_OWNER
            val_type._obj.value = ba.REG_BINARY
            cb_data._obj.value = len(po_bytes)
            ctypes.memmove(data_buf, po_bytes, len(po_bytes))
            return 0
        elif idx == 1:
            val_name_buf.value = ba.VAL_SECURITY_REVIEWER
            val_type._obj.value = ba.REG_BINARY
            cb_data._obj.value = len(sr_bytes)
            ctypes.memmove(data_buf, sr_bytes, len(sr_bytes))
            return 0
        return 259

    fake_advapi32.RegEnumValueW.side_effect = fake_enum_value

    backend = ba.WindowsRegistryBackend(advapi32=fake_advapi32, kernel32=fake_kernel32)
    return backend, fake_advapi32, fake_kernel32, aces


def test_windows_registry_backend_read_trusted_keys_signed_bytes_preservation():
    """Verify WindowsRegistryBackend preserves raw bytes containing 0x80 and 0xff."""
    from app.auth import bootstrap_admins as ba

    if ba.sys.platform != "win32":
        pytest.skip("Win32 ctypes/registry tests run in windows-backend CI job")

    po_bytes = bytes([0x80, 0xFF] + [i % 256 for i in range(2, 32)])
    sr_bytes = bytes([0xFF, 0x80] + [(i * 3) % 256 for i in range(2, 32)])
    assert len(po_bytes) == 32
    assert len(sr_bytes) == 32
    assert po_bytes != sr_bytes

    backend, _, _, _ = _make_mock_win32_backend(po_bytes, sr_bytes)
    res = backend.read_trusted_keys()
    assert res["project_owner"] == po_bytes
    assert res["security_reviewer"] == sr_bytes


def test_windows_registry_backend_negative_and_cleanup_cases():
    """Verify WindowsRegistryBackend validates value types/lengths, Win32 errors, and cleans up."""
    from app.auth import bootstrap_admins as ba

    if ba.sys.platform != "win32":
        pytest.skip("Win32 ctypes/registry tests run in windows-backend CI job")

    po_bytes = bytes([0x80] + [1] * 31)
    sr_bytes = bytes([0xFF] + [2] * 31)

    # 1. Invalid value type (not REG_BINARY)
    backend, fake_advapi32, fake_kernel32, _ = _make_mock_win32_backend(po_bytes, sr_bytes)
    orig_enum = fake_advapi32.RegEnumValueW.side_effect

    def fake_enum_bad_type(
        leaf_key, idx, val_name_buf, cch_val_name, reserved, val_type, data_buf, cb_data
    ):
        orig_enum(leaf_key, idx, val_name_buf, cch_val_name, reserved, val_type, data_buf, cb_data)
        val_type._obj.value = 1  # REG_SZ
        return 0

    fake_advapi32.RegEnumValueW.side_effect = fake_enum_bad_type
    with pytest.raises(ba.BootstrapError, match="must be of type REG_BINARY"):
        backend.read_trusted_keys()
    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called

    # 2. Invalid value length (!= 32 bytes)
    backend, fake_advapi32, fake_kernel32, _ = _make_mock_win32_backend(po_bytes, sr_bytes)

    def fake_enum_bad_len(
        leaf_key, idx, val_name_buf, cch_val_name, reserved, val_type, data_buf, cb_data
    ):
        orig_enum(leaf_key, idx, val_name_buf, cch_val_name, reserved, val_type, data_buf, cb_data)
        cb_data._obj.value = 16
        return 0

    fake_advapi32.RegEnumValueW.side_effect = fake_enum_bad_len
    with pytest.raises(ba.BootstrapError, match="must be exactly 32 bytes"):
        backend.read_trusted_keys()
    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called

    # 3. RegEnumValueW failure
    backend, fake_advapi32, fake_kernel32, _ = _make_mock_win32_backend(po_bytes, sr_bytes)
    fake_advapi32.RegEnumValueW.side_effect = None
    fake_advapi32.RegEnumValueW.return_value = 5  # ERROR_ACCESS_DENIED
    with pytest.raises(ba.BootstrapError, match="RegEnumValueW failed for index 0"):
        backend.read_trusted_keys()
    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called

    # 4. Same key for both roles rejected
    same_bytes = bytes([1] * 32)
    backend, fake_advapi32, fake_kernel32, _ = _make_mock_win32_backend(same_bytes, same_bytes)
    with pytest.raises(ba.BootstrapError, match="must be distinct"):
        backend.read_trusted_keys()
    assert fake_kernel32.LocalFree.called
    assert fake_advapi32.RegCloseKey.called
