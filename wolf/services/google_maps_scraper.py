import asyncio
import random
import json
from typing import List, Optional
from pathlib import Path
import re
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright

class GoogleMapsScraper:
    """Core Google Maps scraping using Playwright (free)"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.debug_mode = True
        self.data_dir = Path("wolf/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize_browser(self):
        """Launch browser with anti-detection measures"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=not self.debug_mode,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized',
                f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Chicago',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation']
        )
        
        self.page = await self.context.new_page()
        
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
            );
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
    
    async def search_businesses(self, niche: str, city: str, max_results: int = 20) -> List[dict]:
        """Search Google Maps for businesses"""
        if not self.page:
            await self.initialize_browser()
        
        businesses = []
        search_query = f"{niche} in {city}"
        encoded_query = search_query.replace(" ", "+")
        
        maps_url = f"https://www.google.com/maps/search/{encoded_query}"
        
        try:
            await self.page.goto(maps_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(3, 5))
            
            if await self._check_captcha():
                print("\nCAPTCHA detected! Please solve it manually in the browser window...")
                print("The browser will remain open for 2 minutes.")
                await asyncio.sleep(120)
                if await self._check_captcha():
                    print("CAPTCHA still present. Please try again later.")
                    return []
            
            await self._scroll_results()
            businesses = await self._extract_businesses(max_results)
            
        except Exception as e:
            print(f"Error during search: {e}")
        
        return businesses
    
    async def _check_captcha(self) -> bool:
        """Check if CAPTCHA is present"""
        try:
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'form[action*="recaptcha"]',
                'div.g-recaptcha',
                '#captcha-form',
                '[aria-label="reCAPTCHA"]'
            ]
            
            for selector in captcha_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            return False
        except Exception:
            return False
    
    async def _scroll_results(self):
        """Scroll through results to load more"""
        try:
            results_panel = await self.page.query_selector('[role="feed"]')
            if not results_panel:
                results_panel = await self.page.query_selector('div[aria-label*="Results"]')
            
            if results_panel:
                for _ in range(5):
                    await results_panel.evaluate('el => el.scrollBy(0, 500)')
                    await asyncio.sleep(random.uniform(2, 4))
            else:
                for _ in range(5):
                    await self.page.evaluate('window.scrollBy(0, 500)')
                    await asyncio.sleep(random.uniform(2, 4))
                    
        except Exception as e:
            print(f"Scrolling error: {e}")
    
    async def _extract_businesses(self, max_results: int) -> List[dict]:
        """Extract business data from current page"""
        businesses = []
        
        try:
            await self.page.wait_for_selector('[role="article"]', timeout=10000)
            listings = await self.page.query_selector_all('[role="article"]')
            
            for listing in listings[:max_results * 2]:
                try:
                    name_elem = await listing.query_selector('div.fontHeadlineSmall')
                    if not name_elem:
                        name_elem = await listing.query_selector('[aria-label]')
                    
                    name = await name_elem.inner_text() if name_elem else "Unknown"
                    
                    website = None
                    website_elem = await listing.query_selector('a[data-value*="Website"]')
                    if not website_elem:
                        website_elem = await listing.query_selector('a[href*="http"]:not([href*="google.com"])')
                    
                    if website_elem:
                        website = await website_elem.get_attribute('href')
                    
                    address_elem = await listing.query_selector('div.fontBodyMedium span')
                    address = await address_elem.inner_text() if address_elem else None
                    
                    phone_elem = await listing.query_selector('[data-tooltip*="Phone"]')
                    phone = await phone_elem.get_attribute('data-tooltip') if phone_elem else None
                    
                    rating_elem = await listing.query_selector('span[aria-hidden="true"]')
                    rating = await rating_elem.inner_text() if rating_elem else None
                    
                    if not website:
                        business_data = {
                            "name": name,
                            "address": address,
                            "phone": phone,
                            "website": website,
                            "rating": rating,
                            "place_id": f"https://www.google.com/maps/place/?q=place_id:{name.replace(' ', '+')}",
                            "discovered_at": datetime.now().isoformat()
                        }
                        businesses.append(business_data)
                    
                    if len(businesses) >= max_results:
                        break
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Extraction error: {e}")
        
        return businesses
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception:
            pass
