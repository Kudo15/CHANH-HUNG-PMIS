import argparse
import base64
import hashlib
import json
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.orm import Session as DBSession

from app.auth.models import AdminBootstrapReceipt, User, UserRole
from app.config import Settings
from app.database import build_engine


class BootstrapError(Exception):
    """Raised when bootstrap validation or execution fails."""


def create_canonical_payload(environment: str, target_subs: list[str]) -> bytes:
    if len(target_subs) != 2:
        raise BootstrapError("Bootstrap requires exactly two target users")
    if target_subs[0] == target_subs[1]:
        raise BootstrapError("Bootstrap target users must be distinct")

    data = {
        "action": "bootstrap_initial_admins",
        "environment": environment,
        "target_subs": [target_subs[0], target_subs[1]],
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_ed25519_public_key(key_input: str | bytes) -> tuple[Ed25519PublicKey, str, bytes]:
    raw_bytes: bytes
    if isinstance(key_input, str):
        cleaned = key_input.strip()
        if "BEGIN PUBLIC KEY" in cleaned:
            pub_key = serialization.load_pem_public_key(cleaned.encode("utf-8"))
            if not isinstance(pub_key, Ed25519PublicKey):
                raise BootstrapError("Only Ed25519 public keys are supported")
            raw_bytes = pub_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            fingerprint = hashlib.sha256(raw_bytes).hexdigest()
            return pub_key, fingerprint, raw_bytes
        else:
            try:
                raw_bytes = base64.b64decode(cleaned)
            except Exception as exc:
                raise BootstrapError("Invalid base64 encoding for public key") from exc
    else:
        raw_bytes = key_input

    if len(raw_bytes) != 32:
        raise BootstrapError("Ed25519 raw public key must be exactly 32 bytes")

    try:
        pub_key = Ed25519PublicKey.from_public_bytes(raw_bytes)
    except Exception as exc:
        raise BootstrapError(f"Failed to load Ed25519 public key: {exc}") from exc

    fingerprint = hashlib.sha256(raw_bytes).hexdigest()
    return pub_key, fingerprint, raw_bytes


def _decode_signature(sig_input: str | bytes) -> bytes:
    if isinstance(sig_input, str):
        cleaned = sig_input.strip()
        try:
            return base64.b64decode(cleaned)
        except Exception as exc:
            raise BootstrapError("Invalid base64 encoding for signature") from exc
    return sig_input


def bootstrap_initial_admins(
    db: DBSession,
    *,
    environment: str,
    target_subs: list[str],
    approvals: dict[str, str | bytes],
    approver_public_keys: dict[str, str | bytes],
) -> AdminBootstrapReceipt:
    # 1. Validate target count and distinctness
    if len(target_subs) != 2:
        raise BootstrapError("Bootstrap requires exactly two target users")
    if target_subs[0] == target_subs[1]:
        raise BootstrapError("Bootstrap target users must be distinct")

    # 2. Check zero-admin precondition
    existing_admins = db.query(UserRole).filter(UserRole.role == "System Admin").count()
    if existing_admins > 0:
        raise BootstrapError(
            "System Admin already exists; bootstrap is only permitted when zero System Admins exist"
        )

    # 3. Check single bootstrap receipt precondition
    existing_receipts = db.query(AdminBootstrapReceipt).count()
    if existing_receipts > 0:
        raise BootstrapError("Bootstrap has already been performed; replay rejected")

    # 4. Verify target users exist and are active
    u1 = db.query(User).filter_by(sub=target_subs[0]).first()
    if not u1:
        raise BootstrapError(
            f"User with sub '{target_subs[0]}' not found; users must first authenticate via OIDC"
        )
    if not u1.is_active:
        raise BootstrapError(f"Target user '{target_subs[0]}' is inactive or deprovisioned")

    u2 = db.query(User).filter_by(sub=target_subs[1]).first()
    if not u2:
        raise BootstrapError(
            f"User with sub '{target_subs[1]}' not found; users must first authenticate via OIDC"
        )
    if not u2.is_active:
        raise BootstrapError(f"Target user '{target_subs[1]}' is inactive or deprovisioned")

    if u1.id == u2.id:
        raise BootstrapError("Target user database IDs must be distinct")

    # 5. Verify approver keys and roles
    required_roles = ["project_owner", "security_reviewer"]
    for role in required_roles:
        if role not in approver_public_keys:
            raise BootstrapError(f"Missing approver public key for role '{role}'")
        if role not in approvals:
            raise BootstrapError(f"Missing approval signature for role '{role}'")

    po_pub, po_fp, po_bytes = _load_ed25519_public_key(approver_public_keys["project_owner"])
    sr_pub, sr_fp, sr_bytes = _load_ed25519_public_key(approver_public_keys["security_reviewer"])

    if po_bytes == sr_bytes:
        raise BootstrapError(
            "Project Owner and Security Reviewer approver keys must be distinct; "
            "same-person approval rejected"
        )

    # 6. Verify canonical payload signatures
    payload = create_canonical_payload(environment, target_subs)
    payload_digest = hashlib.sha256(payload).hexdigest()

    po_sig = _decode_signature(approvals["project_owner"])
    sr_sig = _decode_signature(approvals["security_reviewer"])

    try:
        po_pub.verify(po_sig, payload)
    except InvalidSignature:
        raise BootstrapError(
            "Invalid approval signature for Project Owner; payload or environment mismatch"
        ) from None
    except Exception as exc:
        raise BootstrapError(f"Project Owner signature verification failed: {exc}") from exc

    try:
        sr_pub.verify(sr_sig, payload)
    except InvalidSignature:
        raise BootstrapError(
            "Invalid approval signature for Security Reviewer; payload or environment mismatch"
        ) from None
    except Exception as exc:
        raise BootstrapError(f"Security Reviewer signature verification failed: {exc}") from exc

    # 7. Atomic transaction: create receipt and user roles
    try:
        receipt = AdminBootstrapReceipt(
            environment=environment,
            target_user1_id=u1.id,
            target_user2_id=u2.id,
            target_sub1=target_subs[0],
            target_sub2=target_subs[1],
            approver1_role="project_owner",
            approver1_key_fingerprint=po_fp,
            approver2_role="security_reviewer",
            approver2_key_fingerprint=sr_fp,
            payload_digest=payload_digest,
            consumed=True,
            single_bootstrap_lock="BOOTSTRAP_LOCK",
        )
        db.add(receipt)
        db.flush()

        role1 = UserRole(
            user_id=u1.id,
            role="System Admin",
            granted_by=None,
            second_admin_id=None,
            bootstrap_receipt_id=receipt.id,
        )
        role2 = UserRole(
            user_id=u2.id,
            role="System Admin",
            granted_by=None,
            second_admin_id=None,
            bootstrap_receipt_id=receipt.id,
        )
        db.add(role1)
        db.add(role2)
        db.commit()
        db.refresh(receipt)
        return receipt
    except Exception as exc:
        db.rollback()
        raise BootstrapError(f"Atomic bootstrap transaction failed: {exc}") from exc


def _read_file_or_value(val: str) -> str:
    try:
        with open(val, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, FileNotFoundError):
        return val.strip()


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-time offline initial System Admin bootstrap command."
    )
    parser.add_argument(
        "--environment",
        required=True,
        help="Target environment identifier (e.g. 'development', 'local')",
    )
    parser.add_argument(
        "--target-subs",
        nargs=2,
        required=True,
        metavar=("SUB1", "SUB2"),
        help="Exactly two distinct OIDC subject identifiers for initial admins",
    )
    parser.add_argument(
        "--project-owner-key",
        required=True,
        help="Project Owner Ed25519 public key (PEM, base64 or file path)",
    )
    parser.add_argument(
        "--security-reviewer-key",
        required=True,
        help="Security Reviewer Ed25519 public key (PEM, base64 or file path)",
    )
    parser.add_argument(
        "--project-owner-sig",
        required=True,
        help="Project Owner approval signature (base64 or file path)",
    )
    parser.add_argument(
        "--security-reviewer-sig",
        required=True,
        help="Security Reviewer approval signature (base64 or file path)",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    settings = Settings()
    engine = build_engine(settings)
    if engine is None:
        sys.stderr.write("Database engine not configured; set DATABASE_URL in environment\n")
        return 1

    po_key = _read_file_or_value(parsed.project_owner_key)
    sr_key = _read_file_or_value(parsed.security_reviewer_key)
    po_sig = _read_file_or_value(parsed.project_owner_sig)
    sr_sig = _read_file_or_value(parsed.security_reviewer_sig)

    with DBSession(engine) as db:
        try:
            receipt = bootstrap_initial_admins(
                db,
                environment=parsed.environment,
                target_subs=parsed.target_subs,
                approvals={
                    "project_owner": po_sig,
                    "security_reviewer": sr_sig,
                },
                approver_public_keys={
                    "project_owner": po_key,
                    "security_reviewer": sr_key,
                },
            )
            sys.stdout.write(
                f"SUCCESS: System Admin bootstrap completed.\n"
                f"Receipt ID: {receipt.id}\n"
                f"Environment: {receipt.environment}\n"
                f"Target Sub 1: {receipt.target_sub1}\n"
                f"Target Sub 2: {receipt.target_sub2}\n"
                f"Payload Digest: {receipt.payload_digest}\n"
            )
            return 0
        except BootstrapError as exc:
            sys.stderr.write(f"BOOTSTRAP REJECTED: {exc}\n")
            return 1
        except Exception as exc:
            sys.stderr.write(f"UNEXPECTED ERROR: {exc}\n")
            return 1


if __name__ == "__main__":
    sys.exit(main())
