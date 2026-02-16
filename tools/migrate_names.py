
import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path to allow importing from the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Card

app = create_app()

def migrate():
    with app.app_context():
        print("Starting migration...")
        
        # 1. User table check
        print("Checking User table...")
        # Check if columns exist (SQLite specific, but works for general idea)
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
                parts = user.real_name.split(' ', 1) # simple split by first space
                if len(parts) == 2:
                    user.last_name = parts[0]
                    user.first_name = parts[1]
                else:
                    user.last_name = user.real_name
                    user.first_name = ""
            print(f"User {user.id}: {user.real_name} -> {user.last_name} {user.first_name}")
        
        print("Migrating Card data...")
        cards = Card.query.all()
        for card in cards:
            if card.person_name:
                # remove ZWSP or extra spaces if any
                name = card.person_name.strip()
                # try splitting by full-width space or half-width space
                # standardize space
                name = name.replace('　', ' ')
                parts = name.split(' ', 1)
                
                if len(parts) == 2:
                    card.last_name = parts[0]
                    card.first_name = parts[1]
                else:
                    card.last_name = name
                    card.first_name = ""
            print(f"Card {card.id}: {card.person_name} -> {card.last_name} {card.first_name}")

        db.session.commit()
        print("Migration completed.")

if __name__ == "__main__":
    migrate()
