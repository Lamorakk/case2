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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT,
        username VARCHAR(50),
        name VARCHAR(50),
        surname VARCHAR(50),
        age_group VARCHAR(10),
        familiarity_with_field VARCHAR(50),
        previous_site VARCHAR(50),
        communicative VARCHAR(50),
        english_level VARCHAR(10),
        other_languages VARCHAR(50),
        phone_number VARCHAR(20),
        social_media VARCHAR(100)
    )
""")

conn.commit()

cursor.close()
conn.close()
