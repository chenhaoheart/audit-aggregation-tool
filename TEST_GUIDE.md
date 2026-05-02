# 主题保存功能测试指南

## 📋 测试前准备

✅ **已完成修改：**
1. `ui/dialogs/theme_dialog.py` - 添加了点击即保存逻辑
2. `core/theme_manager.py` - 添加了调试日志

## 🧪 测试步骤

### 步骤1: 确认程序已启动
- 程序窗口应该已打开
- 控制台应该显示运行日志

### 步骤2: 打开主题对话框
- 点击侧边栏或导航栏的**主题按钮**
- 应该弹出主题选择对话框

### 步骤3: 切换主题并观察控制台输出
点击任意主题卡片（比如"暗黑"），然后**立即查看控制台**，应该看到：

```
[DEBUG] _on_theme_clicked 被调用: dark
[DEBUG] 已选择主题: dark
[DEBUG] 准备调用 set_mode(dark)
[DEBUG] 保存配置到: d:\...\config\theme.json
[DEBUG] 保存内容: {'mode': 'dark', 'glass_opacity': 1.0}
[DEBUG] 配置保存成功！
[DEBUG] set_mode 调用完成
```

### 步骤4: 验证文件是否更新
在**不关闭程序**的情况下，打开 `config/theme.json` 文件查看：
```json
{
  "mode": "dark",
  "glass_opacity": 1.0
}
```
应该看到 mode 已经改变！

### 步骤5: 关闭对话框
点击"关闭"按钮

### 步骤6: 关闭整个程序
关闭主窗口

### 步骤7: 重新启动程序
```bash
python main.py
```

### 步骤8: 验证主题是否保持
- 程序启动后应该使用你刚才选择的主题
- 再次打开主题对话框，应该看到之前选择的主题被选中

## 🔍 问题排查

### 如果看不到 [DEBUG] 日志：
❌ **可能原因：** 还在使用旧代码
✅ **解决方法：**
1. 完全关闭程序（包括任务管理器中的进程）
2. 重新运行 `python main.py`

### 如果看到 [DEBUG] 日志但文件没变：
❌ **可能原因：** 文件权限问题或路径错误
✅ **检查项：**
1. 查看 `[DEBUG] 保存配置到:` 后面的路径是否正确
2. 检查是否有错误信息
3. 手动检查该路径下的 theme.json 文件

### 如果文件变了但重启后恢复：
❌ **可能原因：** 有其他代码在初始化时重置主题
✅ **检查项：**
1. 查看 `_load_config()` 是否正确读取
2. 检查是否有其他地方调用 `set_mode(ThemeMode.FLAME)`

## 📊 当前状态

- **配置文件位置**: `config/theme.json`
- **当前值**: forest (来自之前的测试)
- **预期行为**: 点击主题卡片后立即保存，无需点确定

## 💡 技术细节

### 修改的关键代码位置：

#### 1. ui/dialogs/theme_dialog.py:322-337
```python
def _on_theme_clicked(self, theme_mode: str):
    print(f"[DEBUG] _on_theme_clicked 被调用: {theme_mode}")
    # ... 选择逻辑 ...
    print(f"[DEBUG] 准备调用 set_mode({self._selected_theme})")
    theme_manager = get_theme_manager()
    theme_manager.set_mode(self._selected_theme)  # ← 这里会触发保存
    print(f"[DEBUG] set_mode 调用完成")
```

#### 2. core/theme_manager.py:186-193
```python
def _save_config(self):
    try:
        data = {'mode': self._mode, 'glass_opacity': self._glass_opacity}
        print(f"[DEBUG] 保存配置到: {self.config_file}")  # ← 调试信息
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] 配置保存成功！")  # ← 调试信息
    except Exception as e:
        print(f"保存主题配置失败: {e}")
```

## ✅ 成功标志

如果一切正常，你应该看到：
1. ✅ 点击主题卡片后控制台出现 DEBUG 日志
2. ✅ config/theme.json 文件内容立即更新
3. ✅ 关闭并重启程序后，新主题生效

---

**现在请按照上述步骤操作，并将控制台输出贴给我！**
