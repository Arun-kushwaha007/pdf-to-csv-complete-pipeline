"""
Database setup script for PDF to CSV Pipeline
Run this script to create the database schema
"""

import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    """Setup database schema"""
    load_dotenv('config.env')
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("❌ Missing database configuration in config.env")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Read and execute schema
        with open('database_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                cursor.execute(statement)
                print(f"✅ Executed: {statement[:50]}...")
        
        conn.commit()
        print("✅ Database schema created successfully!")
        
        # Test the tables
        cursor.execute("SELECT COUNT(*) FROM raw_records")
        raw_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM filtered_records")
        filtered_count = cursor.fetchone()[0]
        
        print(f"📊 Raw records table: {raw_count} records")
        print(f"📊 Filtered records table: {filtered_count} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Setting up database schema...")
    success = setup_database()
    if success:
        print("🎉 Database setup completed successfully!")
    else:
        print("💥 Database setup failed!")
