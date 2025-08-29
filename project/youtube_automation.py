"""
YouTube automation functionality.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config import Config


class YouTubeAutomation:
    """Handles YouTube automation tasks."""
    
    def __init__(self, driver):
        self.driver = driver
        self.config = Config()
        self.wait = WebDriverWait(driver, self.config.ELEMENT_WAIT_TIMEOUT)
    
    def navigate_to_youtube(self):
        """Navigate to YouTube homepage."""
        print("[INFO] Navigating to YouTube...")
        self.driver.get(self.config.YOUTUBE_URL)
        
        # Wait for page to load
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("[SUCCESS] YouTube loaded successfully")
    
    def search(self, search_term):
        """Search for content on YouTube."""
        try:
            print(f"[INFO] Searching for: {search_term}")
            
            # Find and interact with search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )
            
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load
            self.wait.until(
                EC.presence_of_element_located((By.ID, "contents"))
            )
            
            print(f"[SUCCESS] Search completed for: {search_term}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return False
    
    def get_video_titles(self, max_results=10):
        """Get video titles from search results."""
        try:
            # Wait for video elements to load
            video_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a#video-title"))
            )
            
            titles = []
            for element in video_elements[:max_results]:
                title = element.get_attribute("title")
                if title:
                    titles.append(title)
            
            print(f"[INFO] Found {len(titles)} video titles")
            return titles
            
        except Exception as e:
            print(f"[ERROR] Failed to get video titles: {e}")
            return []
    
    def search_tech_news(self, search_term=None):
        """Search for content on YouTube."""
        if search_term is None:
            search_term = self.config.DEFAULT_SEARCH_TERM
            
        self.navigate_to_youtube()
        success = self.search(search_term)
        
        if success:
            titles = self.get_video_titles()
            if titles:
                print(f"\n=== Search Results for '{search_term}' ===")
                for i, title in enumerate(titles, 1):
                    print(f"{i}. {title}")
                print("=" * 40)
            return titles
        return []