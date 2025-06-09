import requests
from datetime import datetime

def get_cstrade_data():
    url = "https://cdn.cs.trade:2096/api/prices_RUST"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, dict):
            return []
        
        items = []
        for name, info in data.items():
            try:
                withdraw_price = float(info.get("price", 0))
                deposit_price = withdraw_price * 0.92
                
                items.append({
                    "name": str(name).strip(),
                    "deposit_price": deposit_price,
                    "withdraw_price": withdraw_price,
                    "have": int(info.get("have", 0)),
                    "max": int(info.get("max", 1))
                })
            except (ValueError, TypeError):
                continue
                
        return items
        
    except Exception:
        return []