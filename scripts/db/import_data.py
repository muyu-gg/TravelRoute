"""功能说明：从 SQL 文件导入景点数据到数据库。"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_route.settings')
django.setup()

from django.db import connection

def import_sql_file(sql_file_path: str) -> bool:
    """功能说明：执行 SQL 文件导入数据。"""
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL 文件不存在: {sql_file_path}")
        return False

    print(f"📂 正在读取 SQL 文件: {sql_file_path}")
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print("🔌 连接数据库...")
    with connection.cursor() as cursor:
        try:
            # 分割 SQL 语句（按分号分割，但忽略字符串内的分号）
            statements = []
            current_statement = []
            in_string = False
            string_char = None

            for char in sql_content:
                if char in ("'", '"') and not in_string:
                    in_string = True
                    string_char = char
                    current_statement.append(char)
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                    current_statement.append(char)
                elif char == ';' and not in_string:
                    current_statement.append(char)
                    statement = ''.join(current_statement).strip()
                    if statement and not statement.startswith('--'):
                        statements.append(statement)
                    current_statement = []
                else:
                    current_statement.append(char)

            print(f"📝 找到 {len(statements)} 条 SQL 语句")
            executed = 0
            for idx, statement in enumerate(statements, 1):
                if statement.upper().startswith('INSERT') or statement.upper().startswith('USE'):
                    try:
                        cursor.execute(statement)
                        executed += 1
                        if executed % 50 == 0:
                            print(f"   ✅ 已执行 {executed}/{len(statements)} 条...")
                    except Exception as e:
                        print(f"   ⚠️ 语句 {idx} 执行失败: {str(e)[:100]}")

            connection.commit()
            print(f"\n✅ 成功执行 {executed} 条 SQL 语句！")
            return True

        except Exception as e:
            connection.rollback()
            print(f"\n❌ 导入失败: {e}")
            return False


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 景点数据导入工具")
    print("=" * 60)

    sql_file = os.path.join(os.path.dirname(__file__), 'attraction_data.sql')

    success = import_sql_file(sql_file)

    if success:
        print("\n" + "=" * 60)
        print("🎉 数据导入完成！验证中...")
        print("=" * 60)

        from travel.models import Attraction
        from django.db.models import Count

        total = Attraction.objects.count()
        beijing_count = Attraction.objects.filter(city_name__icontains='北京').count()

        print(f"\n📊 导入后统计:")
        print(f"   总景点数: {total}")
        print(f"   北京景点: {beijing_count}")

        if beijing_count > 0:
            print("\n✨ 北京景点列表:")
            for attr in Attraction.objects.filter(city_name__icontains='北京')[:5]:
                print(f"   - {attr.name}")

        print("\n" + "=" * 60)
        print("✅ 全部完成！现在可以重新测试旅游规划功能了！")
        print("=" * 60)