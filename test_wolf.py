#!/usr/bin/env python3
"""Quick test to verify Wolf Agent setup"""
import sys
from pathlib import Path

def test_imports():
    """Test all imports"""
    tests = []
    
    try:
        from wolf.config.models import Country, Niche, City
        tests.append(("Config models", True))
    except Exception as e:
        tests.append((f"Config models: {e}", False))
    
    try:
        from wolf.services.business_finder import BusinessFinder
        tests.append(("Business Finder", True))
    except Exception as e:
        tests.append((f"Business Finder: {e}", False))
    
    try:
        from wolf.services.website_verifier import WebsiteVerifier
        tests.append(("Website Verifier", True))
    except Exception as e:
        tests.append((f"Website Verifier: {e}", False))
    
    try:
        from wolf.services.rate_limiter import HumanBehavior
        tests.append(("Rate Limiter", True))
    except Exception as e:
        tests.append((f"Rate Limiter: {e}", False))
    
    try:
        from wolf.services.google_maps_scraper import GoogleMapsScraper
        tests.append(("Google Maps Scraper", True))
    except Exception as e:
        tests.append((f"Google Maps Scraper: {e}", False))
    
    return tests

def test_directories():
    """Test directory structure"""
    tests = []
    
    dirs = [
        "wolf/config",
        "wolf/data",
        "wolf/services",
        "wolf/tui",
        "wolf/exports"
    ]
    
    for d in dirs:
        if Path(d).exists():
            tests.append((f"Directory: {d}", True))
        else:
            tests.append((f"Directory missing: {d}", False))
            Path(d).mkdir(parents=True, exist_ok=True)
            tests.append((f"Created: {d}", True))
    
    return tests

def test_files():
    """Test required files"""
    tests = []
    
    files = [
        "wolf/config/cities.json",
        "wolf/config/niches.json",
        "wolf/data/leads.json",
        "wolf/data/agent_state.json"
    ]
    
    for f in files:
        if Path(f).exists():
            tests.append((f"File: {f}", True))
        else:
            tests.append((f"File missing: {f}", False))
            if f.endswith('.json'):
                Path(f).parent.mkdir(parents=True, exist_ok=True)
                if 'leads' in f:
                    Path(f).write_text('{"leads": []}')
                elif 'state' in f:
                    Path(f).write_text('{}')
                else:
                    Path(f).write_text('[]')
                tests.append((f"Created default: {f}", True))
    
    return tests

if __name__ == "__main__":
    print("Wolf Agent - Setup Test")
    print("=" * 50)
    
    print("\nTesting directories...")
    dir_tests = test_directories()
    for msg, success in dir_tests:
        print(f"  {'OK' if success else 'XX'} {msg}")
    
    print("\nTesting files...")
    file_tests = test_files()
    for msg, success in file_tests:
        print(f"  {'OK' if success else 'XX'} {msg}")
    
    print("\nTesting imports...")
    import_tests = test_imports()
    for msg, success in import_tests:
        print(f"  {'OK' if success else 'XX'} {msg}")
    
    print("\n" + "=" * 50)
    all_tests = dir_tests + file_tests + import_tests
    passed = sum(1 for _, success in all_tests if success)
    total = len(all_tests)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nWolf Agent is ready!")
        print("Run 'wolf start' to begin")
    else:
        print(f"\n{total - passed} issues found")
        print("Some issues were auto-fixed")
        print("Run this test again to verify")
