# Ansys Mechanical 静力学 (PyMechanical) 常见坑与正确 API

> 配套脚本: `scripts/ansys_mechanical_static.py`
> 环境: Ansys 2024 R2 (v242) + PyMechanical 0.13.x + Python 3.12

---

## 0. Python 版本与装包 (最容易卡死的一步)

- **必须用 Python 3.12, 不要 3.13**: `grpcio` 官方到 2026 年仍**没有 cp313 的预编译 wheel**,
  `pip install ansys-mechanical-core` 在 3.13 下会编译 grpcio 失败或直接 `No matching distribution`。
  解决: `python3.12 -m venv venv && venv\Scripts\activate && pip install ansys-mechanical-core`。
- **装包慢/报 502**: 换清华源 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple ansys-mechanical-core`。
- **只装库, 不装官方 MCP server**: 本 skill 用 `ansys.mechanical.core` 这个**公开 PyPI 库**直接驱动
  Mechanical, 与官方 `pymechanical-mcp` (MCP server) **完全无关**。粉丝**不需要**下载/启动任何 MCP server,
  只要本机装了 Ansys + 这个库就能跑。

## 1. 连接 / 启动

- **必须 insecure**: 2024 R2 (v242) 未打 SP05 时 gRPC 不支持安全连接, 否则报安全握手错误。
  `launch_mechanical(batch=False, exec_file=MECH_EXE, transport_mode="insecure")`
- **`exec_file` 要真实安装路径**: Ansys 默认装在 `C:\Program Files\...` 往往是不完整目录; 真身通常在
  自建盘符 (如 `E:\ANSYS2024R2\ANSYS Inc\v242\aisol\bin\winx64\AnsysWBU.exe`)。找不到 exe 会启动失败。
- **`launch_mechanical` 没有 `timeout=` 参数** (PyMechanical 0.13.x): 传了直接 `TypeError:
  unexpected keyword argument 'timeout'`。冷启动要 30~50s 才就绪, 别加这个参数, 让它自己连。

## 2. Mechanical 内是 IronPython 2.7

- **禁用 f-string**: 所有传给 `run_python_script()` 的字符串用 `%` 格式化, 不要 `f"..."`。
- 字符串拼接进脚本时, 注意 `%` 转义 (模板里用 `CRIT_TPL % (...)` 注入坐标)。

## 3. 单位

- 探测返回的面质心坐标 = Mechanical **当前建模单位**。轴类零件通常是 **mm** (轴长 294 即 294mm,
  不是 294m)。误按米处理会把范围放大 1000 倍, 把整根轴所有面都选成"固定端"。
- 命名选择的坐标判据必须带单位: `Quantity("12.345000 [mm]")`。

## 4. 中文界面结果名

- 中文版 Mechanical 的结果对象名是 **总变形 / 等效应力** (不是 Total Deformation / Equivalent Stress)。
  按英文名去 `Solution.Children` 里匹配会失败。
- **正确做法**: 用对象引用读结果最大值 —— `td = solution.AddTotalDeformation(); es = solution.AddEquivalentStress()`
  然后读 `td.Maximum` / `es.Maximum`, 不依赖名字字符串。

## 5. 命名选择 (Named Selection) 多选面

- 用 worksheet 坐标范围选端面时, 容差太大(如 ±14.7mm)会把端部附近的**键槽/特征面**一并选入,
  固定支撑变成 3 个甚至更多面。收紧到端部 ±3mm 只取端面圆盘即可排除。
- 判据模板: `SelectionCriterionType.LocationX` (轴是 X 用 LocationX, 以此类推) +
  `SelectionOperatorType.RangeInclude` + 带 `[mm]` 的上下界 `Quantity`。

## 6. 两个"显示"是不同的 API (最容易混)

| 想要的效果 | 正确 API | 错误写法(在 PyMechanical 里会 FAIL) |
|---|---|---|
| 几何模型显示为**实体/线框** | `ExtAPI.Graphics.ViewOptions.ModelDisplay = ModelDisplay.ShadedExteriorAndEdges` | — |
| 结果云图上的**网格线(边)**隐藏 | `ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay = MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe` | `ExtAPI.Graphics.ShowMesh = False` |
| 同上(回退) | 直接赋整数 `0` (=NoWireframe) | `ds.Graphics.ResultPrefs.edgeDisplay = 0` |

- `ExtraModelDisplay` 取值: `0`=NoWireframe(无边框) / `1`=UndeformedWireframe(未变形线框) /
  `2`=UndeformedModel(未变形实体) / `3`=ShowElements(显示单元/网格线)。
- **为什么 `ShowMesh` 和 `edgeDisplay` 不行**: PyMechanical 的 `ExtAPI.Graphics` 是包装层,
  `MechanicalGraphicsWrapper` 没有 `ShowMesh` 属性; `ExtAPI.DataModel.InternalObject["ds"].Graphics`
  返回的是 `DispCallable` 包装, 没有 `ResultPrefs` 属性。所以这两条官方论坛写法只在 Mechanical **原生
  脚本窗口**有效, 经 gRPC 跨进程后这层 COM 不暴露。

## 7. 枚举符号作用域

- `MechanicalEnums` 在 Mechanical IronPython 里是**全局符号**, 直接可用。**不要** `import MechanicalEnums`
  (报 `No module named MechanicalEnums`)。`ModelDisplay` 同理是全局枚举, 直接用 `ModelDisplay.ShadedExteriorAndEdges`。

## 8. 存盘

- `ExtAPI.DataModel.Project.SaveAs(path)` **不能覆盖已存在**的 mechdat, 会报 `file already exists`。
  需要存盘时先 `System.IO.File.Delete` 删旧文件(连同 `*_files` 伴随目录和残留锁)再 SaveAs。
  录制/演示场景可整个跳过存盘(脚本里 `SAVE_ENABLED = False`)。

## 9. 官方 API 源码佐证 (本机安装目录)

- 几何显示模式: `aisol/DesignSpace/DSPages/Python/toolbar.py` 第 ~982 行 `SwitchModelDisplayOptions()`
  (用 `ModelDisplay.ShadedExteriorAndEdges` 裸全局枚举)。
- 结果"边"下拉(无边框/线框/实体/单元): 同一目录 `toolbar.py` 第 ~1332 行起, 对应
  `ExtAPI.Graphics.ViewOptions.ResultPreference.ExtraModelDisplay`。
- 安装根示例: `E:\ANSYS2024R2\ANSYS Inc\v242\aisol\DesignSpace\DSPages\Python\toolbar.py`
  (路径随你的安装盘符变化)。
