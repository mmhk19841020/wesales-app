
import sys
import os
print(f"Python Executable: {sys.executable}")
print(f"Sys Path: {sys.path}")

try:
    from sqlalchemy import text
    print("SQLAlchemy imported successfully.")
except ImportError as e:
    print(f"Error importing SQLAlchemy: {e}")
    sys.exit(1)

from app import create_app
from extensions import db
from models import User, Card

app = create_app()

def migrate():
    with app.app_context():
        print("Starting migration...")
        
        # 1. User table check
        print("Checking User table...")
        inspector = db.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('user')]
        
        if 'last_name' not in columns:
            print("Adding last_name column to User...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN last_name VARCHAR(100)"))
                conn.commit()
        if 'first_name' not in columns:
            print("Adding first_name column to User...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN first_name VARCHAR(100)"))
                conn.commit()

        # 2. Card table check
        print("Checking Card table...")
        columns = [c['name'] for c in inspector.get_columns('card')]
        
        if 'last_name' not in columns:
            print("Adding last_name column to Card...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE card ADD COLUMN last_name VARCHAR(100)"))
                conn.commit()
        if 'first_name' not in columns:
            print("Adding first_name column to Card...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE card ADD COLUMN first_name VARCHAR(100)"))
                conn.commit()

        # 3. Data Migration
        print("Migrating User data...")
        users = User.query.all()
        for user in users:
            if user.real_name:
                parts = user.real_name.strip().replace('　', ' ').split(' ', 1) 
                if len(parts) == 2:
                    user.last_name = parts[0]
                    user.first_name = parts[1]
                else:
                    user.last_name = parts[0]
                    user.first_name = ""
            db.session.add(user)
        
        print("Migrating Card data...")
        cards = Card.query.all()
        for card in cards:
            if card.person_name:
                parts = card.person_name.strip().replace('　', ' ').split(' ', 1)
                
                if len(parts) == 2:
                    card.last_name = parts[0]
                    card.first_name = parts[1]
                else:
                    card.last_name = parts[0]
                    card.first_name = ""
            db.session.add(card)

        db.session.commit()
        print("Migration completed.")

if __name__ == "__main__":
    migrate()
