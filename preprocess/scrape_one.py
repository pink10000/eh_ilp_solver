import os
import sys
import re
import urllib.request
import json
from typing import Optional

def fetch_level_data(url: str) -> Optional[dict]:
    try:
        # If url is just an ID like 'f3-ms3', convert it
        if not url.startswith("http"):
            url = f"https://enclose.horse/play/{url}"
            
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            
        match = re.search(r'window\.__LEVEL__\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_one.py <url_or_id> [target_dir]")
        sys.exit(1)
        
    url_or_id = sys.argv[1]
    target_dir = sys.argv[2] if len(sys.argv) > 2 else "maps/custom"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    print(f"Scraping {url_or_id}...")
    level_data = fetch_level_data(url_or_id)
    if level_data:
        # Filename format: ID_budget_score.game
        level_id = level_data.get("id", "level")
        budget = level_data.get("budget", 0)
        score = level_data.get("optimalScore", 0)
        map_str = level_data.get("map", "")
        
        if map_str:
            filename = f"{level_id}_{budget}_{score}.game"
            filepath = os.path.join(target_dir, filename)
            with open(filepath, 'w') as f:
                f.write(map_str)
            print(f"  Saved to {filepath}")
        else:
            print(f"  No map found for {url_or_id}")
    else:
        print(f"  Failed to get level data for {url_or_id}")

if __name__ == "__main__":
    main()
