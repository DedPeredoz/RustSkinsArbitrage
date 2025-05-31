import os
import time
import sqlite3
import logging
from datetime import datetime
from threading import Thread
from parsers.rustbet_parser import get_rustbet_data
from parsers.lootfarm_parser import get_lootfarm_data
from parsers.swapgg_parser import get_swapgg_data
from parsers.cstrade_parser import get_cstrade_data
from parsers.rustypot_parser import rustypot_parser, get_rustypot_data

def setup_logger():
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger('skin_updater')
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(
        'logs/skins_updater.log', 
        encoding='utf-8',
        mode='a'
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

class SkinUpdater:
    def __init__(self):
        self.running = False
        self.update_interval = 1800
        self.sources = {
            "rustbet": get_rustbet_data,
            "lootfarm": get_lootfarm_data,
            "swapgg": get_swapgg_data,
            "cstrade": get_cstrade_data,
            "rustypot": get_rustypot_data
        }
        self.init_db()
        rustypot_parser.start()
        logger.info("="*50)
        logger.info("Система мониторинга цен запущена")
        logger.info(f"Интервал обновления: {self.update_interval} секунд")
        logger.info("="*50)

    def init_db(self):
        try:
            with sqlite3.connect("skins.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS skins (
                        name TEXT NOT NULL,
                        source TEXT NOT NULL,
                        deposit_price REAL,
                        withdraw_price REAL,
                        have INTEGER,
                        max INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (name, source)
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON skins(source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON skins(name)")
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    def update_source(self, source_name, parser):
        try:
            start_time = time.time()
            logger.info(f"Начато обновление: {source_name}")
            
            items = parser()
            if not items:
                logger.warning(f"Нет данных от источника: {source_name}")
                return

            with sqlite3.connect("skins.db") as conn:
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
                        logger.error(f"Ошибка элемента {item.get('name')}: {str(e)}")

                conn.commit()
                elapsed = time.time() - start_time
                logger.info(f"Обновление завершено: {source_name} - {success_count}/{len(items)} предметов за {elapsed:.2f} сек")
                
        except Exception as e:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА ({source_name}): {str(e)}")

    def update_all_sources(self):
        threads = []
        for source_name, parser in self.sources.items():
            if source_name == "rustypot":
                continue
            thread = Thread(target=self.update_source, args=(source_name, parser))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()

    def run(self):
        self.running = True
        logger.info("Автообновление данных запущено")
        
        try:
            while self.running:
                next_update = time.time() + self.update_interval
                self.update_all_sources()
                
                while time.time() < next_update and self.running:
                    time.sleep(1)
                
                logger.info(f"Следующее обновление в: {datetime.fromtimestamp(next_update)}")
                
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки...")
        finally:
            self.running = False
            rustypot_parser.stop()
            logger.info("Автообновление данных остановлено")

if __name__ == "__main__":
    updater = SkinUpdater()
    updater.run()