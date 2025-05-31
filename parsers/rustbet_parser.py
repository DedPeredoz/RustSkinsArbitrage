import requests
from collections import defaultdict

def get_rustbet_data():
    rustbet_url = "https://trade.rustbet.com/api/v1/public/gm/inventory/v2"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }

    all_items = []

    for page in range(1, 13):
        params = {
            'per_page': 60,
            'app_id': 252490,
            'order': 'DESC',
            'orderBy': 'price',
            'page': page
        }

        try:
            response = requests.get(rustbet_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict) or 'data' not in data:
                continue

            for item in data.get("data", []):
                try:
                    price = float(item.get("price", 0))
                    all_items.append({
                        "name": item.get("market_hash_name", "").strip(),
                        "deposit_price": price,
                        "withdraw_price": price,
                        "have": int(item.get("amount", 1)),
                        "max": 100
                    })
                except (ValueError, TypeError):
                    continue

        except requests.RequestException:
            continue

    return group_rustbet_items(all_items)

def group_rustbet_items(items):
    grouped = defaultdict(lambda: {"deposit_price": 0, "withdraw_price": 0, "have": 0, "max": 100})
    for item in items:
        name = item["name"]
        grouped[name]["deposit_price"] = item["deposit_price"]
        grouped[name]["withdraw_price"] = item["withdraw_price"]
        grouped[name]["have"] += item["have"]
        grouped[name]["max"] = item["max"]

    return [{
        "name": name,
        "deposit_price": info["deposit_price"],
        "withdraw_price": info["withdraw_price"],
        "have": info["have"],
        "max": info["max"]
    } for name, info in grouped.items()]