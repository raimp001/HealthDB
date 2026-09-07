"""Administrative CLI.

Privileged roles and researcher approval are deliberately unreachable over
HTTP. Granting them requires shell access to the deployment, and every grant
is written to the audit log.

    python -m api.manage approve-researcher <email>
    python -m api.manage revoke-researcher <email>
    python -m api.manage grant-role <email> <admin|institution> [--institution-id ID]
    python -m api.manage revoke-role <email>
    python -m api.manage list-privileged
    python -m api.manage migrate-dates
    python -m api.manage remove-placeholder-institutions

The two data commands are deliberately not run at boot. Both take locks, and
running them on every serverless cold start caused concurrent invocations to
contend until the function timed out. A destructive migration should also be
an explicit operator decision.
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


def approve_researcher(session, email):
    """Grant research access.

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


def revoke_researcher(session, email):
    """Withdraw research access. Takes effect on the next request."""
    user = session.query(User).filter(User.email == email).first()
    if not user:
        print(f"No user with email {email!r}")
        return 1
    user.researcher_approved_at = None
    session.commit()
    audit.info("RESEARCHER_APPROVAL_REVOKED user=%s", user.id)
    print(f"{email}: research approval revoked")
    return 0


def grant_role(session, email, role, institution_id):
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
    print("Roles resolve from the database on every request, so this takes")
    print("effect immediately without reissuing the user's token.")
    return 0


def revoke_role(session, email):
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


def list_privileged(session):
    rows = session.query(User).filter(User.user_type.in_(PRIVILEGED)).all()
    approved = session.query(User).filter(User.researcher_approved_at.isnot(None)).all()
    if not rows and not approved:
        print("No privileged or approved accounts.")
        return 0
    for u in rows:
        print(f"  {u.email:40} {u.user_type:12} institution={u.institution_id}")
    for u in approved:
        print(f"  {u.email:40} researcher   approved={u.researcher_approved_at}")
    return 0


def migrate_dates(session):
    """Truncate stored clinical dates to the year. Irreversible.

    Backfills original_year, then destroys month and day. See
    docs/MIGRATIONS.md; the discarded precision cannot be recovered without a
    pre-migration backup.
    """
    from .main import migrate_truncate_original_dates
    engine = session.get_bind()
    migrate_truncate_original_dates(engine)
    audit.info("DATE_TRUNCATION_MIGRATION_RUN")
    print("Date truncation complete. Month and day are gone; this is not reversible.")
    return 0


def remove_placeholders(session):
    """Delete institution rows naming real hospitals with no relationship here."""
    from .main import remove_placeholder_institutions
    removed = remove_placeholder_institutions(session)
    audit.info("PLACEHOLDER_INSTITUTIONS_REMOVED count=%s", removed)
    print(f"Removed {removed} placeholder institution row(s).")
    print("Rows referenced by a user or regulatory submission were kept and listed above.")
    return 0


def self_audit(session, *, as_json: bool = False) -> int:
    """Report whether the platform's safety properties still hold.

    Exits non-zero when a blocker is failing, so a scheduled run is a usable
    alarm rather than something a person has to read.
    """
    import json as _json

    from api.self_audit import run_audit

    report = run_audit(session)
    if as_json:
        print(_json.dumps(report.as_dict(), indent=2))
    else:
        for finding in report.findings:
            mark = "ok  " if finding.passed else "FAIL"
            print(f"[{mark}] {finding.severity:<7} {finding.name}: {finding.summary}")
        print()
        print(report.summary())
    return 0 if report.ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="api.manage")
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("approve-researcher", help="Grant research access")
    a.add_argument("email")
    r = sub.add_parser("revoke-researcher", help="Withdraw research access")
    r.add_argument("email")
    g = sub.add_parser("grant-role", help="Promote a user to a privileged role")
    g.add_argument("email")
    g.add_argument("role", choices=sorted(PRIVILEGED))
    g.add_argument("--institution-id")
    rr = sub.add_parser("revoke-role", help="Return a user to the researcher role")
    rr.add_argument("email")
    sub.add_parser("list-privileged", help="Show privileged and approved accounts")
    sub.add_parser("migrate-dates",
                   help="Truncate stored clinical dates to year (irreversible)")
    sub.add_parser("remove-placeholder-institutions",
                   help="Delete seeded rows naming real hospitals")
    sa = sub.add_parser("self-audit",
                        help="Re-derive every safety invariant from live data")
    sa.add_argument("--json", action="store_true", help="Machine-readable output")

    args = parser.parse_args(argv)
    session = SessionLocal()
    try:
        if args.command == "approve-researcher":
            return approve_researcher(session, args.email)
        if args.command == "revoke-researcher":
            return revoke_researcher(session, args.email)
        if args.command == "grant-role":
            return grant_role(session, args.email, args.role, args.institution_id)
        if args.command == "revoke-role":
            return revoke_role(session, args.email)
        if args.command == "migrate-dates":
            return migrate_dates(session)
        if args.command == "remove-placeholder-institutions":
            return remove_placeholders(session)
        if args.command == "self-audit":
            return self_audit(session, as_json=args.json)
        return list_privileged(session)
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
