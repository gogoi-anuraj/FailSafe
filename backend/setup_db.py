"""
FAILSAFE — Database Setup Script
Run once before starting the server:
    python setup_db.py

Creates tables and a default test user.
"""

from database import create_tables
from database import SessionLocal, User
from auth     import hash_password


def main():
    print("Creating tables...")
    create_tables()

    db = SessionLocal()
    try:
        # Create a default test user if none exist
        existing = db.query(User).first()
        if not existing:
            test_user = User(
                name     = "Faculty Demo",
                email    = "faculty@failsafe.edu",
                password = hash_password("password123")
            ) 
            db.add(test_user)
            db.commit()
            print("Default user created:")
            print("  Email   : faculty@failsafe.edu")
            print("  Password: password123")
            print("  (Change this before going to production!)")
        else:
            print("Users already exist — skipping default user creation.")
    finally:
        db.close()

    print("\nSetup complete! Start the server with:")
    print("  uvicorn main:app --reload")


if __name__ == "__main__":
    main()
