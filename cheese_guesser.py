import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CheeseGuesser:
    def __init__(self):
        """Initialize the Cheese Guesser"""
        self.url = "https://www.gloudemans.nl/kaaswiel/?gf_protect_submission=1"
        self.email = "sharnevesht@gmail.com"  # Fixed email address
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        try:
            options = Options()
            
            # Add arguments to make browser less detectable
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Add user agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            
            # Add experimental options
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            return driver
            
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            raise

    def generate_random_name(self):
        """Generate a random name for the form"""
        first_names = ["Jan", "Piet", "Klaas", "Henk", "Peter", "Hans", "Mark", "Tom", "Paul", "Rob"]
        last_names = ["Jansen", "de Vries", "Bakker", "Visser", "Smit", "Meijer", "Mulder", "de Boer", "Dijkstra", "Vos"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def generate_random_phone(self):
        """Generate a random Dutch phone number"""
        return f"06{random.randint(10000000, 99999999)}"

    def submit_form(self, weight):
        """Submit the form with the given weight"""
        driver = None
        try:
            # Create new driver instance for each submission
            driver = self.setup_driver()
            
            # Load the page
            driver.get(self.url)
            
            # Wait for the form to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "input_9_1"))
            )
            
            # Fill in the form
            # Name
            name_field = driver.find_element(By.ID, "input_9_1")
            name_field.send_keys(self.generate_random_name())
            
            # Phone
            phone_field = driver.find_element(By.ID, "input_9_3")
            phone_field.send_keys(self.generate_random_phone())
            
            # Email
            email_field = driver.find_element(By.ID, "input_9_4")
            email_field.send_keys(self.email)
            
            # Weight (in textarea)
            weight_field = driver.find_element(By.ID, "input_9_5")
            weight_field.send_keys(str(weight))
            
            # Find submit button
            submit_button = driver.find_element(By.ID, "gform_submit_button_9")
            
            # Scroll to the button
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)  # Wait for scroll to complete
            
            # Try multiple methods to click the button
            try:
                # Method 1: JavaScript click
                driver.execute_script("arguments[0].click();", submit_button)
            except:
                try:
                    # Method 2: Wait for button to be clickable and click
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "gform_submit_button_9"))
                    )
                    submit_button.click()
                except:
                    # Method 3: Move to element and click
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(submit_button).click().perform()
            
            # Wait for submission
            time.sleep(2)
            
            logger.info(f"Submitted form with weight: {weight}g")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False
        finally:
            if driver:
                driver.quit()

    def run(self, start_weight=7000, end_weight=12000, step=100):
        """Run the cheese weight guessing script with systematic weight increments"""
        try:
            logger.info(f"Starting cheese weight guessing script")
            logger.info(f"Range: {start_weight}g to {end_weight}g")
            logger.info(f"Step size: {step}g")
            logger.info(f"Using email: {self.email}")
            
            successful_submissions = 0
            total_attempts = 0
            
            # Generate list of weights to try
            weights = range(start_weight, end_weight + 1, step)
            total_weights = len(weights)
            
            for i, weight in enumerate(weights, 1):
                total_attempts += 1
                
                if self.submit_form(weight):
                    successful_submissions += 1
                
                # Add random delay between submissions
                time.sleep(random.uniform(2, 4))
                
                # Log progress
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{total_weights} weights tried")
                    logger.info(f"Successful submissions: {successful_submissions}/{total_attempts}")
            
            logger.info(f"Completed {successful_submissions} successful submissions out of {total_attempts} attempts")
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")

if __name__ == "__main__":
    guesser = CheeseGuesser()
    # Try weights from 7000g to 12000g in steps of 100g
    guesser.run(start_weight=7000, end_weight=12000, step=1) 