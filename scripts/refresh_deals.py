#!/usr/bin/env python3
"""
ClawSavings Deal Refresh Script

Refreshes the deal layer in discounts.json by scraping current voucher prices
from various sources.

Usage:
    python refresh_deals.py --source poalim_wonder
    python refresh_deals.py --source htzone_club --category supermarkets
    python refresh_deals.py --all

Requirements:
    - playwright (pip install playwright && playwright install)
    - Login credentials for protected sources (htzone, poalim)

Note: This is a stub implementation. Full browser automation requires:
    1. Stored credentials (via env vars or secure vault)
    2. Playwright browser automation
    3. Page-specific selectors for each source
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# KB path - adjust if running from different location
KB_PATH = Path(__file__).parent.parent / "discounts.json"


def load_kb():
    """Load the knowledge base."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_kb(kb):
    """Save the knowledge base."""
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved KB to {KB_PATH}")


def refresh_poalim_wonder(kb, category=None):
    """
    Refresh Poalim Wonder voucher deals.
    
    Stub implementation - full version would:
    1. Login to bankhapoalim.co.il
    2. Navigate to Poalim Wonder section
    3. Scrape current voucher prices
    4. Update kb['categories'][cat]['sources']['poalim_wonder']['deals']
    """
    print("🔄 Refreshing Poalim Wonder deals...")
    print("   ⚠️  Stub implementation - manual update required")
    print()
    print("   To update manually:")
    print("   1. Login to https://www.bankhapoalim.co.il/he/Poalim-Wonder")
    print("   2. Check current voucher prices")
    print("   3. Update discounts.json with new prices")
    print("   4. Set cached_at to today's date")
    print()
    
    # In full implementation, would look something like:
    # 
    # from playwright.sync_api import sync_playwright
    # 
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
    #     page = browser.new_page()
    #     page.goto("https://www.bankhapoalim.co.il/he/Poalim-Wonder")
    #     # Login flow...
    #     # Scrape voucher prices...
    #     # Update KB...
    
    return False  # Indicates no actual update was made


def refresh_htzone_club(kb, category=None):
    """
    Refresh HiTech Zone club voucher deals.
    
    Stub implementation - full version would:
    1. Login to htzone.co.il
    2. Navigate to voucher sections
    3. Scrape current voucher prices
    4. Update kb['categories'][cat]['sources']['htzone_club']['deals']
    """
    print("🔄 Refreshing HiTech Zone Club deals...")
    print("   ⚠️  Stub implementation - manual update required")
    print()
    print("   To update manually:")
    print("   1. Login to https://www.htzone.co.il")
    print("   2. Navigate to voucher section for desired category")
    print("   3. Update discounts.json with new prices")
    print("   4. Set cached_at to today's date")
    print()
    
    # Category-specific URLs:
    urls = {
        "supermarkets": "https://www.htzone.co.il/sale/1147",
        "restaurants": "https://www.htzone.co.il/sale/1148",
        "entertainment": "https://www.htzone.co.il/sale/1149",
        "fashion": "https://www.htzone.co.il/sale/1150",
        "pharma": "https://www.htzone.co.il/sale/1152",
        "electronics": "https://www.htzone.co.il/sale/1153",
        "home_renovation": "https://www.htzone.co.il/sale/1154",
        "gym_sports": "https://www.htzone.co.il/sale/1155",
        "kids_baby": "https://www.htzone.co.il/sale/1156",
    }
    
    if category and category in urls:
        print(f"   URL for {category}: {urls[category]}")
    else:
        print("   Category URLs:")
        for cat, url in urls.items():
            print(f"   - {cat}: {url}")
    
    return False


def check_staleness(kb):
    """Report which sources have stale or missing cache."""
    print("📊 Cache Status Report")
    print("=" * 50)
    
    today = datetime.now().date()
    ttl_days = kb.get("meta", {}).get("cache_ttl_days", 30)
    
    stale = []
    fresh = []
    
    for cat_id, cat_data in kb.get("categories", {}).items():
        for source_id, source_data in cat_data.get("sources", {}).items():
            if "cached_at" not in source_data:
                continue
                
            cached_at = source_data.get("cached_at")
            
            if cached_at is None:
                stale.append((cat_id, source_id, "never cached"))
            else:
                try:
                    cache_date = datetime.strptime(cached_at, "%Y-%m-%d").date()
                    age_days = (today - cache_date).days
                    
                    if age_days > ttl_days:
                        stale.append((cat_id, source_id, f"{age_days} days old"))
                    else:
                        fresh.append((cat_id, source_id, f"{age_days} days old"))
                except ValueError:
                    stale.append((cat_id, source_id, f"invalid date: {cached_at}"))
    
    if stale:
        print("\n⚠️  STALE (needs refresh):")
        for cat, source, reason in sorted(stale):
            print(f"   - {cat}/{source}: {reason}")
    
    if fresh:
        print("\n✅ FRESH:")
        for cat, source, reason in sorted(fresh):
            print(f"   - {cat}/{source}: {reason}")
    
    if not stale and not fresh:
        print("\n   No cacheable sources found.")
    
    return len(stale)


def main():
    parser = argparse.ArgumentParser(description="Refresh ClawSavings deal data")
    parser.add_argument("--source", choices=["poalim_wonder", "htzone_club", "all"],
                        help="Source to refresh")
    parser.add_argument("--category", help="Specific category to refresh")
    parser.add_argument("--status", action="store_true", 
                        help="Show cache staleness report")
    
    args = parser.parse_args()
    
    if not KB_PATH.exists():
        print(f"❌ KB not found at {KB_PATH}")
        sys.exit(1)
    
    kb = load_kb()
    
    if args.status:
        check_staleness(kb)
        return
    
    if not args.source:
        print("Usage: python refresh_deals.py --source <source> [--category <cat>]")
        print("       python refresh_deals.py --status")
        print()
        print("Sources: poalim_wonder, htzone_club, all")
        print()
        check_staleness(kb)
        return
    
    refreshers = {
        "poalim_wonder": refresh_poalim_wonder,
        "htzone_club": refresh_htzone_club,
    }
    
    if args.source == "all":
        for source, refresher in refreshers.items():
            refresher(kb, args.category)
            print()
    else:
        refreshers[args.source](kb, args.category)


if __name__ == "__main__":
    main()
