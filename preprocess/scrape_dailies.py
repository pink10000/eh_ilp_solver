import os
import re
import urllib.request
import json
from datetime import date, timedelta
from typing import Optional

def fetch_level_data(url: str) -> Optional[dict]:
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            
        # Try to find window.__LEVEL__ JSON
        match = re.search(r'window\.__LEVEL__\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def scrape_dailies():
    start_date = date(2025, 12, 30)
    end_date = date.today()
    
    target_dir = os.path.join("maps", "daily")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Check if already exists
        exists = any(f.startswith(date_str) for f in os.listdir(target_dir))
        
        if exists:
            # print(f"Skipping {date_str}, already exists.")
            pass
        else:
            url = f"https://enclose.horse/play/{date_str}"
            print(f"Scraping {date_str}...")
            
            level_data = fetch_level_data(url)
            if level_data:
                # Filename format: YYYY-MM-DD_budget_score.game
                budget = level_data.get("budget", 0)
                score = level_data.get("optimalScore", 0)
                map_str = level_data.get("map", "")
                
                if map_str:
                    filename = f"{date_str}_{budget}_{score}.game"
                    filepath = os.path.join(target_dir, filename)
                    with open(filepath, 'w') as f:
                        f.write(map_str)
                    print(f"  Saved to {filepath}")
                else:
                    print(f"  No map found for {date_str}")
            else:
                print(f"  Failed to get level data for {date_str}")
        
        current_date += timedelta(days=1)

if __name__ == "__main__":
    scrape_dailies()
