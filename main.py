# main.py
from src.database.init_db import init_database
from src.parsers.rustbet_parser import get_rustbet_data
from src.parsers.lootfarm_parser import get_lootfarm_data
from src.parsers.swapgg_parser import get_swapgg_data
from src.parsers.cstrade_parser import get_cstrade_data
from rustypot_ffi import get_rustypot_data  # Импорт Rust-функции
import sqlite3
import time
from datetime import datetime

def save_all_to_db():
    init_database()
    
    sources = {
        "rustbet": get_rustbet_data,
        "lootfarm": get_lootfarm_data,
        "swapgg": get_swapgg_data,
        "cstrade": get_cstrade_data,
        "rustypot": get_rustypot_data  # Rust-парсер
    }
    
    for source_name, parser in sources.items():
        try:
            print(f"\n[{datetime.now()}] Загрузка данных с {source_name}...")
            start_time = time.time()
            
            items = parser()
            # ... остальной код без изменений ...
            if not items:
                print(f"[ПРОПУСК] Нет данных от {source_name}")
                continue
                
            conn = sqlite3.connect('skins.db')
            cursor = conn.cursor()
            
            success_count = 0
            for item in items:
                try:
                    cursor.execute("""
                        INSERT INTO skins (name, source, deposit_price, withdraw_price, have, max)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(name, source) DO UPDATE SET
                            deposit_price = excluded.deposit_price,
                            withdraw_price = excluded.withdraw_price,
                            have = excluded.have,
                            max = excluded.max,
                            last_updated = CURRENT_TIMESTAMP
                    """, (
                        item["name"],
                        source_name,
                        item["deposit_price"],
                        item["withdraw_price"],
                        item["have"],
                        item.get("max", 100)
                    ))
                    success_count += 1
                except Exception as e:
                    print(f"[ОШИБКА] {source_name} - {item.get('name')}: {e}")
                    
            conn.commit()
            conn.close()
            print(f"[УСПЕХ] Обработано {success_count}/{len(items)} предметов за {time.time()-start_time:.2f} сек")
            
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА] {source_name}: {e}")

    print(f"\n[{datetime.now()}] Все данные успешно обновлены!")

if __name__ == "__main__":
    save_all_to_db()