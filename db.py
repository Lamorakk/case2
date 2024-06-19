import MySQLdb
import logging

db_config = {
    'user': 'root',
    'passwd': 'root',
    'host': '127.0.0.1',
    'db': 'quizik'
}

conn = MySQLdb.connect(**db_config)
cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS quizik")
cursor.execute("USE quizik")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT,
        username VARCHAR(50),
        name VARCHAR(50),
        surname VARCHAR(50),
        age_group VARCHAR(10),
        familiarity VARCHAR(50),
        previous_site VARCHAR(50),
        communicative VARCHAR(50),
        english_level VARCHAR(10),
        other_languages VARCHAR(50),
        phone_number VARCHAR(20),
        social_links VARCHAR(100),
        contact_info VARCHAR(100) 
    )
""")

# Function to check if a column exists in a table
def column_exists(cursor, table_name, column_name):
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{column_name}';
    """)
    return cursor.fetchone()[0] > 0

# Check and add columns if they do not exist
if not column_exists(cursor, 'responses', 'social_links'):
    cursor.execute("ALTER TABLE responses ADD COLUMN social_links VARCHAR(100)")

if not column_exists(cursor, 'responses', 'contact_info'):
    cursor.execute("ALTER TABLE responses ADD COLUMN contact_info VARCHAR(100)")

conn.commit()
cursor.close()
conn.close()
