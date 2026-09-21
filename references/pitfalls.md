# Ansys Mechanical 静力学 (PyMechanical) 常见坑与正确 API

> 配套脚本: `scripts/ansys_mechanical_static.py`
> 环境: Ansys 2024 R2 (v242) + PyMechanical 0.13.x + Python 3.12

---

## 0. Python 版本与装包

- **必须用 Python 3.12, 不要 3.13**: `grpcio` 无 cp313 预编译 wheel, 3.13 下 `pip install` 会编译失败或 `No matching distribution`。
  解决: `python3.12 -m venv venv && venv\Scripts\activate && pip install ansys-mechanical-core`。
- **装包慢/502**: 换清华源 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ansys-mechanical-core`。
- **只装公开库, 不装官方 MCP server**: 本 skill 用 `ansys.mechanical.core` (PyPI 公开库) 直连 Mechanical,
  与官方 `pymechanical-mcp` 无关, 粉丝无需下载/启动任何 MCP server。

## 1. 连接 / 启动

- **必须 insecure**: 2024 R2 (v242) 未打 SP05 时 gRPC 不支持安全连接, 否则安全握手报错。
  `launch_mechanical(batch=False, exec_file=MECH_EXE, transport_mode="insecure")`
- **`exec_file` 用真实安装路径**: 默认 `C:\Program Files\...` 常是残缺目录; 真身通常在自建盘符
  (如 `E:\ANSYS2024R2\ANSYS Inc\v242\aisol\bin\winx64\AnsysWBU.exe`)。找不到 exe 会启动失败。
- **`launch_mechanical` 没有 `timeout=` 参数** (0.13.x): 传了直接 `TypeError`。
  冷启动 30~50s 才就绪, 别加这个参数。

## 2. Mechanical 内是 IronPython 2.7

- **禁用 f-string**: 所有传给 `run_python_script()` 的字符串用 `%` 格式化。
- 模板注入坐标注意 `%` 转义 (脚本里 `CRIT_TPL % (...)`)。

## 3. 单位

- 面质心坐标 = 当前建模单位。轴类零件通常 **mm** (轴长 294 即 294mm, 不是 294m)。
  误按米处理会把范围放大 1000 倍, 把整根轴都选成"固定端"。
- 坐标判据必须带单位: `Quantity("12.345000 [mm]")`。

## 4. 中文界面结果名

- 中文版结果对象名是 **总变形 / 等效应力** (非 Total Deformation / Equivalent Stress),
  按英文名匹配 `Solution.Children` 会失败。
- **正确做法**: 用对象引用读最大值 —— `td = solution.AddTotalDeformation(); es = solution.AddEquivalentStress()`,
  然后读 `td.Maximum` / `es.Maximum`。

## 5. 命名选择 (Named Selection) 多选面

- worksheet 坐标范围选端面时, 容差过大(如 ±14.7mm)会把端部键槽/特征面也选入, 固定支撑变成多个面。
  收紧到端部 ±3mm 只取端面圆盘即可排除。
- 判据: `SelectionCriterionType.LocationX` + `SelectionOperatorType.RangeInclude` + 带 `[mm]` 的上下界 `Quantity`。

## 6. 两个"显示"是不同的 API (最容易混)

| 想要的效果 | 正确 API | 错误写法(会 FAIL) |
|---|---|---|
| 几何显示为实体/线框 | `ExtAPI.Graphics.ViewOptions.ModelDisplay = ModelDisplay.ShadedExteriorAndEdges` | — |
| 结果云图网格线隐藏 | `ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay = MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe` | `ExtAPI.Graphics.ShowMesh = False` |
| 同上(回退) | 直接赋整数 `0` (=NoWireframe) | `ds.Graphics.ResultPrefs.edgeDisplay = 0` |

- `ExtraModelDisplay` 取值: `0`=NoWireframe / `1`=UndeformedWireframe / `2`=UndeformedModel / `3`=ShowElements。
- `ShowMesh` / `edgeDisplay` 是 Mechanical **原生脚本窗口**写法, 经 gRPC 跨进程后这层 COM 不暴露, 故不可用。

## 7. 枚举符号作用域

- `MechanicalEnums`、`ModelDisplay` 等都是 IronPython **全局符号**, 直接可用, 不要 `import`。

## 8. 存盘

- `ExtAPI.DataModel.Project.SaveAs(path)` **不能覆盖已存在** mechdat (报 `file already exists`)。
  需存盘时先 `System.IO.File.Delete` 删旧文件(含 `*_files` 伴随目录)再 SaveAs。
  录制/演示可整个跳过(脚本 `SAVE_ENABLED = False`)。

## 9. 官方 API 佐证 (本机安装目录)

- 几何显示模式: `aisol/DesignSpace/DSPages/Python/toolbar.py` 第 ~982 行 `SwitchModelDisplayOptions()`。
- 结果"边"下拉: 同目录 `toolbar.py` 第 ~1332 行起, 对应 `ResultPreference.ExtraModelDisplay`。
