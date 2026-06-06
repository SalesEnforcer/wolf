from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, Label, ProgressBar, Select, Input
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message
from typing import Optional
import asyncio
from datetime import datetime

from ..services.rate_limiter import HumanBehavior
from ..services.business_finder import BusinessFinder
from ..services.website_verifier import WebsiteVerifier
from ..services.google_maps_scraper import GoogleMapsScraper
from ..config.models import Country, Niche, City

class MainMenu(Screen):
    \"\"\"Main menu screen\"\"\"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🐺 WOLF AGENT v1.0.0-beta", classes="title"),
            Static("SMB Lead Generator - Zero Cost Edition", classes="subtitle"),
            Static("", classes="spacer"),
            Button("A. Assess Current Lead List", variant="primary", id="assess"),
            Button("B. Export Current Lead List", variant="primary", id="export"),
            Button("C. Find New Leads", variant="success", id="find"),
            Button("D. Exit", variant="error", id="exit"),
            classes="menu-container"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "assess":
            self.app.push_screen(AssessScreen())
        elif event.button.id == "export":
            self.app.push_screen(ExportScreen())
        elif event.button.id == "find":
            self.app.push_screen(SearchConfigScreen())
        elif event.button.id == "exit":
            self.app.exit()

class AssessScreen(Screen):
    \"\"\"Screen to assess current leads\"\"\"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Static("📊 Current Lead Assessment", classes="title"),
            Static(id="stats"),
            Static(id="recent_leads"),
            classes="assess-container"
        )
        yield Footer()
        yield Button("Back to Main Menu", variant="primary", id="back")
    
    def on_mount(self) -> None:
        finder = BusinessFinder()
        leads = finder.get_all_leads()
        
        stats_widget = self.query_one("#stats", Static)
        stats_text = f"""
Total Leads: {len(leads)}
Verified No Website: {sum(1 for l in leads if l.get('verified_no_website'))}
Awaiting Verification: {sum(1 for l in leads if not l.get('verified_no_website'))}

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        stats_widget.update(stats_text)
        
        # Show recent leads
        recent = sorted(leads, key=lambda x: x.get('discovered_at', ''), reverse=True)[:10]
        recent_widget = self.query_one("#recent_leads", Static)
        recent_text = "Recent Leads:\n" + "="*50 + "\n"
        for lead in recent:
            recent_text += f"• {lead.get('name', 'Unknown')} - {lead.get('city', 'N/A')}\n"
        recent_widget.update(recent_text)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

class ExportScreen(Screen):
    \"\"\"Screen to export leads\"\"\"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("💾 Export Leads", classes="title"),
            Static("Export format:", classes="label"),
            Horizontal(
                Button("JSON", variant="primary", id="export_json"),
                Button("CSV", variant="primary", id="export_csv"),
                Button("TXT", variant="primary", id="export_txt"),
            ),
            Static(id="export_status"),
            Button("Back to Main Menu", variant="default", id="back"),
            classes="export-container"
        )
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id in ["export_json", "export_csv", "export_txt"]:
            self.export_leads(event.button.id.replace("export_", ""))
    
    def export_leads(self, format_type: str):
        finder = BusinessFinder()
        leads = finder.get_all_leads()
        
        export_dir = Path("wolf/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wolf_leads_{timestamp}.{format_type}"
        filepath = export_dir / filename
        
        if format_type == "json":
            with open(filepath, 'w') as f:
                json.dump(leads, f, indent=2, default=str)
        elif format_type == "csv":
            import csv
            if leads:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=leads[0].keys())
                    writer.writeheader()
                    writer.writerows(leads)
        elif format_type == "txt":
            with open(filepath, 'w', encoding='utf-8') as f:
                for lead in leads:
                    f.write(f"Name: {lead.get('name', 'N/A')}\n")
                    f.write(f"Phone: {lead.get('phone', 'N/A')}\n")
                    f.write(f"Address: {lead.get('address', 'N/A')}\n")
                    f.write("-" * 50 + "\n")
        
        status = self.query_one("#export_status", Static)
        status.update(f"✅ Exported {len(leads)} leads to {filepath}")

class SearchConfigScreen(Screen):
    \"\"\"Screen to configure search parameters\"\"\"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("🎯 Configure Search", classes="title"),
            Static("Where are we looking?", classes="subtitle"),
            Select(
                [(c.value, c.value) for c in Country],
                prompt="Select Country",
                id="country"
            ),
            Static(id="city_status", classes="status"),
            Select([], prompt="Select City", id="city"),
            Static("What niche?", classes="subtitle"),
            Select([], prompt="Select Niche", id="niche"),
            Static(id="config_status"),
            Horizontal(
                Button("Start Search", variant="success", id="start"),
                Button("Back", variant="default", id="back"),
            ),
            classes="config-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        # Load niches
        try:
            with open("wolf/config/niches.json", 'r') as f:
                niches_data = json.load(f)
            niches = niches_data.get("niches", [])
            niche_select = self.query_one("#niche", Select)
            niche_select.set_options([(n, n) for n in niches])
        except Exception:
            pass
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "country":
            # Load cities for selected country
            try:
                with open("wolf/config/cities.json", 'r') as f:
                    cities_data = json.load(f)
                
                country_name = event.value
                country_enum = next(c for c in Country if c.value == country_name)
                
                filtered_cities = [
                    c for c in cities_data.get("cities", [])
                    if c.get("country") == country_enum.name
                ]
                
                city_select = self.query_one("#city", Select)
                city_select.set_options([
                    (f"{c['name']}, {c.get('state', '')}", c['name'])
                    for c in filtered_cities
                ])
                
                status = self.query_one("#city_status", Static)
                status.update(f"Found {len(filtered_cities)} cities in {country_name}")
            except Exception as e:
                status = self.query_one("#city_status", Static)
                status.update(f"Error loading cities: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "start":
            country = self.query_one("#country", Select).value
            city = self.query_one("#city", Select).value
            niche = self.query_one("#niche", Select).value
            
            if not all([country, city, niche]):
                status = self.query_one("#config_status", Static)
                status.update("❌ Please select all fields")
                return
            
            self.app.push_screen(SearchProgressScreen(country, city, niche))

class SearchProgressScreen(Screen):
    \"\"\"Screen showing search progress\"\"\"
    
    def __init__(self, country: str, city: str, niche: str):
        super().__init__()
        self.country = country
        self.city = city
        self.niche = niche
        self.scraper = None
        self.search_task = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(f"🔍 Searching for {self.niche} in {self.city}", classes="title"),
            ProgressBar(total=20, id="progress"),
            Static(id="progress_text"),
            ScrollableContainer(
                Static(id="log"),
                classes="log-container"
            ),
            Button("Cancel", variant="error", id="cancel", classes="hidden"),
            classes="progress-container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        # Start the search
        self.search_task = asyncio.create_task(self.run_search())
    
    async def run_search(self):
        \"\"\"Execute the search process\"\"\"
        log = self.query_one("#log", Static)
        progress = self.query_one("#progress", ProgressBar)
        progress_text = self.query_one("#progress_text", Static)
        
        try:
            # Initialize services
            behavior = HumanBehavior()
            
            # Check cooldown
            can_run, message = behavior.can_run()
            if not can_run:
                log.update(f"❌ {message}")
                return
            
            log.update("🚀 Initializing Wolf Agent...\n")
            
            # Initialize scraper
            self.scraper = GoogleMapsScraper()
            log.update(f"{log.renderable}\n🌐 Launching browser...")
            await self.scraper.initialize_browser()
            
            log.update(f"{log.renderable}\n✅ Browser ready")
            
            # Search for businesses
            log.update(f"{log.renderable}\n🔍 Searching: '{self.niche} in {self.city}'")
            raw_businesses = await self.scraper.search_businesses(
                self.niche, self.city, max_results=30
            )
            
            log.update(f"{log.renderable}\n📊 Found {len(raw_businesses)} businesses without websites")
            
            # Verify websites
            finder = BusinessFinder()
            verifier = WebsiteVerifier()
            verified_leads = []
            
            for i, business in enumerate(raw_businesses[:25]):  # Get extras for filtering
                if len(verified_leads) >= 20:
                    break
                
                # Check for duplicates
                if finder.is_duplicate(business.get("name"), business.get("phone")):
                    log.update(f"{log.renderable}\n⏭️  Skipping duplicate: {business.get('name')}")
                    continue
                
                # Verify no website
                log.update(f"{log.renderable}\n🔍 Verifying: {business.get('name')}")
                
                await behavior.human_delay(1, 3)  # Human-like delay
                
                verification = await verifier.verify_no_website(
                    business.get("name"),
                    business.get("website"),
                    self.city
                )
                
                if not verification["has_website"]:
                    business["verified_no_website"] = True
                    business["city"] = self.city
                    business["niche"] = self.niche
                    business["country"] = self.country
                    verified_leads.append(business)
                    log.update(f"{log.renderable}\n✅ Confirmed no website: {business.get('name')}")
                else:
                    log.update(f"{log.renderable}\n❌ Website found: {business.get('name')}")
                
                # Update progress
                progress.update(progress=len(verified_leads))
                progress_text.update(f"Leads found: {len(verified_leads)}/20")
            
            # Save leads
            if verified_leads:
                finder.save_leads(verified_leads)
                behavior.save_run_state(
                    self.city, self.niche, len(verified_leads),
                    f"{self.niche} in {self.city}"
                )
                
                log.update(f"{log.renderable}\n\n✅ Search complete!")
                log.update(f"{log.renderable}\n📊 Total new leads: {len(verified_leads)}")
                log.update(f"{log.renderable}\n💾 Leads saved to wolf/data/leads.json")
            else:
                log.update(f"{log.renderable}\n\n⚠️  No new leads found")
            
            progress.update(progress=20)
            
        except Exception as e:
            log.update(f"{log.renderable}\n\n❌ Error: {str(e)}")
        finally:
            if self.scraper:
                await self.scraper.close()
            
            # Show done button
            cancel_btn = self.query_one("#cancel", Button)
            cancel_btn.label = "Done"
            cancel_btn.variant = "primary"
            cancel_btn.remove_class("hidden")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            if self.search_task:
                self.search_task.cancel()
            if self.scraper:
                asyncio.create_task(self.scraper.close())
            self.app.pop_screen()

class WolfApp(App):
    \"\"\"Main Wolf Agent Application\"\"\"
    
    CSS = """
    .title {
        text-align: center;
        text-style: bold;
        color: ;
        padding: 1;
    }
    
    .subtitle {
        text-align: center;
        color: -muted;
        padding-bottom: 1;
    }
    
    .menu-container {
        align: center middle;
        height: 100%;
    }
    
    .menu-container Button {
        margin: 1;
        min-width: 40;
    }
    
    .assess-container {
        padding: 2;
        height: auto;
    }
    
    .export-container {
        padding: 2;
        align: center middle;
    }
    
    .config-container {
        padding: 2;
        align: center middle;
    }
    
    .progress-container {
        padding: 2;
    }
    
    .log-container {
        height: 20;
        border: solid ;
        margin-top: 2;
    }
    
    .status {
        color: -muted;
        text-align: center;
    }
    
    .spacer {
        height: 1;
    }
    
    Button {
        margin: 1;
    }
    
    Select {
        margin: 1;
        min-width: 30;
    }
    
    .hidden {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle dark mode"),
    ]
    
    def on_mount(self) -> None:
        self.push_screen(MainMenu())
        self.title = "🐺 Wolf Agent v1.0.0-beta"
        self.sub_title = "SMB Lead Generator"
    
    def action_quit(self) -> None:
        self.exit()
    
    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
