import httpx
import asyncio
from typing import Optional, Tuple
from urllib.parse import urlparse
import re

class WebsiteVerifier:
    """Service 2: Verify if a business actually has a website"""
    
    def __init__(self):
        self.timeout = 10.0
        self.max_redirects = 5
        self.common_patterns = [
            lambda name: name.lower().replace(" ", ""),
            lambda name: name.lower().replace(" ", "-"),
            lambda name: name.lower().replace(" ", "").replace("'", ""),
            lambda name: re.sub(r'[^a-z0-9]', '', name.lower()),
        ]
        self.common_tlds = [".com", ".net", ".org", ".co", ".biz", ".io"]
    
    async def check_website_exists(self, url: str) -> Tuple[bool, Optional[str]]:
        """Check if a website exists and is accessible"""
        if not url or url in ["none", "null", "undefined", ""]:
            return False, None
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, max_redirects=self.max_redirects) as client:
                response = await client.head(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code < 400:
                    return True, str(response.url)
                elif response.status_code == 403:
                    response = await client.get(url)
                    return response.status_code < 400, str(response.url)
                else:
                    return False, None
                    
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout):
            if url.startswith('https://'):
                try:
                    http_url = url.replace('https://', 'http://', 1)
                    async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                        response = await client.head(http_url)
                        return response.status_code < 400, str(response.url)
                except Exception:
                    return False, None
            return False, None
        except Exception:
            return False, None
    
    async def discover_website(self, business_name: str, city: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Try to discover a business website through common patterns"""
        name_clean = business_name.lower().strip()
        
        for pattern in self.common_patterns:
            domain_base = pattern(name_clean)
            for tld in self.common_tlds:
                url = f"https://www.{domain_base}{tld}"
                exists, final_url = await self.check_website_exists(url)
                if exists:
                    return True, final_url
        
        return False, None
    
    async def verify_no_website(self, business_name: str, raw_website: Optional[str] = None, city: Optional[str] = None) -> dict:
        """Comprehensive check - verify business has no website"""
        result = {
            "has_website": False,
            "website_url": None,
            "verified": False,
            "verification_method": None
        }
        
        if raw_website and raw_website not in ["", "none", "null", "undefined"]:
            exists, final_url = await self.check_website_exists(raw_website)
            if exists:
                result["has_website"] = True
                result["website_url"] = final_url
                result["verified"] = True
                result["verification_method"] = "google_maps_provided"
                return result
        
        exists, url = await self.discover_website(business_name, city)
        if exists:
            result["has_website"] = True
            result["website_url"] = url
            result["verified"] = True
            result["verification_method"] = "pattern_discovery"
            return result
        
        result["verified"] = True
        result["verification_method"] = "no_website_found"
        
        return result
