import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Optional
import json
from pathlib import Path

class HumanBehavior:
    \"\"\"Service 3: Human-like search behavior with rate limiting\"\"\"
    
    def __init__(self):
        self.base_delay = (3.0, 8.0)  # Base delay range between actions
        self.reading_pause = (15.0, 30.0)  # Simulating reading results
        self.scroll_pause = (2.0, 5.0)  # Pause between scrolls
        self.typing_delay = (0.05, 0.15)  # Delay per character when typing
        self.session_start_time = None
        self.actions_count = 0
        self.data_dir = Path("wolf/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def human_delay(self, min_seconds: float = None, max_seconds: float = None):
        \"\"\"Random delay to simulate human behavior\"\"\"
        if min_seconds is None:
            min_seconds = self.base_delay[0]
        if max_seconds is None:
            max_seconds = self.base_delay[1]
        
        delay = random.uniform(min_seconds, max_seconds)
        # Add jitter (±20%)
        jitter = delay * random.uniform(-0.2, 0.2)
        final_delay = max(0.5, delay + jitter)
        
        await asyncio.sleep(final_delay)
        self.actions_count += 1
    
    async def simulate_reading(self):
        \"\"\"Simulate reading search results\"\"\"
        delay = random.uniform(self.reading_pause[0], self.reading_pause[1])
        await asyncio.sleep(delay)
    
    async def simulate_scroll_pause(self):
        \"\"\"Pause between scrolling actions\"\"\"
        delay = random.uniform(self.scroll_pause[0], self.scroll_pause[1])
        await asyncio.sleep(delay)
    
    async def simulate_typing(self, text: str):
        \"\"\"Simulate human typing speed\"\"\"
        for char in text:
            await asyncio.sleep(random.uniform(self.typing_delay[0], self.typing_delay[1]))
    
    def can_run(self, cooldown_hours: int = 8) -> tuple[bool, Optional[str]]:
        \"\"\"Check if enough time has passed since last run\"\"\"
        state_file = self.data_dir / "agent_state.json"
        
        if not state_file.exists():
            return True, None
        
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            if state.get('last_run'):
                last_run = datetime.fromisoformat(state['last_run']['last_run'])
                cooldown_end = last_run + timedelta(hours=cooldown_hours)
                
                if datetime.now() < cooldown_end:
                    remaining = cooldown_end - datetime.now()
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    return False, f"Cooldown active. {hours}h {minutes}m remaining"
        except Exception:
            return True, None
        
        return True, None
    
    def save_run_state(self, city: str, niche: str, leads_count: int, search_term: str):
        \"\"\"Save run state after completion\"\"\"
        state_file = self.data_dir / "agent_state.json"
        
        state = {
            "last_run": {
                "last_run": datetime.now().isoformat(),
                "city": city,
                "niche": niche,
                "leads_collected": leads_count,
                "search_term": search_term
            },
            "total_leads_collected": self.get_total_leads() + leads_count,
            "cooldown_hours": 8
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_total_leads(self) -> int:
        \"\"\"Get total leads collected\"\"\"
        state_file = self.data_dir / "agent_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('total_leads_collected', 0)
            except Exception:
                return 0
        return 0
    
    def get_last_run_info(self) -> Optional[dict]:
        \"\"\"Get information about last run\"\"\"
        state_file = self.data_dir / "agent_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    return state.get('last_run')
            except Exception:
                return None
        return None
