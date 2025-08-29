"""
Main application logic for the project.
"""

from .chrome_driver import ChromeDriverManager
from .youtube_automation import YouTubeAutomation
from .utils import FileHandler
from .config import Config


class MainApplication:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        self.config = Config()
        self.chrome_manager = ChromeDriverManager()
        self.file_handler = FileHandler()
        
    def run_youtube_demo(self):
        """Run the YouTube automation demo."""
        print(f"\n=== {self.config.PROJECT_NAME} v{self.config.VERSION} ===")
        search_term = self.config.DEFAULT_SEARCH_TERM
        print(f"Searching YouTube for: '{search_term}'")
        
        try:
            with self.chrome_manager.managed_driver(keep_open=False) as driver:
                if not driver:
                    return
                
                # Create YouTube automation instance
                youtube = YouTubeAutomation(driver)
                
                # Store search term for saving results
                self._last_search_term = search_term
                
                # Run the automation with user search
                video_titles = youtube.search_tech_news(search_term)
                
                # Save results to file
                if video_titles:
                    self._save_results(video_titles)
                
                # Wait for user interaction
                input("\n[INFO] Browse the results and press Enter when done...")
                
                # Wait for user to finish browsing
                input("\n[INFO] Press Enter to close Chrome and exit...")
                # Chrome will be closed by the context manager (default behavior)
                
        except KeyboardInterrupt:
            print("\n[INFO] Operation cancelled by user.")
        except Exception as e:
            print(f"\n[ERROR] Application error: {e}")
    
    def _save_results(self, video_titles):
        """Save video titles to a file."""
        try:
            # Save as JSON
            data = {
                "search_term": getattr(self, '_last_search_term', self.config.DEFAULT_SEARCH_TERM),
                "timestamp": self._get_timestamp(),
                "results": video_titles
            }
            
            json_file = self.config.PROJECT_DIR / "results" / "youtube_results.json"
            if self.file_handler.write_json(json_file, data):
                print(f"[INFO] Results saved to: {json_file}")
            
            # Save as text file for easy reading
            text_content = f"YouTube Search Results\n"
            text_content += f"Search Term: {getattr(self, '_last_search_term', self.config.DEFAULT_SEARCH_TERM)}\n"
            text_content += f"Timestamp: {self._get_timestamp()}\n\n"
            
            for i, title in enumerate(video_titles, 1):
                text_content += f"{i}. {title}\n"
            
            text_file = self.config.PROJECT_DIR / "results" / "youtube_results.txt"
            if self.file_handler.write_text(text_file, text_content):
                print(f"[INFO] Results also saved to: {text_file}")
                
        except Exception as e:
            print(f"[ERROR] Failed to save results: {e}")
    
    def _get_timestamp(self):
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def run(self):
        """Main entry point for the application."""
        self.run_youtube_demo()