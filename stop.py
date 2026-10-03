import os
import sys
import subprocess


def print_banner():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║     觅途行 · 关闭所有相关进程         ║")
    print("  ╚══════════════════════════════════════╝")
    print()


def kill_process(name, display_name):
    r = subprocess.run(
        f'tasklist /FI "IMAGENAME eq {name}"',
        shell=True, capture_output=True, text=True,
    )
    if name.lower() in r.stdout.lower():
        print(f"  [关闭] {display_name} ({name})...")
        subprocess.run(f'taskkill /F /IM {name}', shell=True, capture_output=True)
        print(f"       已关闭。")
        return True
    else:
        print(f"  [跳过] 未发现运行中的 {name}。")
        return False


def main():
    print_banner()
    killed = False
    if kill_process("python.exe", "Django 服务器"):
        killed = True
    if kill_process("python3.11.exe", "Python 3.11"):
        killed = True
    if kill_process("pythonw.exe", "Python 无窗口进程"):
        killed = True

    print()
    if killed:
        print("  所有觅途行相关进程已关闭。")
    else:
        print("  未发现任何运行中的相关进程。")
    print()


if __name__ == "__main__":
    main()