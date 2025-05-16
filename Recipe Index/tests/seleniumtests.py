# tests/seleniumtests.py

import os
import sys
import time
import threading
import unittest

# ────────────────────────────────────────────────────────────────
# Make project root importable (so `import app` & `PopulateDB` work)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────

from app import app as flask_app, db
from PopulateDB import main as populate_db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

localHost = "http://localhost:5000/"

class BasicSeleniumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure Flask for testing
        flask_app.testing = True
        flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        # Create in-memory schema and seed data
        cls.ctx = flask_app.app_context()
        cls.ctx.push()
        db.create_all()
        # Seed via PopulateDB script, which reads sys.argv[1]
        prev_argv = sys.argv.copy()
        sys.argv = [sys.argv[0], '5']
        populate_db()
        sys.argv = prev_argv

        # Start Flask dev server in a thread
        def run_flask():
            flask_app.run(use_reloader=False)
        
        cls.server = threading.Thread(target=run_flask)
        cls.server.daemon = True
        cls.server.start()
        time.sleep(2)  # Give the server more time to start

        # Launch headless Chrome
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=opts)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        # No need to terminate the thread as it's a daemon thread
        db.drop_all()
        cls.ctx.pop()

    def test_seeded_user_login_flow(self):
        # Seeded user (Test User 1) should log in successfully
        self.driver.get(localHost + "login")
        # Fill form
        self.driver.find_element(By.ID, "email").send_keys("test1@email.com")
        self.driver.find_element(By.ID, "password").send_keys("1")
        # Click submit button
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(1)  # Give it a moment to process
        # Redirects to /profile
        self.assertTrue(self.driver.current_url.endswith("/profile"))

    def test_create_and_view_recipe(self):
        # Log in
        self.test_seeded_user_login_flow()
        # Go to Create page
        self.driver.find_element(By.CSS_SELECTOR, "button[onclick=\"location.href='/create'\"]").click()
        # Fill form
        title = f"Selenium Recipe {int(time.time())}"
        self.driver.find_element(By.ID, "title").send_keys(title)
        self.driver.find_element(By.ID, "description").send_keys("A delicious test dish.")
        self.driver.find_element(By.ID, "cook_time").send_keys("15")
        self.driver.find_element(By.ID, "servings").send_keys("2")
        # Select first ingredient
        select2_container = self.driver.find_element(By.CLASS_NAME, "select2-container")
        select2_container.click()
        time.sleep(0.5)  # Wait for dropdown to open
        first_option = self.driver.find_element(By.CLASS_NAME, "select2-results__option")
        first_option.click()
        # Add quantity
        self.driver.find_element(By.NAME, "quantity").send_keys("1")
        # Add instruction
        self.driver.find_element(By.NAME, "instructions").send_keys("Mix all ingredients")
        # Upload an image
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "image.jpeg"))
        self.driver.find_element(By.ID, "images").send_keys(img_path)
        # Submit form
        self.driver.execute_script("document.getElementById('recipeForm').submit();")
        # Wait for redirect
        time.sleep(2)  # Give more time for the redirect
        current_url = self.driver.current_url
        self.assertIn("/recipe?id=", current_url)
        # Page shows the title
        self.assertIn(title, self.driver.page_source)

    def test_search_recipe(self):
        # Create recipe then search for it
        self.test_create_and_view_recipe()
        # Use header search box
        self.driver.find_element(By.NAME, "q").send_keys("Selenium Recipe")
        self.driver.find_element(By.NAME, "q").send_keys(Keys.ENTER)
        time.sleep(1)
        # At least one result shows 'Selenium Recipe'
        results = self.driver.find_elements(By.XPATH, f"//h3[contains(text(), 'Selenium Recipe')]")
        self.assertGreater(len(results), 0)

    def test_edit_profile(self):
        # Log in
        self.test_seeded_user_login_flow()
        # Go to Profile
        self.driver.get(localHost + "profile")
        # Click Edit Profile
        self.driver.find_element(By.CLASS_NAME, "edit-profile-btn").click()
        time.sleep(1)
        # Change bio
        bio_input = self.driver.find_element(By.ID, "profile_description")
        bio_input.clear()
        new_bio = "Updated via Selenium"
        bio_input.send_keys(new_bio)
        # Upload profile image
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "image.jpeg"))
        self.driver.find_element(By.ID, "profile_image").send_keys(img_path)
        # Submit edits
        self.driver.find_element(By.CLASS_NAME, "edit-profile-btn").click()
        time.sleep(1)
        # Back on profile page, check new bio appears
        self.assertIn(new_bio, self.driver.page_source)

    def test_private_recipe_access(self):
        # Log in and create a private recipe
        self.test_seeded_user_login_flow()
        self.driver.find_element(By.CSS_SELECTOR, "button[onclick=\"location.href='/create'\"]").click()
        self.driver.find_element(By.ID, "title").send_keys("Private Dish")
        self.driver.find_element(By.ID, "description").send_keys("A private test recipe")
        self.driver.find_element(By.ID, "cook_time").send_keys("5")
        self.driver.find_element(By.ID, "servings").send_keys("1")
        # Select first ingredient
        select2_container = self.driver.find_element(By.CLASS_NAME, "select2-container")
        select2_container.click()
        time.sleep(0.5)  # Wait for dropdown to open
        first_option = self.driver.find_element(By.CLASS_NAME, "select2-results__option")
        first_option.click()
        # Add quantity
        self.driver.find_element(By.NAME, "quantity").send_keys("1")
        # Add instruction
        self.driver.find_element(By.NAME, "instructions").send_keys("Mix all ingredients")
        # Select 'private' privacy
        self.driver.find_element(By.CSS_SELECTOR, "input[name='privacy'][value='private']").click()
        # Submit form using JavaScript
        self.driver.execute_script("document.getElementById('recipeForm').submit();")
        time.sleep(2)  # Give more time for the redirect
        # Extract recipe ID from URL
        url = self.driver.current_url
        self.assertIn("/recipe?id=", url)
        recipe_id = url.split("id=")[1]
        # Log out
        self.driver.find_element(By.LINK_TEXT, "Log Out").click()
        time.sleep(1)
        # Login as another seeded user
        self.driver.get(localHost + "login")
        self.driver.find_element(By.NAME, "email").send_keys("test2@email.com")
        self.driver.find_element(By.NAME, "password").send_keys("2")
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(1)  # Wait for login redirect
        # Now try to view the private recipe
        self.driver.get(f"{localHost}recipe?id={recipe_id}")
        time.sleep(1)
        # Should be redirected to homepage
        self.assertEqual(self.driver.current_url, localHost)

if __name__ == "__main__":
    unittest.main(verbosity=2)
