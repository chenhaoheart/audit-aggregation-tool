import json
import sqlite3
import sys
import os

sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design')
from services.section_chart_service import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM section_points LIMIT 3")
rows = c.fetchall()
for row in rows:
    d = dict(row)
    print("\nDict from Row:")
    for k, v in d.items():
        print(f"  {k}: {v} (type: {type(v).__name__})")
    # Now json serialize with default=str
    j = json.dumps(d, default=str)
    parsed = json.loads(j)
    print("\nAfter JSON round-trip:")
    for k, v in parsed.items():
        print(f"  {k}: {v} (type: {type(v).__name__})")

conn.close()
