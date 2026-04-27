import json

with open(r'd:\github\空间数据检查桌面版-主题-design\异常断面汇总_test2.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('const SECTIONS = ') + len('const SECTIONS = ')
pos = start
brace_count = 0
while pos < len(content):
    if content[pos] == '{':
        brace_count += 1
    elif content[pos] == '}':
        brace_count -= 1
        if brace_count == 0:
            break
    pos += 1

sections_json = content[start:pos+1]
sections = json.loads(sections_json)

if sections:
    first_key = list(sections.keys())[0]
    sec = sections[first_key]
    points = sec.get('points', [])
    
    print("Points count:", len(points))
    print("\nFirst 3 points (full):")
    for i, p in enumerate(points[:3]):
        print(f"  Point {i}: {json.dumps(p, indent=4)}")
    
    distances = [p.get('distance') for p in points]
    elevations = [p.get('elevation') for p in points]
    
    print("\nDistance types:", [type(d).__name__ for d in distances[:5]])
    print("Elevation types:", [type(e).__name__ for e in elevations[:5]])
    print("\nAll distances are numbers:", all(isinstance(d, (int, float)) for d in distances))
    print("All elevations are numbers:", all(isinstance(e, (int, float)) for e in elevations))
