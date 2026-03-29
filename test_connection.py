"""
Test MySQL database connection using SQLAlchemy
"""
from sqlalchemy import text
from config import engine

def test_connection():
    """Test connection to MySQL server"""
    try:
        # Attempt to connect
        with engine.connect() as connection:
            result = connection.execute(text("SELECT VERSION()"))
            version = result.fetchone()
            print(f"✓ MySQL connection successful!")
            print(f"MySQL version: {version[0]}")
            print("✓ Connection test completed successfully!")
            return True
            
    except Exception as e:
        print(f"✗ Error connecting to MySQL: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that MySQL server is running")
        print("2. Verify username and password in config.py are correct")
        print("3. Ensure MySQL is listening on port 3306")
        return False

if __name__ == "__main__":
    test_connection()
