# Ansys Mechanical 静力学自动化 Skill（PyMechanical 直连）

一个面向 Ansys Mechanical 用户的**免费开源 skill**：用 PyMechanical 库自动跑静力学分析
（导入 STEP → 建分析 → 赋材料 → 网格 → 加固定支撑 + 载荷 → 求解 → 读结果云图）。

适合学习、教学和「福利发放」场景——粉丝装好 PyMechanical + 本机 Ansys 即可照跑，
**全程不依赖官方 MCP server**。

> 作者：Zhang Zheng（抖音「YES 工程师」）。本仓库为教学/福利用途，欢迎 star / fork。

---

## 特性

- **纯 PyMechanical 直连**：`launch_mechanical()` + `run_python_script()`，不启动任何 MCP server
- **几何实体显示**：导入后自动切成实体着色（不再是线框）
- **结果云图无边框**：自动隐藏结果上的网格线（「边 → 无边框」）
- **中文连通自检**：`connect_check.py` 一键排查 Python 版本 / 库 / Ansys 路径问题
- **坑位全覆盖**：Python 3.12、`insecure` 连接、mm 单位、中文结果名、命名选择多选键槽面等

---

## 环境要求

| 依赖 | 说明 |
|---|---|
| **Windows + Ansys Mechanical 2024 R2 (v242)** | 其他版本内部 API 可能变化（脚本已针对 v242 验证） |
| **Python 3.12** | ⚠️ **不要用 3.13**：`grpcio` 官方无 cp313 wheel，`pip install` 会直接失败 |
| `ansys-mechanical-core` | `pip install ansys-mechanical-core`（装包慢/失败换清华源 `-i https://pypi.tuna.tsinghua.edu.cn/simple`） |
| 本机已装**授权的** Ansys Mechanical | PyMechanical 只是驱动程序，需你自备 Ansys 许可 |

---

## 快速开始

```bash
# 0. 先跑环境自检（中文报告卡在哪）
python connect_check.py

# 1. 改两个路径：打开 scripts/ansys_mechanical_static.py，把顶部
#    STEP_PATH（你的零件）和 MECH_EXE（AnsysWBU.exe 真实路径）改成你自己的
#   注意：C:\Program Files 下的 Ansys 常是残缺目录，找不到就到 E:\ 盘找

# 2. 运行（1800=保持窗口 30 分钟供录屏；2=每步停 2 秒看清过程；第二数传 0 关闭延时）
python ansys_mechanical_static.py 1800 2
```

求解后日志打印 `SOLVED: MaxDef=... | MaxEqvStress=...`，结果云图自动以「无边框」显示，几何为实体着色。

---

## 文件结构

```
ansys-mechanical-static/
├── SKILL.md                          # 给 AI（WorkBuddy/Claude）看的技能说明
├── README.md                         # 本文件（给人看）
├── LICENSE                           # MIT License
├── scripts/
│   ├── ansys_mechanical_static.py    # 主脚本：两端固定 + 中部 1000N 示例工况
│   └── connect_check.py              # 环境连通自检向导
└── references/
    └── pitfalls.md                   # 所有踩坑详解 + 官方源码行号
```

> 用 WorkBuddy 的粉丝：把整个目录解压到 `~/.workbuddy/skills/`，之后跟 AI 说
> 「用 PyMechanical 跑一个静力学分析」即可让它接管本脚本。
> 不用 WorkBuddy 的粉丝：直接拿 `scripts/` 里的 `.py` 跑即可。

---

## 工作原理

```python
from ansys.mechanical.core import launch_mechanical
mech = launch_mechanical(batch=False, exec_file=MECH_EXE, transport_mode="insecure")
mech.run_python_script('''<Mechanical 内部 IronPython 2.7 脚本>''')  # 建分析/网格/边界/求解
mech.exit()
```

Mechanical 内部是 **IronPython 2.7**，禁用 f-string，用 `%` 格式化。
结果读取用对象引用（`td.Maximum` / `es.Maximum`），不按英文名匹配「总变形/等效应力」。

---

## 常见问题

见 [`references/pitfalls.md`](references/pitfalls.md)，重点：

- **Python 必须 3.12**：3.13 的 `grpcio` 装不上。
- **连接报安全 gRPC 错误**：加 `transport_mode="insecure"`（v242 未打 SP05 不支持安全 gRPC）。
- **导入后只见线框**：脚本已自动设 `ModelDisplay=ShadedExteriorAndEdges`，确认该句执行成功。
- **结果上还有网格线**：脚本已设 `ExtraModelDisplay=NoWireframe`；切勿用
  `ExtAPI.Graphics.ShowMesh` 或 `edgeDisplay`（在 PyMechanical 里会 FAIL）。
- **固定支撑多选了面**：v242 坐标范围法会把端部键槽面带进来，脚本已收紧容差到 ±3mm。

---

## 许可证与合规（License & Compliance）

- **本仓库代码**：以 [MIT License](LICENSE) 发布，版权归 Zhang Zheng 所有。可自由使用、修改、分发、商用。
- **第三方依赖**：`ansys-mechanical-core`（PyMechanical）由 Ansys, Inc. 以 **Apache License 2.0** 发布。
- **Ansys Mechanical** 是 Ansys, Inc. 的**商业软件**，需用户自备有效授权；本仓库不包含 Ansys 任何程序文件或源代码，仅通过公开 API 调用。
- **商标**：ANSYS® 是 Ansys, Inc. 或其子公司在美国及其他国家的注册商标。本仓库与 Ansys, Inc. **无官方关联**，仅为技术教学用途提及该名称。
- 本仓库所有内容仅供学习研究，**作者不对分析结果的准确性或任何使用后果负责**。

---

## 免责声明

本工具按「现状」提供，不提供任何明示或暗示的担保。使用本工具进行的任何工程分析，
其正确性、安全性与合规性由使用者自行负责。
