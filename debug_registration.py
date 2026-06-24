#!/usr/bin/env python3
"""
Debug script for registration issues.
Run this to diagnose registration failures.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from config import Config
from app.database import get_db_connection, execute_query
from app.models.user import User

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('debug_registration')

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    print(f"\n► {title}")
    print("-" * 70)

def check_database_config():
    """Check database configuration."""
    print_section("Database Configuration")
    print(f"  Host: {Config.MYSQL_HOST}")
    print(f"  User: {Config.MYSQL_USER}")
    print(f"  Password: {'[SET]' if Config.MYSQL_PASSWORD else '[EMPTY]'}")
    print(f"  Database: {Config.MYSQL_DB}")

def check_database_connection():
    """Verify database connection."""
    print_section("Database Connection Test")
    try:
        conn = get_db_connection()
        if conn:
            print("✓ Database connection successful!")
            conn.close()
            return True
        else:
            print("✗ Database connection returned None")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False

def check_users_table():
    """Check if users table exists and its structure."""
    print_section("Users Table Structure")
    
    try:
        query = "DESCRIBE users"
        result = execute_query(query, fetch=True)
        
        if result:
            print("✓ Users table exists!")
            print("\nTable columns:")
            for row in result:
                print(f"  - {row['Field']}: {row['Type']} (Null: {row['Null']}, Key: {row['Key']})")
            return True
        else:
            print("✗ Users table does not exist or query failed")
            return False
    except Exception as e:
        print(f"✗ Error checking table structure: {e}")
        return False

def test_user_creation():
    """Test the user creation process step by step."""
    print_section("Test User Creation Process")
    
    test_email = f"debug_test_{int(__import__('time').time())}@test.com"
    test_data = {
        'full_name': 'Debug Test User',
        'email': test_email,
        'phone': '+977-9841234567',
        'password': 'TestPassword123'
    }
    
    print(f"Testing with data:")
    for key, value in test_data.items():
        print(f"  - {key}: {value}")
    
    # Test email_exists
    print(f"\n1. Testing User.email_exists('{test_email}')...")
    try:
        exists = User.email_exists(test_email)
        print(f"   Result: {exists} (should be False)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test user creation
    print(f"\n2. Testing User.create()...")
    try:
        user_id = User.create(
            test_data['full_name'],
            test_data['email'],
            test_data['phone'],
            test_data['password']
        )
        print(f"   Result: user_id = {user_id}")
        
        if user_id:
            print(f"   ✓ User creation successful!")
            
            # Test retrieval
            print(f"\n3. Testing User.get_by_id({user_id})...")
            user = User.get_by_id(user_id)
            if user:
                print(f"   ✓ User retrieved successfully")
                print(f"   User data: {user}")
                return True
            else:
                print(f"   ✗ Could not retrieve user after creation")
                return False
        else:
            print(f"   ✗ User creation failed (returned {user_id})")
            return False
    except Exception as e:
        print(f"   ✗ Error during user creation: {e}")
        return False

def check_form_fields():
    """Verify form field names in HTML template."""
    print_section("Registration Form Fields")
    
    template_path = 'app/templates/auth/register.html'
    required_fields = ['full_name', 'email', 'phone', 'password', 'confirm_password']
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        print(f"Checking for required form fields in {template_path}:")
        all_found = True
        for field in required_fields:
            if f'name="{field}"' in content:
                print(f"  ✓ {field}")
            else:
                print(f"  ✗ {field} NOT FOUND")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"✗ Error reading template: {e}")
        return False

def main():
    print_header("BHETAMLA REGISTRATION DEBUG SCRIPT")
    
    checks = [
        ("Database Configuration", check_database_config),
        ("Database Connection", check_database_connection),
        ("Users Table", check_users_table),
        ("Form Fields", check_form_fields),
        ("User Creation", test_user_creation),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"Error in {check_name}: {e}", exc_info=True)
            results[check_name] = False
    
    # Summary
    print_header("DEBUG SUMMARY")
    print("\nResults:")
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {check_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All checks passed! Registration should work.")
    else:
        print("\n✗ Some checks failed. See details above.")
        print("\nCommon issues:")
        if not results.get("Database Connection"):
            print("  • Database credentials in config.py may be incorrect")
            print("  • MySQL may not be running")
            print("  • Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD in config.py")
        if not results.get("Users Table"):
            print("  • Users table not created in database")
            print("  • Run database schema setup/migration")
        if not results.get("Form Fields"):
            print("  • HTML form field names don't match expected names")
            print("  • Required fields: full_name, email, phone, password, confirm_password")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit(main())
