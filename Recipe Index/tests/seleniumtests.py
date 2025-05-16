# tests/seleniumtests.py

import os
import sys
import time
import multiprocessing
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

        # Start Flask dev server
        cls.server = multiprocessing.Process(
            target=flask_app.run, kwargs={"use_reloader": False}
        )
        cls.server.daemon = True
        cls.server.start()
        time.sleep(1)

        # Launch headless Chrome
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        cls.driver = webdriver.Chrome(options=opts)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.server.terminate()
        db.drop_all()
        cls.ctx.pop()

    def test_seeded_user_login_flow(self):
        # Seeded user (Test User 1) should log in successfully
        self.driver.get(localHost + "login")
        self.driver.find_element(By.NAME, "email").send_keys("test1@email.com")
        self.driver.find_element(By.NAME, "password").send_keys("1")
        self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        # Redirects to /profile
        self.assertTrue(self.driver.current_url.endswith("/profile"))

    def test_create_and_view_recipe(self):
        # Log in
        self.test_seeded_user_login_flow()
        # Go to Create page
        self.driver.find_element(By.LINK_TEXT, "Create!").click()
        # Fill form
        title = f"Selenium Recipe {int(time.time())}"
        self.driver.find_element(By.ID, "title").send_keys(title)
        self.driver.find_element(By.ID, "description").send_keys("A delicious test dish.")
        self.driver.find_element(By.ID, "cook_time").send_keys("15")
        self.driver.find_element(By.ID, "servings").send_keys("2")
        # Upload an image
        img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "image.jpeg"))
        self.driver.find_element(By.ID, "images").send_keys(img_path)
        # Submit
        self.driver.find_element(By.CLASS_NAME, "submit-btn").click()
        time.sleep(1)
        # View page URL contains recipe id
        self.assertIn("/recipe?id=", self.driver.current_url)
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
        self.driver.find_element(By.LINK_TEXT, "Create!").click()
        self.driver.find_element(By.ID, "title").send_keys("Private Dish")
        self.driver.find_element(By.ID, "cook_time").send_keys("5")
        self.driver.find_element(By.ID, "servings").send_keys("1")
        # Select 'private' privacy
        self.driver.find_element(By.CSS_SELECTOR, "input[name='privacy'][value='private']").click()
        self.driver.find_element(By.CLASS_NAME, "submit-btn").click()
        time.sleep(1)
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
        # Attempt to view the private recipe
        self.driver.get(f"{localHost}recipe?id={recipe_id}")
        time.sleep(1)
        # Should be redirected to homepage
        self.assertEqual(self.driver.current_url, localHost)

if __name__ == "__main__":
    unittest.main(verbosity=2)
