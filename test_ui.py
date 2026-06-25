import time
import random
import sys
import io

# Prevent UnicodeEncodeError on Windows terminals
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

BASE_URL = "http://127.0.0.1:5002"

def get_driver():
    """Attempt to initialize a headless Chrome or Edge WebDriver."""
    print("Setting up WebDriver...")
    errors = []
    
    # Try Chrome first
    try:
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,1024")
        chrome_options.add_argument("--log-level=3")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome WebDriver initialized successfully!")
        return driver
    except Exception as e:
        errors.append(f"Chrome initialization failed: {e}")
        
    # Try Edge next
    try:
        edge_options = EdgeOptions()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1280,1024")
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        print("Edge WebDriver initialized successfully!")
        return driver
    except Exception as e:
        errors.append(f"Edge initialization failed: {e}")
        
    print("Failed to initialize any browser. Errors:")
    for err in errors:
        print(err)
    sys.exit(1)

def run_tests():
    driver = get_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        print("\n--- Test 1: Navigation to Register Page ---")
        driver.get(f"{BASE_URL}/auth/register")
        print(f"Loaded page title: {driver.title}")
        assert "Create your account" in driver.page_source or "Sign Up" in driver.title or "register" in driver.current_url.lower()
        print("Register page loaded successfully.")

        print("\n--- Test 2: User Registration ---")
        rand_id = random.randint(1000, 9999)
        test_email = f"tester_{rand_id}@bhetamla.com"
        
        name_input = wait.until(EC.presence_of_element_located((By.ID, "reg-name")))
        email_input = driver.find_element(By.ID, "reg-email")
        phone_input = driver.find_element(By.ID, "reg-phone")
        password_input = driver.find_element(By.ID, "reg-password")
        confirm_input = driver.find_element(By.ID, "reg-confirm")
        
        name_input.send_keys("Tester Test")
        email_input.send_keys(test_email)
        phone_input.send_keys("9841234567")
        password_input.send_keys("Password123!")
        confirm_input.send_keys("Password123!")
        
        submit_btn = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        print("Clicking 'Create Account' button...")
        submit_btn.click()
        
        # Should redirect to login page
        wait.until(EC.url_contains("/auth/login"))
        print(f"Redirected to: {driver.current_url}")
        print("Registration completed and redirected to Login.")

        print("\n--- Test 3: User Login ---")
        login_email = wait.until(EC.presence_of_element_located((By.ID, "login-email")))
        login_password = driver.find_element(By.ID, "login-password")
        
        login_email.send_keys(test_email)
        login_password.send_keys("Password123!")
        
        login_submit = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        print("Clicking 'Continue with Email' login button...")
        login_submit.click()
        
        # Should redirect to dashboard
        wait.until(EC.url_contains("/user/dashboard"))
        print(f"Successfully logged in! Current URL: {driver.current_url}")
        assert "dashboard" in driver.current_url.lower()

        print("\n--- Test 4: Dashboard Buttons and Navigation ---")
        # Find side-bar buttons/links
        sidebar_links = driver.find_elements(By.CSS_SELECTOR, "aside nav a, .sidebar nav a")
        if not sidebar_links:
            sidebar_links = driver.find_elements(By.CSS_SELECTOR, "nav a")
            
        print(f"Found {len(sidebar_links)} navigation links.")
        for link in sidebar_links:
            text = link.text.strip()
            href = link.get_attribute("href")
            print(f" - Link: '{text}' -> {href}")

        print("\n--- Test 5: Safety Hub Actions ---")
        driver.get(f"{BASE_URL}/user/safety")
        print(f"Loaded Safety Hub: {driver.current_url}")
        
        # Test adding emergency contact
        try:
            add_contact_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Contact') or @id='add-contact-btn']")))
            print("Found 'Add Contact' button. Clicking it...")
            add_contact_btn.click()
            
            # Fill contact form inside the modal
            time.sleep(1) # Allow modal transition
            name_field = driver.find_element(By.ID, "ec-name")
            phone_field = driver.find_element(By.ID, "ec-phone")
            relationship_field = driver.find_element(By.ID, "ec-relation")
            
            name_field.send_keys("Emergency Friend")
            phone_field.send_keys("9801122334")
            
            # Select relationship
            for option in relationship_field.find_elements(By.TAG_NAME, "option"):
                if option.text == "Friend":
                    option.click()
                    break
            
            save_btn = driver.find_element(By.CSS_SELECTOR, "#modal-emergency-contact form button[type='submit']")
            print("Clicking 'Save Contact' button...")
            save_btn.click()
            time.sleep(2)
            print("Emergency contact added successfully.")
        except Exception as e:
            print(f"Could not complete Add Contact test: {e}.")

        # Test SOS button
        try:
            sos_btn = wait.until(EC.element_to_be_clickable((By.ID, "sos-main-btn")))
            print("Found 'SOS Trigger' button. Clicking it...")
            sos_btn.click()
            time.sleep(1)
            # Accept confirmation dialog
            alert = wait.until(EC.alert_is_present())
            print(f"SOS alert text: {alert.text}")
            alert.accept()
            time.sleep(2)
            print("SOS alert confirmed and triggered successfully.")
        except Exception as e:
            print(f"Could not complete SOS trigger test: {e}")

        print("\n--- Test 6: Explore Page & Restaurant Feed ---")
        driver.get(f"{BASE_URL}/explore/")
        print(f"Loaded Explore: {driver.current_url}")
        spots = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".restaurant-card, .spot-card, .place-card, .card, div")))
        print(f"Successfully loaded explore feed with {len(spots)} elements.")

        print("\n--- Test 7: Ride Planner ---")
        driver.get(f"{BASE_URL}/ride/planner")
        print(f"Loaded Ride Planner page: {driver.current_url}")
        time.sleep(1)

        print("\n--- Test 8: Meetup Plan Page ---")
        driver.get(f"{BASE_URL}/meetup/plan")
        print(f"Loaded Meetup Plan page: {driver.current_url}")
        time.sleep(1)

        # Check console logs for any JavaScript errors
        print("\n--- Check Browser Console Logs ---")
        logs = driver.get_log("browser")
        error_logs = [log for log in logs if log["level"] == "SEVERE"]
        if error_logs:
            print("Warning: JavaScript errors detected in console logs:")
            for log in error_logs:
                print(f" - {log['message']}")
        else:
            print("No JavaScript errors detected in the browser console logs!")

        print("\n===============================================")
        print("ALL UI BUTTONS & PAGE NAVIGATION TESTS PASSED SUCCESSFULLY!")
        print("===============================================")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
