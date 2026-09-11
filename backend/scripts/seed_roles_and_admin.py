"""Seed initial roles and an optional admin user.
Run: python scripts/seed_roles_and_admin.py --admin-user admin --admin-pass changeme
"""
import argparse
from app.core.database import SessionLocal
from app.models.identity import Role, Org, User
from sqlalchemy.exc import IntegrityError
from app.services.auth_service import register_user


def seed(admin_user: str | None, admin_pass: str | None):
    db = SessionLocal()
    try:
        for name, desc in [("admin", "Super administrator"), ("pentester", "Pentest user"), ("auditor", "Read-only auditor")]:
            r = db.query(Role).filter(Role.name == name).first()
            if not r:
                db.add(Role(name=name, description=desc))
        db.commit()
    except IntegrityError:
        db.rollback()

    if admin_user and admin_pass:
        # create org
        org = db.query(Org).filter(Org.name == "default").first()
        if not org:
            org = Org(name="default")
            db.add(org)
            db.commit()
            db.refresh(org)
        # create admin user via register_user
        try:
            register_user(admin_user, admin_pass, role="admin")
        except Exception:
            pass
        # set role on user
        u = db.query(User).filter(User.username == admin_user).first()
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if u and admin_role:
            u.role_id = admin_role.id
            u.org_id = org.id
            db.commit()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--admin-user", default=None)
    p.add_argument("--admin-pass", default=None)
    args = p.parse_args()
    seed(args.admin_user, args.admin_pass)
