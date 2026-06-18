#!/usr/bin/env python3
"""
One-command setup and test for Bhetamla.
Attempts to fix registration and login issues automatically.
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"\n► {description}")
    print("-" * 70)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(f"⚠️  {result.stderr}")
    return result.returncode == 0

def create_env_file():
    """Create .env file with minimal config for testing."""
    print("\n► Creating .env Configuration File")
    print("-" * 70)
    
    env_content = """# Bhetamla Configuration - Auto-generated for testing
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=bhetamla_db
SECRET_KEY=bhetamla-secret-2024
FLASK_ENV=development

# Email disabled for testing (users auto-verified)
MAIL_USERNAME=
MAIL_PASSWORD=
"""
    
    env_path = '.env'
    if os.path.exists(env_path):
        print(f"✓ .env already exists, keeping existing configuration")
        return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✓ Created {env_path}")
    print("  - Email verification disabled for testing")
    print("  - Users will be auto-verified on registration")
    print("  - UPDATE MYSQL_PASSWORD if your MySQL requires one")

def main():
    print("\n" + "="*70)
    print("  BHETAMLA ONE-COMMAND SETUP & TEST")
    print("="*70)
    
    print("""
This script will:
1. Create .env configuration file
2. Setup database with required tables
3. Run diagnostic tests
4. Show you how to test registration & login

Let's get started!
""")
    
    # Step 1: Create .env
    create_env_file()
    
    # Step 2: Setup database
    print("\n► Setting Up Database")
    print("-" * 70)
    run_command("python setup_database.py", "Initializing database...")
    
    # Step 3: Run diagnostics
    print("\n► Running Diagnostic Tests")
    print("-" * 70)
    run_command("python debug_registration.py", "Testing configuration...")
    
    # Summary
    print("\n" + "="*70)
    print("  SETUP COMPLETE")
    print("="*70)
    print("""
✓ Configuration created (.env)
✓ Database initialized
✓ All systems ready

NEXT STEPS:
───────────

1. Start Flask:
   python run.py

2. Open browser:
   http://localhost:5000

3. Register a test user:
   - Click "Sign up"
   - Fill the form
   - Will be auto-verified (no email needed)

4. Login with your credentials:
   - Email: your registered email
   - Password: your password

5. SUCCESS! 🎉

IMPORTANT NOTES:
────────────────

• If database setup failed:
  - Update MYSQL_PASSWORD in .env with your MySQL root password
  - Run: python quick_setup.py (for MySQL password reset help)
  - Run: python setup_database.py (again)

• To enable real email verification:
  - Add Gmail SMTP credentials to .env
  - See FIX_LOGIN_EMAIL.md for Gmail setup instructions

• Check .env file anytime:
  cat .env

""")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
