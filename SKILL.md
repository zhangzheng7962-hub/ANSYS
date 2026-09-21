---
name: ansys-mechanical-static
description: "This skill should be used when a user wants to automate a static structural (静力学) analysis in Ansys Mechanical through PyMechanical (the ansys.mechanical.core Python library) — importing a STEP/IGES part, assigning material, meshing, applying fixed supports and loads, solving, and reading deformation/stress results. It covers the correct IronPython/API calls and the known PyMechanical 2024 R2 (v242) pitfalls: insecure gRPC connection, geometry display mode (ModelDisplay), result edge/mesh hiding (ExtraModelDisplay), mm units, Chinese result names, and named-selection face over-selection. It drives Mechanical directly via PyMechanical and does NOT require the official Mechanical MCP server."
agent_created: true
---

# Ansys Mechanical 静力学分析 (PyMechanical 直连)

通过 PyMechanical 库直接驱动 Ansys Mechanical 做静力学自动化。适合「发福利/教学」
场景: 给一个 STEP 零件, 自动建分析、导几何、赋材料、网格、加边界条件、求解、读结果。
全程不依赖官方 MCP server, 粉丝装好 PyMechanical + 本机 Ansys 即可照跑。

## 何时使用

- 用户要「用 Python 驱动 Ansys 做静力学/结构分析」
- 用户要导入 STEP/IGES 零件、自动加固定支撑 + 载荷、求解变形/应力
- 用户要把结果云图的网格线隐藏(「边 → 无边框」)、把几何显示为实体
- 用户遇到 PyMechanical 连接/API 报错 (insecure、ShowMesh 不存在、中文结果名等)

## 工作流

0. **先跑环境自检**: `python connect_check.py` — 中文报告 Python 版本 / 库 / Ansys 路径是否就绪,
   不通会指出具体卡点(多数粉丝卡在 Python 3.13 装不上 grpcio 或 Ansys 路径填错)。
1. **确认环境**: 用户已 `pip install ansys-mechanical-core`, 且本机有 Ansys 安装
   (记下 `AnsysWBU.exe` 的真实完整路径, 默认 `C:\Program Files` 下的常是残缺目录)。
   ⚠️ **Python 必须用 3.12, 不要用 3.13**: grpcio 官方无 cp313 轮子, 3.13 下 `pip install`
   会直接失败。建一个 3.12 的 venv 再装最稳 (装包慢/502 时换清华源 `-i https://pypi.tuna.tsinghua.edu.cn/simple`)。
2. **改两个路径**: 复制 `scripts/ansys_mechanical_static.py`, 把顶部的
   `STEP_PATH` (零件) 和 `MECH_EXE` (Mechanical 可执行文件) 改成用户自己的。
3. **运行**: `python ansys_mechanical_static.py 1800 2`
   (1800=保持窗口 30 分钟供录屏; 2=每步停 2 秒看清过程; 第二个数传 0 可关延时)。
4. **读结果**: 求解后日志打印 `SOLVED: MaxDef=... | MaxEqvStress=...`,
   结果云图自动以「无边框」显示(无网格线), 几何为实体着色。

## 关键事实 (详见 references/pitfalls.md)

- **连接**: `launch_mechanical(batch=False, exec_file=MECH_EXE, transport_mode="insecure")`。
  2024 R2 (v242) 未打 SP05 不支持安全 gRPC; `launch_mechanical` 不接受 `timeout=` 参数。
- **Mechanical 内是 IronPython 2.7**: 禁用 f-string, 用 `%` 格式化。
- **单位**: 探测坐标即当前建模单位, 轴类零件通常是 **mm**, 别按米处理。
- **中文结果名**: 读结果用对象引用 (`td.Maximum` / `es.Maximum`), 别按英文名匹配
  「总变形/等效应力」。
- **几何显示(实体/线框)**: `ExtAPI.Graphics.ViewOptions.ModelDisplay = ModelDisplay.ShadedExteriorAndEdges`
- **结果网格线隐藏(无边框)**: `ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay
  = MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe` (赋整数 `0` 亦可)。
- **两个 API 不要混**, 且以下写法在 PyMechanical 里会 FAIL, 切勿使用:
  `ExtAPI.Graphics.ShowMesh`、`ds.Graphics.ResultPrefs.edgeDisplay`、
  `launch_mechanical(timeout=...)`。
- **命名选择**: worksheet 坐标范围选端面时, 容差收紧到 ±3mm, 避免把端部键槽/特征面多选进来。

## 资源

- `scripts/connect_check.py` — 环境连通自检 (跑主脚本前先跑, 中文排错向导)。
- `scripts/ansys_mechanical_static.py` — 完整可运行模板 (两端固定 + 中部 1000N 示例工况)。
- `references/pitfalls.md` — 坑位详解 + 官方源码行号 (`aisol/.../DSPages/Python/toolbar.py`)。

## 调整工况

- 改载荷大小/方向: 脚本 §9 `force.{分量}.Output.DiscreteValues = [Quantity("-1000 [N]")]`。
- 改支撑/载荷位置: 改 §8 命名选择的范围 (`lo/hi/END_TOL` 或 `mid±tol`)。
- 纯实体无轮廓边: §4 把 `ShadedExteriorAndEdges` 改成 `ShadedExterior`。
- 存盘: §11 把 `SAVE_ENABLED = True` (脚本会先删旧 mechdat 再 SaveAs)。
