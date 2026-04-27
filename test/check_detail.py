import sys
sys.path.insert(0, r'd:\github\空间数据检查桌面版-主题-design')
from services.section_chart_service import SectionChartService, DB_PATH
import sqlite3
import json

service = SectionChartService()

# 获取一个断面的详细信息
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM sections WHERE anomaly = 1 OR validation_error = 1 LIMIT 1")
row = c.fetchone()
if row:
    key = row["section_key"]
    print(f"Testing section: {row['name']}")
    
    # 直接从数据库查询
    c.execute("SELECT * FROM section_points WHERE section_key = ? ORDER BY seq", (key,))
    points = []
    for pr in c.fetchall():
        p = dict(pr)
        points.append(p)
    
    print(f"\nDirect DB query - {len(points)} points")
    print("First 5 elevation values:", [p['elevation'] for p in points[:5]])
    print("First 5 distance values:", [p['distance'] for p in points[:5]])
    
    # 通过get_section_detail获取
    sec = service.get_section_detail(key)
    print(f"\nVia get_section_detail - {len(sec['points'])} points")
    print("First 5 elevation values:", [p['elevation'] for p in sec['points'][:5]])
    print("First 5 distance values:", [p['distance'] for p in sec['points'][:5]])

conn.close()
