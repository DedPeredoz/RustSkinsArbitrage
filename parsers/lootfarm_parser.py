import requests
from datetime import datetime

def get_lootfarm_data():
    url = "https://loot.farm/fullpriceRUST.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, list):
            return []

        items = []
        for item in data:
            try:
                withdraw_price = float(item.get("price", 0)) / 100
                deposit_price = withdraw_price * 0.92
                
                items.append({
                    "name": str(item.get("name", "")).strip(),
                    "deposit_price": deposit_price,
                    "withdraw_price": withdraw_price,
                    "have": int(item.get("have", 0)),
                    "max": int(item.get("max", 0))
                })
            except (ValueError, TypeError):
                continue
                
        return items
        
    except Exception:
        return []