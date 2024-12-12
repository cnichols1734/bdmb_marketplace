# migration_script.py
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

        print("Renaming existing tables...")
        # 1. Rename existing tables to temporary names
        cursor.execute('ALTER TABLE post RENAME TO post_old')
        cursor.execute('ALTER TABLE photo RENAME TO photo_old')
        cursor.execute('ALTER TABLE comment RENAME TO comment_old')

        print("Creating new tables with AUTOINCREMENT...")
        # 2. Create new tables with AUTOINCREMENT
        cursor.execute('''
            CREATE TABLE post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                price FLOAT NOT NULL,
                category VARCHAR(20) NOT NULL,
                uuid VARCHAR(36) NOT NULL,
                created_at DATETIME,
                post_password VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(120)
            )
        ''')

        cursor.execute('''
            CREATE TABLE photo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR(255),
                post_id INTEGER NOT NULL,
                timestamp DATETIME,
                FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE comment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                timestamp DATETIME,
                FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE
            )
        ''')

        print("Copying data to new tables...")
        # 3. Copy data from old tables to new tables
        cursor.execute('INSERT INTO post SELECT * FROM post_old')
        cursor.execute('INSERT INTO photo SELECT * FROM photo_old')
        cursor.execute('INSERT INTO comment SELECT * FROM comment_old')

        print("Cleaning up old tables...")
        # 4. Drop old tables
        cursor.execute('DROP TABLE post_old')
        cursor.execute('DROP TABLE photo_old')
        cursor.execute('DROP TABLE comment_old')

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