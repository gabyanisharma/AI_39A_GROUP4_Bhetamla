#!/usr/bin/env python3
"""
Quick setup helper for Bhetamla.
Helps you configure MySQL and email settings.
"""

import os
import sys

def create_env_file():
    """Create .env file interactively."""
    print("\n" + "="*70)
    print("  BHETAMLA QUICK SETUP")
    print("="*70)
    
    print("\n🔧 MySQL Configuration")
    print("-" * 70)
    print("You need your MySQL root password.")
    print("If you don't know it, you can reset it. See instructions below.")
    
    mysql_host = input("\nMySQL Host [localhost]: ").strip() or "localhost"
    mysql_user = input("MySQL User [root]: ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()
    mysql_db = input("MySQL Database [bhetamla_db]: ").strip() or "bhetamla_db"
    
    if not mysql_password:
        print("\n⚠️  WARNING: No MySQL password provided!")
        print("The app will not be able to connect to the database.")
        reset_choice = input("Would you like instructions to reset your MySQL password? (y/n): ").lower()
        if reset_choice == 'y':
            print_mysql_reset_instructions()
            return
    
    print("\n📧 Email Configuration (Optional)")
    print("-" * 70)
    print("Leave blank to skip email verification (testing only).")
    mail_username = input("Email address (Gmail): ").strip() or ""
    mail_password = input("Email app password: ").strip() or ""
    
    # Create .env file
    env_content = f"""# Database Configuration
MYSQL_HOST={mysql_host}
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DB={mysql_db}

# Flask Configuration
SECRET_KEY=bhetamla-secret-2024
FLASK_ENV=development

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME={mail_username}
MAIL_PASSWORD={mail_password}
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✓ .env file created at {env_path}")
    print("\nConfiguration saved:")
    print(f"  MySQL: {mysql_user}@{mysql_host}/{mysql_db}")
    if mail_username:
        print(f"  Email: {mail_username}")
    else:
        print(f"  Email: (not configured - email verification disabled)")
    
    # Next steps
    print("\n" + "="*70)
    print("  NEXT STEPS")
    print("="*70)
    print("""
1. Initialize the database:
   python setup_database.py

2. Run the Flask app:
   python run.py

3. Open http://localhost:5000 and register a user

4. For email verification:
   - Check your email inbox (or spam folder)
   - Or disable verification (see instructions below)
""")

def print_mysql_reset_instructions():
    """Print MySQL password reset instructions."""
    print("\n" + "="*70)
    print("  MYSQL PASSWORD RESET INSTRUCTIONS")
    print("="*70)
    
    print("""
macOS (Homebrew):
  1. Stop MySQL:        brew services stop mysql
  2. Start safe mode:   mysqld_safe --skip-grant-tables &
  3. Connect:           mysql -u root
  4. Run this SQL:
     FLUSH PRIVILEGES;
     ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';
     EXIT;
  5. Restart MySQL:     brew services restart mysql
  6. Verify:            mysql -u root -p -e "SELECT VERSION();"

Linux (apt):
  1. Stop MySQL:        sudo systemctl stop mysql
  2. Start safe mode:   sudo mysqld_safe --skip-grant-tables &
  3. Connect:           mysql -u root
  4. Run the same SQL as above
  5. Restart:           sudo systemctl restart mysql

Windows:
  1. Open Services (services.msc)
  2. Stop "MySQL80" service
  3. Open command prompt as admin
  4. Run: mysqld --skip-grant-tables
  5. In another cmd window, run: mysql -u root
  6. Run the same SQL as above

After resetting, run this script again to configure Bhetamla.
""")

def print_email_setup():
    """Print Gmail app password setup instructions."""
    print("""
Email Setup for Gmail:
  1. Enable 2-Factor Authentication on your Google account
  2. Go to https://myaccount.google.com/apppasswords
  3. Create "App password" for "Mail" and "Mac"
  4. Copy the 16-character password
  5. Use it as "Email app password" in the setup
""")

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
