# add_column_db.py
import sqlite3
from datetime import datetime
import os
from shutil import copyfile

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to the instance directory and database file
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'new_database_V4.db')

def migrate_database():
    # Connect to the database using absolute path
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print(f"Connected to database at: {DB_PATH}")
        # Begin transaction
        cursor.execute('BEGIN TRANSACTION')

        print("Creating new post table...")
        # Create new table with is_sold column
        cursor.execute('''
            CREATE TABLE post_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                price FLOAT NOT NULL,
                category VARCHAR(20) NOT NULL,
                uuid VARCHAR(36) NOT NULL,
                created_at DATETIME,
                post_password VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(120),
                is_sold BOOLEAN NOT NULL DEFAULT 0
            )
        ''')

        print("Copying data to new table...")
        # Copy data from old table to new table
        cursor.execute('''
            INSERT INTO post_new (
                id, title, description, price, category, uuid,
                created_at, post_password, phone, email
            )
            SELECT 
                id, title, description, price, category, uuid,
                created_at, post_password, phone, email
            FROM post
        ''')

        print("Dropping old table...")
        # Drop old table
        cursor.execute('DROP TABLE post')

        print("Renaming new table...")
        # Rename new table to original name
        cursor.execute('ALTER TABLE post_new RENAME TO post')

        # Commit transaction
        cursor.execute('COMMIT')
        print("Migration completed successfully!")

    except Exception as e:
        # Rollback in case of error
        cursor.execute('ROLLBACK')
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # First verify the database exists
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {BASE_DIR}")
        print(f"Looking for database in instance directory: {INSTANCE_DIR}")
        exit(1)

    # Create backup with timestamp in the same directory as the original
    backup_name = f'new_database_V4_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    backup_path = os.path.join(INSTANCE_DIR, backup_name)

    try:
        print(f"Creating backup of database...")
        copyfile(DB_PATH, backup_path)
        print(f"Backup created: {backup_path}")

        print(f"Starting migration...")
        migrate_database()
        print(f"Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")