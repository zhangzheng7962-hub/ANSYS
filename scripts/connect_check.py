# -*- coding: utf-8 -*-
"""
Ansys Mechanical 静力学 - 环境连通自检 (粉丝免费版配套)
跑主脚本前先跑这个: python connect_check.py
中文报告环境是否就绪, 不通会指出具体卡点, 多数粉丝卡在 Python 版本或 Ansys 路径。
"""
import sys
import os

# ↓↓↓ 粉丝改这一行: 你的 Mechanical 可执行文件真实完整路径 ↓↓↓
# 注意: Ansys 默认装在 C:\Program Files 下的常是残缺目录, 真身通常在自建盘符,
# 例如 E:\ANSYS2024R2\ANSYS Inc\v242\aisol\bin\winx64\AnsysWBU.exe
MECH_EXE = r"E:\ANSYS2024R2\ANSYS Inc\v242\aisol\bin\winx64\AnsysWBU.exe"


def check():
    ok = True
    print("=== Ansys Mechanical 环境自检 ===\n")

    # 1. Python 版本
    major, minor = sys.version_info[:2]
    if (major, minor) == (3, 13):
        ok = False
        print("[FAIL] Python 3.13 不支持: grpcio 无 cp313 预编译包, "
              "pip install ansys-mechanical-core 会失败")
        print("       解决: 用 Python 3.12 建 venv 再装 (python3.12 -m venv venv)")
    elif major == 3 and minor < 12:
        ok = False
        print("[WARN] Python %d.%d 偏老, 建议 3.12" % (major, minor))
    else:
        print("[OK]   Python %d.%d" % (major, minor))

    # 2. 库是否安装
    try:
        import ansys.mechanical.core  # noqa: F401
        print("[OK]   ansys-mechanical-core 已安装")
    except Exception as e:
        ok = False
        print("[FAIL] ansys-mechanical-core 未安装: %s" % e)
        print("       解决: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ansys-mechanical-core")

    # 3. Ansys 可执行文件路径
    if os.path.isfile(MECH_EXE):
        print("[OK]   AnsysWBU.exe 路径存在")
    else:
        ok = False
        print("[FAIL] AnsysWBU.exe 路径不存在: %s" % MECH_EXE)
        print("       解决: 找到本机 Ansys 安装目录下的 AnsysWBU.exe "
              "(常在 <盘>:/.../v242/aisol/bin/winx64/) 并改上方 MECH_EXE")

    print("")
    if ok:
        print("=== 环境就绪, 可运行: python ansys_mechanical_static.py 1800 2 ===")
        print("=== 若运行后仍连不上/报错, 可找作者付费协助连通 ===")
    else:
        print("=== 环境未就绪, 按上面 [FAIL] 逐条处理 ===")
        print("=== 自己搞不定可找作者付费连通环境 ===")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check() else 1)
