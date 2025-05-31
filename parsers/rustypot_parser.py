import requests
import sqlite3
import logging
import time
from threading import Thread, Lock

logger = logging.getLogger('skin_updater')

class RustyPotParser:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.conn = sqlite3.connect("skins.db", check_same_thread=False)
        self.lock = Lock()
        self.running = False
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.init_db()

    def init_db(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rustypot_items (
                    name TEXT PRIMARY KEY,
                    price REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def fetch_items(self):
        """Альтернативный метод получения данных через HTTP API"""
        try:
            url = "https://rustypot.com/api/items"  # Замените на реальный API endpoint
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("items", [])
        except Exception as e:
            logger.error(f"Failed to fetch RustyPot items: {e}")
            return []

    def update_items(self):
        while self.running:
            try:
                items = self.fetch_items()
                if not items:
                    logger.warning("No items received from RustyPot")
                    time.sleep(60)
                    continue

                with self.lock:
                    cursor = self.conn.cursor()
                    for item in items:
                        try:
                            cursor.execute("""
                                INSERT INTO rustypot_items (name, price)
                                VALUES (?, ?)
                                ON CONFLICT(name) DO UPDATE SET
                                    price = excluded.price,
                                    last_updated = CURRENT_TIMESTAMP
                            """, (item["name"], item["price"]))
                        except Exception as e:
                            logger.error(f"DB error for item {item.get('name')}: {e}")
                    self.conn.commit()
                    logger.info(f"Updated {len(items)} RustyPot items")

                time.sleep(300)  # Обновляем каждые 5 минут

            except Exception as e:
                logger.error(f"RustyPot update error: {e}")
                time.sleep(60)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = Thread(target=self.update_items, daemon=True)
            self.thread.start()
            logger.info("RustyPot HTTP parser started")

    def stop(self):
        self.running = False
        if hasattr(self, 'thread') and self.thread:
            self.thread.join(timeout=1)
        self.conn.close()

    def get_data(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, price FROM rustypot_items")
            rows = cursor.fetchall()
            return [{
                "name": row[0],
                "deposit_price": float(row[1]),
                "withdraw_price": float(row[1]),
                "have": 1,
                "max": 100
            } for row in rows]

rustypot_parser = RustyPotParser()

def get_rustypot_data():
    return rustypot_parser.get_data()