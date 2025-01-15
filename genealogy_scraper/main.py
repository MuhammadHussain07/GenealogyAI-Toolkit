import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATIONS ---
ANCESTRY_URL = "https://www.ancestry.com/signin"
TREE_PAGE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
EMAIL = "anthonymdavenport@gmail.com"
PASSWORD = "*****************"

def initialize_driver():
    """Initialize undetected Chrome driver."""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)
    return driver

def login_and_navigate(driver):
    """Logs in to ancestry.com, clicks 'Sign in', and navigates to the family tree page."""
    try:
        print("[INFO] Opening Ancestry login page...")
        driver.get(ANCESTRY_URL)
        time.sleep(3)  # Wait for the page to load
        
        # Wait for the login form
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))

        # Simulate human typing for email
        print("[INFO] Entering email...")
        email_field = driver.find_element(By.ID, "username")
        for char in EMAIL:
            email_field.send_keys(char)
            time.sleep(0.1)  # Simulate typing delay

        # Simulate human typing for password
        print("[INFO] Entering password...")
        password_field = driver.find_element(By.ID, "password")
        for char in PASSWORD:
            password_field.send_keys(char)
            time.sleep(0.1)  # Simulate typing delay

        # Click the "Sign in" button
        print("[INFO] Clicking the 'Sign in' button...")
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        # Wait for page redirection or check for error messages
        print("[INFO] Waiting for the page to redirect...")
        time.sleep(5)  # Allow time for redirection
        if "signin" in driver.current_url.lower():
            print("[ERROR] Login failed. Capturing screenshot...")
            driver.save_screenshot("login_error.png")
            return False

        print("[SUCCESS] Login successful!")

        # Navigate to the family tree page
        print("[INFO] Navigating to the family tree page...")
        driver.get(TREE_PAGE_URL)
        time.sleep(3)  # Wait for the tree page to load
        
        # Verify tree page loaded
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
        )
        print("[SUCCESS] Family tree page loaded successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] An error occurred during login or navigation: {e}")
        driver.save_screenshot("error.png")
        driver.quit()
        return False

if __name__ == "__main__":
    driver = initialize_driver()
    if login_and_navigate(driver):
        print("[INFO] Task completed successfully!")
    driver.quit()
