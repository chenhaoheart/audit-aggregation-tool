with open(r'd:\github\空间数据检查桌面版-主题-design\异常断面汇总_test2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the showChart function and the ECharts configuration
in_showchart = False
brace_count = 0
for i, line in enumerate(lines):
    if 'function showChart' in line:
        in_showchart = True
        print(f"Line {i+1}: {line.rstrip()}")
        continue
    
    if in_showchart:
        print(f"Line {i+1}: {line.rstrip()}")
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0 and 'charts.section = chart' in line:
            break
