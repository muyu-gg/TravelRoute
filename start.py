import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
MANAGE_PY = BASE_DIR / "manage.py"
REQUIREMENTS = BASE_DIR / "requirements.txt"


def _load_env():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()

DB_NAME = os.getenv("MYSQL_DATABASE", "travel_route_base")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))


def print_banner():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║        觅途行 · MiTuXing              ║")
    print("  ║     AI 旅游路线规划系统 一键启动      ║")
    print("  ╚══════════════════════════════════════╝")
    print()


def run(cmd, **kwargs):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)


def ensure_venv():
    if VENV_PYTHON.exists():
        print(f"  [信息] 虚拟环境已存在。")
        return
    print("  [信息] 正在创建虚拟环境...")
    subprocess.run([sys.executable, "-m", "venv", str(BASE_DIR / "venv")], check=True)
    print("  [信息] 正在安装依赖...")
    pip = str(BASE_DIR / "venv" / "Scripts" / "pip.exe")
    subprocess.run(
        [pip, "install", "-r", str(REQUIREMENTS), "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        check=True,
    )
    print("  [信息] 虚拟环境创建完成。")


def ensure_mysql():
    r = run("tasklist /FI \"IMAGENAME eq mysqld.exe\"")
    if "mysqld.exe" in r.stdout:
        print("  [信息] MySQL 正在运行。")
        return True
    print("  [警告] MySQL 未运行，尝试启动...")
    run("net start mysql")
    r2 = run("tasklist /FI \"IMAGENAME eq mysqld.exe\"")
    if "mysqld.exe" in r2.stdout:
        print("  [信息] MySQL 已启动。")
        return True
    print("  [错误] 无法启动 MySQL，请手动启动后重试。")
    return False


def _db_check_code():
    return (
        "import pymysql; "
        f"c=pymysql.connect(host='{DB_HOST}',port={DB_PORT},user='{DB_USER}',password='{DB_PASS}'); "
        "cur=c.cursor(); "
        f"cur.execute(\"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{DB_NAME}'\"); "
        "r=cur.fetchone(); c.close(); "
        "print('exists' if r else 'not_exists')"
    )


def _db_create_code():
    return (
        "import pymysql; "
        f"c=pymysql.connect(host='{DB_HOST}',port={DB_PORT},user='{DB_USER}',password='{DB_PASS}'); "
        "cur=c.cursor(); "
        f"cur.execute('CREATE DATABASE `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'); "
        "c.close(); print('created')"
    )


def ensure_database():
    r = subprocess.run(
        [str(VENV_PYTHON), "-c", _db_check_code()],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"  [错误] 连接 MySQL 失败: {r.stderr.strip()}")
        return False

    if "exists" in r.stdout:
        print(f"  [信息] 数据库 {DB_NAME} 已存在。")
        return True

    print("  [信息] 数据库不存在，正在初始化...")
    r2 = subprocess.run(
        [str(VENV_PYTHON), "-c", _db_create_code()],
        capture_output=True, text=True,
    )
    if r2.returncode != 0:
        print(f"  [错误] 创建数据库失败: {r2.stderr.strip()}")
        return False
    print("  [信息] 数据库创建成功，执行迁移...")
    subprocess.run([str(VENV_PYTHON), str(MANAGE_PY), "migrate", "--noinput"], check=True)
    print("  [信息] 数据库初始化完成。")
    return True


def ensure_superuser():
    r = subprocess.run(
        [
            str(VENV_PYTHON), "-c",
            "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','travel_route.settings'); "
            "import django; django.setup(); "
            "from accounts.models import User; "
            "print('yes' if User.objects.filter(is_superuser=True).exists() else 'no')",
        ],
        capture_output=True, text=True,
    )
    if "yes" in r.stdout:
        print("  [信息] 超级管理员已存在。")
        return
    print(f"  [信息] 创建超级管理员 {ADMIN_USER}/{ADMIN_PASS} ...")
    subprocess.run(
        [
            str(VENV_PYTHON), "-c",
            "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','travel_route.settings'); "
            "import django; django.setup(); "
            "from accounts.models import User; "
            "User.objects.create_superuser('admin','admin@example.com','admin123'); "
            "print('超级管理员创建成功')",
        ],
        check=True,
    )


def start_server():
    print()
    print("  ────────────────────────────────────────")
    print("  启动成功！")
    print()
    print(f"  首页:     http://127.0.0.1:{SERVER_PORT}/")
    print(f"  后台:     http://127.0.0.1:{SERVER_PORT}/admin/")
    print(f"  账号:     {ADMIN_USER} / {ADMIN_PASS}")
    print()
    print("  按 Ctrl+C 停止服务器")
    print("  ────────────────────────────────────────")
    print()
    try:
        subprocess.run([str(VENV_PYTHON), str(MANAGE_PY), "runserver", f"0.0.0.0:{SERVER_PORT}"])
    except KeyboardInterrupt:
        print("\n  服务器已停止。")


def main():
    print_banner()
    ensure_venv()
    if not ensure_mysql():
        sys.exit(1)
    if not ensure_database():
        sys.exit(1)
    ensure_superuser()
    start_server()


if __name__ == "__main__":
    main()