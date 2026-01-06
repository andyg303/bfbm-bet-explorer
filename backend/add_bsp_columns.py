import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def add_bsp_columns():
    """Add BSP metric columns to the bets table"""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    
    cursor = conn.cursor()
    
    try:
        print("Adding BSP metric columns...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='bets' AND column_name='bsp_diff_absolute'
        """)
        
        if cursor.fetchone():
            print("BSP columns already exist")
        else:
            cursor.execute("""
                ALTER TABLE bets 
                ADD COLUMN bsp_diff_absolute FLOAT,
                ADD COLUMN bsp_diff_percentage FLOAT,
                ADD COLUMN bsp_diff_probability FLOAT
            """)
            conn.commit()
            print("BSP columns added successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        raise

if __name__ == "__main__":
    add_bsp_columns()
