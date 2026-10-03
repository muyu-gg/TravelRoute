"""功能说明：CSRF 调试工具 - 帮助诊断和解决 CSRF 问题。"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from django.conf import settings

print("=" * 70)
print("🔐 CSRF 配置检查工具")
print("=" * 70)

# 1. 检查 CSRF 相关设置
print("\n📋 Django CSRF 设置:")
print(f"   CSRF_COOKIE_NAME: {getattr(settings, 'CSRF_COOKIE_NAME', '未设置')}")
print(f"   CSRF_HEADER_NAME: {getattr(settings, 'CSRF_HEADER_NAME', '未设置')}")
print(f"   CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', '未设置')}")
print(f"   CSRF_COOKIE_HTTPONLY: {getattr(settings, 'CSRF_COOKIE_HTTPONLY', '未设置')}")
print(f"   CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', '未设置')}")
print(f"   SESSION_COOKIE_AGE: {getattr(settings, 'SESSION_COOKIE_AGE', '未设置')} 秒")

# 2. 检查中间件配置
print("\n🔧 中间件配置:")
middleware_classes = getattr(settings, 'MIDDLEWARE', [])
csrf_middleware_found = False
for middleware in middleware_classes:
    if 'csrf' in middleware.lower():
        print(f"   ✅ 找到: {middleware}")
        csrf_middleware_found = True

if not csrf_middleware_found:
    print("   ❌ 未找到 CSRF 中间件！")

# 3. 检查模板渲染
print("\n📝 模板检查:")
template_path = os.path.join(os.path.dirname(__file__), 'templates', 'planner', 'planner.html')
if os.path.exists(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if '{% csrf_token %}' in content:
            print("   ✅ planner.html 包含 {% csrf_token %}")
        else:
            print("   ❌ planner.html 缺少 {% csrf_token %}")

        if 'X-CSRFToken' in content:
            print("   ✅ JavaScript 包含 X-CSRFToken 头")
        else:
            print("   ⚠️  JavaScript 可能缺少 X-CSRFToken 头")
else:
    print(f"   ⚠️  未找到模板文件: {template_path}")

# 4. 输出解决方案
print("\n" + "=" * 70)
print("💡 解决方案（按优先级排序）")
print("=" * 70)

solutions = [
    {
        "title": "方案1：强制刷新页面（推荐首先尝试）",
        "steps": [
            "1. 在浏览器中按 Ctrl + Shift + R (Windows) 或 Cmd + Shift + R (Mac)",
            "2. 或者按 Ctrl + F5 强制刷新",
            "3. 这会重新加载页面并获取新的 CSRF token",
        ]
    },
    {
        "title": "方案2：清除浏览器缓存和 Cookie",
        "steps": [
            "1. 按 F12 打开开发者工具",
            "2. 右键点击浏览器的刷新按钮",
            "3. 选择'清空缓存并硬性重新加载'",
            "4. 或者手动清除该站点的 Cookie 和缓存",
        ]
    },
    {
        "title": "方案3：使用隐私/无痕模式测试",
        "steps": [
            "1. 打开浏览器的隐私/无痕窗口",
            "2. 登录系统",
            "3. 访问规划页面并提交表单",
            "4. 如果正常工作，说明是缓存问题",
        ]
    },
    {
        "title": "方案4：检查多个标签页问题",
        "steps": [
            "1. 关闭所有其他浏览器标签页",
            "2. 只保留一个标签页访问应用",
            "3. 重新登录（如果需要）",
            "4. 再次尝试提交表单",
        ]
    },
]

for idx, solution in enumerate(solutions, 1):
    print(f"\n{solution['title']}")
    for step in solution["steps"]:
        print(f"   {step}")

print("\n" + "=" * 70)
print("🔍 高级调试信息")
print("=" * 70)
print("""
如果上述方案都不起作用，请检查：

1. 浏览器控制台错误：
   - 按 F12 → Console 标签
   - 查看是否有 JavaScript 错误

2. 网络请求详情：
   - 按 F12 → Network 标签
   - 提交表单，找到 POST 请求
   - 检查 Request Headers 中是否有 X-CSRFToken
   - 检查 Cookies 中是否有 csrftoken

3. Django 调试页面信息：
   - 当前页面显示的 CSRF 错误详情
   - 确认 Reason given for failure 部分

4. 临时禁用 CSRF（仅用于开发环境）：
   ⚠️  不推荐在生产环境中使用！

   可以在 settings.py 中添加：
   CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8000", "http://localhost:8000"]
""")

print("=" * 70)
print("✅ 检查完成")
print("=" * 70)