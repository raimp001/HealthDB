"""Administrative CLI.

Privileged roles are deliberately not reachable from any HTTP endpoint —
that is what the registration vulnerability allowed. Creating an admin or
institution account requires shell access to the deployment and is recorded
in the audit log.

Usage:
    python -m api.manage grant-role <email> <admin|institution> [--institution-id ID]
    python -m api.manage list-privileged
    python -m api.manage revoke-role <email>
"""
import argparse
import logging
import sys
from datetime import datetime

from .database import SessionLocal
from .models import User, Institution

audit = logging.getLogger("healthdb.audit")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

PRIVILEGED = {"admin", "institution"}


def grant_role(session, email: str, role: str, institution_id: str | None) -> int:
    if role not in PRIVILEGED:
        print(f"Refusing: {role!r} is not a privileged role ({', '.join(sorted(PRIVILEGED))})")
        return 1

    user = session.query(User).filter(User.email == email).first()
    if not user:
        print(f"No user with email {email!r}")
        return 1

    if role == "institution":
        if not institution_id:
            print("An institution role requires --institution-id")
            return 1
        if not session.query(Institution).filter(Institution.id == institution_id).first():
            print(f"No institution with id {institution_id!r}")
            return 1
        user.institution_id = institution_id

    previous = user.user_type
    user.user_type = role
    session.commit()
    audit.info("ROLE_GRANTED user=%s from=%s to=%s", user.id, previous, role)
    print(f"{email}: {previous} -> {role}")
    print("Existing tokens for this user keep their old role until reissued;")
    print("role is resolved from the database on every privileged request.")
    return 0


def revoke_role(session, email: str) -> int:
    user = session.query(User).filter(User.email == email).first()
    if not user:
        print(f"No user with email {email!r}")
        return 1
    previous = user.user_type
    user.user_type = "researcher"
    user.institution_id = None
    session.commit()
    audit.info("ROLE_REVOKED user=%s from=%s", user.id, previous)
    print(f"{email}: {previous} -> researcher")
    return 0


def approve_researcher(session, email: str) -> int:
    """Explicitly approve a researcher for research features.

    Deliberately separate from email verification: a verified address proves
    control of a mailbox, not institutional affiliation or standing. Vet the
    person out of band before running this.
    """
    user = session.query(User).filter(User.email == email).first()
    if not user:
        print(f"No user with email {email!r}")
        return 1
    if user.user_type != "researcher":
        print(f"Refusing: {email} is a {user.user_type}, not a researcher")
        return 1
    if not user.is_verified:
        print(f"Refusing: {email} has not verified their email address yet")
        return 1
    if user.researcher_approved_at:
        print(f"{email} was already approved at {user.researcher_approved_at}")
        return 0

    user.researcher_approved_at = datetime.utcnow()
    session.commit()
    audit.info("RESEARCHER_APPROVED user=%s", user.id)
    print(f"{email}: approved for research features")
    return 0


def revoke_researcher(session, email: str) -> int:
    """Withdraw research access. Takes effect on the researcher's next request."""
    user = session.query(User).filter(User.email == email).first()
    if not user:
        print(f"No user with email {email!r}")
        return 1
    user.researcher_approved_at = None
    session.commit()
    audit.info("RESEARCHER_APPROVAL_REVOKED user=%s", user.id)
    print(f"{email}: research approval revoked")
    return 0


def list_privileged(session) -> int:
    rows = session.query(User).filter(User.user_type.in_(PRIVILEGED)).all()
    if not rows:
        print("No privileged accounts.")
        return 0
    for u in rows:
        print(f"  {u.email:40} {u.user_type:12} institution={u.institution_id}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="api.manage")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("grant-role", help="Promote a user to a privileged role")
    g.add_argument("email")
    g.add_argument("role", choices=sorted(PRIVILEGED))
    g.add_argument("--institution-id")

    r = sub.add_parser("revoke-role", help="Return a user to the researcher role")
    r.add_argument("email")

    sub.add_parser("list-privileged", help="Show all privileged accounts")

    ar = sub.add_parser("approve-researcher", help="Grant research access")
    ar.add_argument("email")

    rr = sub.add_parser("revoke-researcher", help="Withdraw research access")
    rr.add_argument("email")

    args = parser.parse_args(argv)
    session = SessionLocal()
    try:
        if args.command == "grant-role":
            return grant_role(session, args.email, args.role, args.institution_id)
        if args.command == "revoke-role":
            return revoke_role(session, args.email)
        if args.command == "approve-researcher":
            return approve_researcher(session, args.email)
        if args.command == "revoke-researcher":
            return revoke_researcher(session, args.email)
        return list_privileged(session)
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
