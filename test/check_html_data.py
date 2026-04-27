import json

# 读取HTML文件中的SECTIONS数据
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
    
    print("断面:", sec['name'])
    print("点数:", len(points))
    
    distances = [p.get('distance') for p in points]
    elevations = [p.get('elevation') for p in points]
    
    print("\nDistance range:", min(distances), "-", max(distances))
    print("Elevation range:", min(elevations), "-", max(elevations))
    print("\nUnique elevation values:", len(set(elevations)))
    
    print("\nAll distance values:")
    print(distances)
    
    print("\nAll elevation values:")
    print(elevations)
