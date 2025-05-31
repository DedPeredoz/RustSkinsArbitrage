#!/usr/bin/env python3
import time
import subprocess
from datetime import datetime

def main():
    print(f"🚀 Daily updater started at {datetime.now()}")
    updater_process = subprocess.Popen(["python", "updater.py"])
    
    try:
        while True:
            time.sleep(3600)
            print(f"⏳ System is running... {datetime.now()}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping the updater...")
        updater_process.terminate()
        updater_process.wait()
        print("✅ Updater stopped successfully")

if __name__ == "__main__":
    main()