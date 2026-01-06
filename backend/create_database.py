import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os

load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        raise

if __name__ == "__main__":
    create_database()
