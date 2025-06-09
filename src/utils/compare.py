"""
Модуль для сравнения цен между разными площадками
Содержит функции для сравнения RustBet с другими маркетплейсами
"""
from collections import defaultdict

def group_rustbet_items(items):
    """
    Группирует предметы из RustBet по имени
    Args:
        items: Список предметов из RustBet API
    Returns:
        Сгруппированный список предметов с суммированным количеством
    """
    grouped = defaultdict(lambda: {"price": 0, "amount": 0})
    for item in items:
        name = item.get("name")
        price = item.get("price", 0)
        try:
            amount = int(item.get("amount", 1) or 1)
        except (ValueError, TypeError):
            amount = 1

        grouped[name]["price"] = price
        grouped[name]["amount"] += amount

    return [{"name": k, "price": v["price"], "amount": v["amount"]} for k, v in grouped.items()]

def compare_with_lootfarm(rust_items, loot_items, use_deposit_prices=False):
    """
    Сравнивает цены RustBet с LootFarm
    Args:
        rust_items: Предметы из RustBet
        loot_items: Предметы из LootFarm
        use_deposit_prices: Флаг использования депозитных цен
    Returns:
        Отсортированный список предметов с разницей цен
    """
    loot_dict = {item['name']: item for item in loot_items}
    results = []

    for item in rust_items:
        name = item["name"]
        rust_price = item["deposit_price" if use_deposit_prices else "withdraw_price"]
        amount = item.get("have", 1)
        loot_item = loot_dict.get(name)

        if loot_item:
            loot_price = loot_item['price']
            if loot_price == 0:
                continue
            percent_diff = ((rust_price - loot_price) / loot_price) * 100
            have_max_str = f"{loot_item['have']}/{loot_item['max']}"
            max_flag = "MAX" if loot_item['have'] >= loot_item['max'] else ""

            results.append({
                "Name": name,
                "RustBet Price": rust_price,
                "Amount": amount,
                "LootFarm Price": loot_price,
                "Difference (%)": percent_diff,
                "LootFarm Stock": have_max_str,
                "Max Status": max_flag
            })

    return sorted(results, key=lambda x: x['Difference (%)'], reverse=True)

def compare_with_swap(rust_items, swap_items):
    """
    Сравнивает цены RustBet с Swap.GG
    Args:
        rust_items: Предметы из RustBet
        swap_items: Предметы из Swap.GG
    Returns:
        Отсортированный список предметов с разницей цен
    """
    swap_dict = {
        item['n'].strip().lower(): item['p']
        for item in swap_items
    }

    results = []
    for item in rust_items:
        name = item["name"]
        rust_price = item["withdraw_price"]
        amount = item["have"]
        lookup_name = name.strip().lower()

        if lookup_name in swap_dict:
            swap_price = swap_dict[lookup_name]
            if swap_price == 0:
                continue
            percent_diff = ((rust_price - swap_price) / swap_price) * 100

            results.append({
                "Name": name,
                "RustBet Price": rust_price,
                "Amount": amount,
                "Swap.gg Price": swap_price,
                "Difference (%)": percent_diff
            })

    return sorted(results, key=lambda x: x['Difference (%)'], reverse=True)

def compare_with_cstrade(rust_items, cstrade_items):
    """
    Сравнивает цены RustBet с CS.TRADE
    Args:
        rust_items: Предметы из RustBet
        cstrade_items: Предметы из CS.TRADE
    Returns:
        Отсортированный список предметов с разницей цен
    """
    cs_dict = {item['Name']: item for item in cstrade_items}
    results = []

    for item in rust_items:
        name = item["name"]
        rust_price = item["withdraw_price"]
        amount = item["have"]
        cs_item = cs_dict.get(name)

        if cs_item:
            cs_price = cs_item["Price"]
            if cs_price == 0:
                continue
            percent_diff = ((rust_price - cs_price) / cs_price) * 100
            have_max_str = f"{cs_item['Have']}/{cs_item['Max']}"
            max_flag = "MAX" if cs_item['Have'] == cs_item['Max'] else ""

            results.append({
                "Name": name,
                "RustBet Price": rust_price,
                "Amount": amount,
                "CS.TRADE Price": cs_price,
                "Difference (%)": percent_diff,
                "CS.TRADE Stock": have_max_str,
                "Max Status": max_flag
            })

    return sorted(results, key=lambda x: x['Difference (%)'], reverse=True)