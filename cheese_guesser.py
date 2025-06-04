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
        self.setup_driver()
        
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
            
            self.driver = webdriver.Chrome(options=options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
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
        try:
            # Load the page
            self.driver.get(self.url)
            
            # Wait for the form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "input_1"))
            )
            
            # Fill in the form
            # Name
            name_field = self.driver.find_element(By.NAME, "input_1")
            name_field.send_keys(self.generate_random_name())
            
            # Phone
            phone_field = self.driver.find_element(By.NAME, "input_2")
            phone_field.send_keys(self.generate_random_phone())
            
            # Email (using fixed address)
            email_field = self.driver.find_element(By.NAME, "input_3")
            email_field.send_keys(self.email)
            
            # Weight
            weight_field = self.driver.find_element(By.NAME, "input_4")
            weight_field.send_keys(str(weight))
            
            # Submit the form
            submit_button = self.driver.find_element(By.CLASS_NAME, "gform_submit_button")
            submit_button.click()
            
            # Wait for submission
            time.sleep(2)
            
            logger.info(f"Submitted form with weight: {weight}g")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False

    def run(self, start_weight=7000, end_weight=12000, num_submissions=5000):
        """Run the cheese weight guessing script"""
        try:
            logger.info(f"Starting cheese weight guessing script")
            logger.info(f"Range: {start_weight}g to {end_weight}g")
            logger.info(f"Number of submissions: {num_submissions}")
            logger.info(f"Using email: {self.email}")
            
            successful_submissions = 0
            
            for i in range(num_submissions):
                # Generate a random weight within the range
                weight = random.randint(start_weight, end_weight)
                
                if self.submit_form(weight):
                    successful_submissions += 1
                
                # Add random delay between submissions
                time.sleep(random.uniform(2, 4))
                
                # Log progress
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: {i + 1}/{num_submissions} submissions completed")
            
            logger.info(f"Completed {successful_submissions} successful submissions")
            
        finally:
            self.driver.quit()

if __name__ == "__main__":
    guesser = CheeseGuesser()
    guesser.run() 