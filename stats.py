import os
import sqlite3
import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()
# Extract SQLite path from DB_URL env var
db_url = os.getenv("DB_URL", "sqlite:///state.db").split("sqlite:///")[-1]
conn = sqlite3.connect(db_url)
cursor = conn.cursor()
# Ensure the actions table exists
cursor.execute("CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, date TEXT, type TEXT, success INTEGER)")
conn.commit()

def main():
    today = datetime.date.today().isoformat()
    types = ["invite", "like", "comment"]
    print(f"Action summary for {today}:")
    total = 0
    for t in types:
        cursor.execute("SELECT COUNT(*) FROM actions WHERE date=? AND type=?", (today, t))
        count = cursor.fetchone()[0]
        print(f"  {t}s: {count}")
        total += count
    print(f"  Total actions: {total}")

    # Success rate
    cursor.execute(
        "SELECT COUNT(*) FROM actions WHERE date=? AND success=1", (today,)
    )
    successes = cursor.fetchone()[0]
    rate = (successes / total * 100) if total > 0 else 0
    print(f"Success rate: {rate:.2f}%")

    print("\nRecent actions (last 1000):")
    cursor.execute(
        "SELECT id, date, type, success FROM actions ORDER BY id DESC LIMIT 1000"
    )
    rows = cursor.fetchall()
    for row in rows:
        id_, date, typ, success = row
        status = "✔" if success else "✖"
        print(f"{id_:4d} | {date} | {typ:7s} | {status}")

if __name__ == "__main__":
    main() 