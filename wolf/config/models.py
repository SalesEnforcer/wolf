from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Country(str, Enum):
    US = "United States"
    UK = "United Kingdom"
    CA = "Canada"
    AU = "Australia"
    NG = "Nigeria"
    ZA = "South Africa"
    KE = "Kenya"
    GH = "Ghana"

class Niche(str, Enum):
    PLUMBERS = "plumbers"
    ELECTRICIANS = "electricians"
    DENTISTS = "dentists"
    LAWYERS = "lawyers"
    RESTAURANTS = "restaurants"
    BARBERS = "barbers"
    HAIR_SALONS = "hair salons"
    MECHANICS = "mechanics"
    CLEANING_SERVICES = "cleaning services"
    LANDSCAPERS = "landscapers"
    PAINTERS = "painters"
    ROOFERS = "roofers"
    HVAC = "hvac contractors"
    PEST_CONTROL = "pest control"
    MOVERS = "movers"
    PHOTOGRAPHERS = "photographers"
    BAKERS = "bakers"
    TAILORS = "tailors"
    CARPENTERS = "carpenters"
    TUTORS = "tutors"

class City(BaseModel):
    name: str
    state: Optional[str] = None
    country: Country

class Business(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    google_maps_url: str
    website_found: bool = False
    website_url: Optional[str] = None
    verified_no_website: bool = False
    niche: str
    city: str
    country: str
    discovered_at: datetime = Field(default_factory=datetime.now)
    source: str = "google_maps"

class SearchConfig(BaseModel):
    city: City
    niche: Niche
    max_leads: int = 20

class RunRecord(BaseModel):
    last_run: datetime
    city: str
    niche: str
    leads_collected: int
    search_term: str

class AgentState(BaseModel):
    last_run: Optional[RunRecord] = None
    total_leads_collected: int = 0
    cooldown_hours: int = 8
