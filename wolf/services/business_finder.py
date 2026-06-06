import asyncio
import random
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

class BusinessFinder:
    \"\"\"Service 1: Find businesses without websites on Google Maps\"\"\"
    
    def __init__(self):
        self.data_dir = Path("wolf/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.leads_file = self.data_dir / "leads.json"
        self._initialize_leads_file()
    
    def _initialize_leads_file(self):
        \"\"\"Initialize leads file if it doesn't exist\"\"\"
        if not self.leads_file.exists():
            with open(self.leads_file, 'w') as f:
                json.dump({"leads": []}, f, indent=2)
    
    def is_duplicate(self, business_name: str, phone: Optional[str] = None) -> bool:
        \"\"\"Check if business already exists in leads\"\"\"
        try:
            with open(self.leads_file, 'r') as f:
                data = json.load(f)
            
            for lead in data.get("leads", []):
                # Check by name (case insensitive)
                if lead.get("name", "").lower() == business_name.lower():
                    return True
                # Check by phone if available
                if phone and lead.get("phone") == phone:
                    return True
            return False
        except Exception:
            return False
    
    def save_leads(self, new_leads: List[dict]):
        \"\"\"Save new leads to file, avoiding duplicates\"\"\"
        try:
            with open(self.leads_file, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {"leads": []}
        
        existing_names = {lead.get("name", "").lower() for lead in data["leads"]}
        existing_phones = {lead.get("phone") for lead in data["leads"] if lead.get("phone")}
        
        for lead in new_leads:
            name_key = lead.get("name", "").lower()
            phone = lead.get("phone")
            
            if name_key not in existing_names and (not phone or phone not in existing_phones):
                data["leads"].append(lead)
                existing_names.add(name_key)
                if phone:
                    existing_phones.add(phone)
        
        with open(self.leads_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_all_leads(self) -> List[dict]:
        \"\"\"Get all saved leads\"\"\"
        try:
            with open(self.leads_file, 'r') as f:
                data = json.load(f)
            return data.get("leads", [])
        except Exception:
            return []
    
    def get_lead_count(self) -> int:
        \"\"\"Get total number of leads\"\"\"
        return len(self.get_all_leads())
    
    def extract_business_data(self, raw_data: dict) -> Optional[dict]:
        \"\"\"Extract and normalize business data from raw Google Maps data\"\"\"
        try:
            business = {
                "name": raw_data.get("title", ""),
                "address": raw_data.get("address", ""),
                "phone": raw_data.get("phone", ""),
                "google_maps_url": raw_data.get("place_id", ""),
                "website_found": False,
                "website_url": None,
                "verified_no_website": False,
                "rating": raw_data.get("rating", None),
                "reviews_count": raw_data.get("reviews", None),
                "category": raw_data.get("type", ""),
                "discovered_at": datetime.now().isoformat(),
                "source": "google_maps"
            }
            
            # Check if website exists in raw data
            if raw_data.get("website"):
                business["website_found"] = True
                business["website_url"] = raw_data.get("website")
            
            return business
        except Exception:
            return None
