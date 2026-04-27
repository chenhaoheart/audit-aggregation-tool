# Extract the chart configuration from the HTML file
with open(r'd:\github\空间数据检查桌面版-主题-design\异常断面汇总_test2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and print the series configuration
for i, line in enumerate(lines):
    if 'series:' in line and 'yData.map' in line:
        print(f"Line {i+1}: {line.strip()}")
        # Also show context - 3 lines before and after
        print("\nContext:")
        for j in range(max(0, i-3), min(len(lines), i+4)):
            marker = ">>> " if j == i else "    "
            print(f"{marker}Line {j+1}: {lines[j].rstrip()}")
