"""
Creates the 5 standard roles (customer, cashier, manager, admin, owner) and an admin/owner user.

Usage (from the backend folder, with your .env DATABASE_URL set):
    python -m app.scripts.create_admin --email owner@freshcobakers.com --name "Owner" --role owner --create-tables

--create-tables runs Base.metadata.create_all() first (handy for a fresh local dev DB;
for production use Alembic migrations instead).
"""
import argparse
import getpass

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.services.auth_service import get_or_create_role

ROLES = ["customer", "cashier", "manager", "admin", "owner"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create roles and an admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Administrator")
    parser.add_argument("--role", default="owner", choices=ROLES)
    parser.add_argument("--password", default=None, help="If omitted you will be asked (recommended)")
    parser.add_argument("--create-tables", action="store_true")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")

    if args.create_tables:
        Base.metadata.create_all(engine)
        print("Tables created.")

    db = SessionLocal()
    try:
        roles = {name: get_or_create_role(db, name) for name in ROLES}
        user = db.query(User).filter(User.email == args.email).first()
        if user is None:
            user = User(name=args.name, email=args.email, password_hash=hash_password(password),
                        role_id=roles[args.role].id)
            db.add(user)
            action = "created"
        else:
            user.role_id = roles[args.role].id
            user.password_hash = hash_password(password)
            action = "updated"
        db.commit()
        print(f"User {args.email} {action} with role '{args.role}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
