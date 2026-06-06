#!/usr/bin/env python3
"""Wolf Agent v1.0.0-beta - Command-line entry point"""
import typer
from pathlib import Path
import sys
import asyncio

app = typer.Typer(
    name="wolf",
    help="Wolf Agent - Google Maps SMB Lead Generator",
    add_completion=False
)

def check_dependencies():
    """Check if all dependencies are installed"""
    missing = []
    
    try:
        import playwright
    except ImportError:
        missing.append("playwright")
    
    try:
        import httpx
    except ImportError:
        missing.append("httpx")
    
    try:
        import textual
    except ImportError:
        missing.append("textual")
    
    try:
        import typer
    except ImportError:
        missing.append("typer")
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        print("Then: playwright install chromium")
        sys.exit(1)
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
            except Exception:
                print("Chromium not installed for Playwright")
                print("Run: playwright install chromium")
                sys.exit(1)
    except Exception:
        pass

@app.command()
def start():
    """Start Wolf Agent TUI interface"""
    print("""
    +=======================================+
    |     WOLF AGENT v1.0.0-beta           |
    |     SMB Lead Generator               |
    |     Zero-Cost Edition                |
    +=======================================+
    
    Initializing...
    """)
    
    check_dependencies()
    
    data_dir = Path("wolf/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    config_dir = Path("wolf/config")
    if not config_dir.exists():
        print("Config directory not found!")
        print("Make sure you are running from the wolf-agent directory")
        sys.exit(1)
    
    from .tui.interface import WolfApp
    
    app_instance = WolfApp()
    app_instance.run()

@app.command()
def version():
    """Show Wolf Agent version"""
    from . import __version__
    print(f"Wolf Agent v{__version__}")
    print("Zero-Cost Edition")

@app.command()
def install():
    """Install all dependencies"""
    import subprocess
    import sys
    
    print("Installing Wolf Agent dependencies...")
    
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    
    print("Installation complete!")
    print("You can now run: wolf start")

def main():
    """Main entry point"""
    app()

if __name__ == "__main__":
    main()
