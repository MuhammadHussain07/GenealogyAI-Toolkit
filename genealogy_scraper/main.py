import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

# --- CONFIGURATIONS ---
TREE_PAGE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"



# --- STEP 1: Login ---
def selenium_login():
    print("[INFO] Launching undetected Selenium...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)

    try:
        driver.get(ANCESTRY_URL)

        print("[INFO] Waiting for the login form...")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))

        # Fill login credentials
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        print("[INFO] Waiting for login to complete...")
        WebDriverWait(driver, 30).until(EC.url_contains("ancestry.com"))

        print("[SUCCESS] Login successful!")
        return driver

    except Exception as e:
        print(f"[ERROR] Selenium login failed: {e}")
        driver.quit()
        return None


# --- STEP 2: Extract data from the tree page ---
def extract_tree_data(driver):
    print("[INFO] Navigating to the tree page...")
    driver.get(TREE_PAGE_URL)

    print("[INFO] Waiting for the tree page to load...")
    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
    )

    print("[INFO] Extracting tree data...")
    data = []

    # Extract names, DoBs, and image URLs
    try:
        nodes = driver.find_elements(By.CSS_SELECTOR, "span.nodeTitle.notranslate")
        dob_nodes = driver.find_elements(By.CSS_SELECTOR, "span.nodeInfo")
        image_nodes = driver.find_elements(By.CSS_SELECTOR, "span.nodePhoto img")

        for i, node in enumerate(nodes):
            name = node.text.strip()
            dob = dob_nodes[i].text.strip() if i < len(dob_nodes) else "N/A"
            image_url = image_nodes[i].get_attribute("src") if i < len(image_nodes) else "N/A"
            data.append({"Name": name, "DoB": dob, "ImageURL": image_url})

    except Exception as e:
        print(f"[ERROR] Failed to extract tree data: {e}")

    return data


# --- STEP 3: Extract detailed information ---
def extract_details(driver, data):
    print("[INFO] Extracting detailed information for each profile...")
    enriched_data = []

    for person in data:
        try:
            print(f"[INFO] Extracting details for: {person['Name']}...")
            # Click on the person's profile
            person_node = driver.find_element(By.XPATH, f'//span[text()="{person["Name"]}"]')
            person_node.click()

            # Wait for the profile page to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "hoverBirthDate")))

            # Extract additional information
            birth_date = driver.find_element(By.ID, "hoverBirthDate").text
            birth_place = driver.find_element(By.ID, "hoverBirthPlace").text
            death_date = driver.find_element(By.ID, "hoverDeathDate").text
            death_place = driver.find_element(By.ID, "hoverDeathPlace").text

            person.update({
                "BirthDate": birth_date,
                "BirthPlace": birth_place,
                "DeathDate": death_date,
                "DeathPlace": death_place,
            })
            enriched_data.append(person)

            # Navigate back to the tree page
            driver.back()
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate")))

        except Exception as e:
            print(f"[ERROR] Failed to extract details for {person['Name']}: {e}")
            person.update({
                "BirthDate": "N/A",
                "BirthPlace": "N/A",
                "DeathDate": "N/A",
                "DeathPlace": "N/A",
            })
            enriched_data.append(person)

    return enriched_data


# --- STEP 4: Save the extracted data to a CSV ---
def save_to_csv(data):
    print("[INFO] Saving data to a CSV file...")
    with open("ancestry_data.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["Name", "DoB", "ImageURL", "BirthDate", "BirthPlace", "DeathDate", "DeathPlace"])
        writer.writeheader()
        writer.writerows(data)
    print("[SUCCESS] Data saved to ancestry_data.csv!")


# --- MAIN FUNCTION ---
def main():
    driver = selenium_login()
    if not driver:
        print("[ERROR] Selenium login failed. Exiting.")
        return

    tree_data = extract_tree_data(driver)
    if not tree_data:
        print("[ERROR] No data extracted from the tree page.")
        return

    detailed_data = extract_details(driver, tree_data)
    save_to_csv(detailed_data)

    driver.quit()
    print("[INFO] Process completed successfully!")


if __name__ == "__main__":
    main()
