"""功能说明：验证 CSRF 修复是否生效。"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from django.conf import settings

print("=" * 70)
print("✅ CSRF 修复验证")
print("=" * 70)

csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])

print(f"\n📋 当前 CSRF_TRUSTED_ORIGINS 配置:")
if csrf_trusted_origins:
    for origin in csrf_trusted_origins:
        print(f"   ✅ {origin}")
else:
    print("   ❌ 未配置")

print(f"\n🔍 检查结果:")

required_origins = ["http://127.0.0.1:8000", "http://localhost:8000"]
all_configured = all(origin in csrf_trusted_origins for origin in required_origins)

if all_configured:
    print("   ✅ 所有必要来源已配置")
    print("\n🎉 修复已完成！")
    print("\n下一步操作:")
    print("   1. 重启 Django 服务器 (必须)")
    print("   2. 强制刷新浏览器 (Ctrl+Shift+R)")
    print("   3. 重新提交旅游规划表单")
else:
    missing = [origin for origin in required_origins if origin not in csrf_trusted_origins]
    print(f"   ❌ 缺少配置: {missing}")
    print("\n⚠️  请检查 settings.py 中的 CSRF_TRUSTED_ORIGINS 设置")

print("\n" + "=" * 70)