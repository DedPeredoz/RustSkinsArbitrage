import requests

def get_swapgg_data():
    url = "https://api.swap.gg/v2/trade/inventory/bot/252490"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            print(f"Unexpected data format: {data}")
            return []

        items = []
        for item in data.get("result", []):
            try:
                withdraw_price = float(item.get("p", 0)) / 100
                deposit_price = withdraw_price * 0.92
                
                items.append({
                    "name": item.get("n", "").strip(),
                    "deposit_price": deposit_price,
                    "withdraw_price": withdraw_price,
                    "have": len(item.get("a", []))
                })
            except Exception as e:
                print(f"[SwapGG WARN] Item processing error: {e}")
                continue

        return items

    except requests.RequestException as e:
        print(f"[SwapGG ERROR] {e}")
        return []