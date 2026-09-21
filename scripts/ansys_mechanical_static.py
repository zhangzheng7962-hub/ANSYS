# -*- coding: utf-8 -*-
# =============================================================================
#  Ansys Mechanical 静力学分析自动化模板 (PyMechanical 直连, 无需官方 MCP)
# =============================================================================
#  适用: Ansys 2024 R2 (v242) 及类似版本, 通过 ansys.mechanical.core 直接驱动
#        Mechanical (GUI 模式)。不依赖任何官方 MCP server, 纯 PyMechanical 库。
#
#  演示工况: 一根轴类零件 (STEP), 两端固定 + 中部 1000N 集中力,
#            求最大变形与等效应力, 结果云图以"无边框"显示(隐藏网格线)。
#
#  前提:
#    1) pip install ansys-mechanical-core
#    2) 本机已安装 Ansys, 并能找到 AnsysWBU.exe 的完整路径
#    3) 2024 R2 / v242 未打 SP05 时 gRPC 不支持安全连接 -> transport_mode="insecure"
#
#  用法:
#    python ansys_mechanical_static.py [HOLD_SECONDS] [STEP_DELAY]
#      HOLD_SECONDS : 求解后保持窗口可见的秒数 (录屏用, 默认 1800 = 30 分钟)
#      STEP_DELAY   : 每步停留秒数 (录屏看清过程, 默认 2s; 传 0 关闭延时)
# =============================================================================
import sys
import time
import traceback

# ============================ 1. 机器相关路径 (改成你自己的) ===================
STEP_PATH = r"D:\path\to\your_part.STEP"        # 待分析零件(STEP/IGES)
MECH_EXE = r"E:\ANSYS2024R2\ANSYS Inc\v242\aisol\bin\winx64\AnsysWBU.exe"  # Mechanical 可执行文件

HOLD_SECONDS    = int(sys.argv[1]) if len(sys.argv) > 1 else 1800
STEP_DELAY      = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
PRE_IMPORT_DELAY = 5.0   # 启动连接后停留, 录屏先看空窗口


def log(msg):
    print(msg, flush=True)


# ============================ 2. 启动 Mechanical ==============================
try:
    from ansys.mechanical.core import launch_mechanical
except Exception as e:
    log("[FATAL] import pymechanical 失败: %s" % e)
    sys.exit(2)

log("[1] 启动 Mechanical (GUI 模式)...")
log("[1] exe=%s" % MECH_EXE)
t0 = time.time()
try:
    # 2024 R2 (v242) 未打 SP05 -> 不支持安全 gRPC, 必须用 insecure 本地直连
    # 注意: launch_mechanical 不接受 timeout= 关键字参数 (PyMechanical 0.13.x)
    mech = launch_mechanical(batch=False, exec_file=MECH_EXE, transport_mode="insecure")
except Exception as e:
    log("[FATAL] launch_mechanical 失败: %s" % e)
    traceback.print_exc()
    sys.exit(3)
log("[1] OK 已启动并连接, 耗时 %.1fs" % (time.time() - t0))
log("[1] 停留 %.0f 秒(录屏: 先看空窗口)..." % PRE_IMPORT_DELAY)
time.sleep(PRE_IMPORT_DELAY)


def R(script, tag):
    """在 Mechanical (IronPython 2.7) 中执行脚本. 禁 f-string!"""
    try:
        r = mech.run_python_script(script)
        log("[%s] OK -> %s" % (tag, r))
        if STEP_DELAY > 0:
            time.sleep(STEP_DELAY)
        return r
    except Exception as e:
        log("[%s] FAIL -> %s" % (tag, e))
        return None


# ============================ 3. 建静力学分析 ================================
R(
    'analysis = Model.AddStaticStructuralAnalysis()\n'
    '"analysis={0}".format(analysis.Name)',
    "analysis",
)

# ============================ 4. 导入几何 + 实体显示 =========================
R(
    'geometry_import = Model.GeometryImportGroup.AddGeometryImport()\n'
    'fmt = Ansys.Mechanical.DataModel.Enums.GeometryImportPreference.Format.Automatic\n'
    'prefs = Ansys.ACT.Mechanical.Utilities.GeometryImportPreferences()\n'
    'prefs.ProcessNamedSelections = True\n'
    'geometry_import.Import(r"' + STEP_PATH + '", fmt, prefs)\n'
    '"bodies={0}".format(Model.Geometry.GetChildren(DataModelObjectCategory.Body, True).Count)',
    "import",
)

# 几何显示模式: ShadedExteriorAndEdges=实体+边 / ShadedExterior=纯实体 / Wireframe=线框
# (结果云图的边显示是另一个 API, 见 §10, 二者不要混)
R(
    'try:\n'
    '    ExtAPI.Graphics.ViewOptions.ModelDisplay = ModelDisplay.ShadedExteriorAndEdges\n'
    '    md = str(ExtAPI.Graphics.ViewOptions.ModelDisplay)\n'
    'except Exception as e1:\n'
    '    try:\n'
    '        ExtAPI.Graphics.ViewOptions.ModelDisplay = MechanicalEnums.Graphics.ModelDisplay.ShadedExteriorAndEdges\n'
    '        md = str(ExtAPI.Graphics.ViewOptions.ModelDisplay) + " (enum)"\n'
    '    except Exception as e2:\n'
    '        md = "FAIL: {0} | {1}".format(e1, e2)\n'
    '"ModelDisplay={0}".format(md)',
    "display",
)

# ============================ 5. 赋材料 ======================================
R(
    'body = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)[0]\n'
    'body.Material = "Structural Steel"\n'
    '"material={0}".format(body.Material)',
    "material",
)

# ============================ 6. 探测几何范围 (判断主轴与单位) ===============
PROBE = (
    'bodies = Model.Geometry.GetChildren(DataModelObjectCategory.Body, True)\n'
    'body = bodies[0]\n'
    'out = ""\n'
    'try:\n'
    '    gb = body.GetGeoBody()\n'
    '    xs=[]; ys=[]; zs=[]\n'
    '    for f in gb.Faces:\n'
    '        c = f.Centroid\n'
    '        try:\n'
    '            xs.append(c[0]); ys.append(c[1]); zs.append(c[2])\n'
    '        except:\n'
    '            xs.append(c.X); ys.append(c.Y); zs.append(c.Z)\n'
    '    out = "NFACES={0}|X={1:.6f},{2:.6f}|Y={3:.6f},{4:.6f}|Z={5:.6f},{6:.6f}".format('
    'len(xs), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))\n'
    'except Exception as e1:\n'
    '    try:\n'
    '        bb = body.GetGeoBody().BoundingBox\n'
    '        out = "BBOX|X={0:.6f},{1:.6f}|Y={2:.6f},{3:.6f}|Z={4:.6f},{5:.6f}".format('
    'bb.MinPoint.X, bb.MaxPoint.X, bb.MinPoint.Y, bb.MaxPoint.Y, bb.MinPoint.Z, bb.MaxPoint.Z)\n'
    '    except Exception as e2:\n'
    '        out = "PROBE_ERR|e1={0}|e2={1}".format(str(e1), str(e2))\n'
    'out'
)
probe_out = R(PROBE, "probe")

if not probe_out or ("X=" not in str(probe_out) and "BBOX" not in str(probe_out)):
    log("[FATAL] 几何探测失败, 无法判断轴向, 终止")
    sys.exit(4)

# 解析探测结果, 找出最长轴作为主轴
try:
    parts = {}
    for kv in str(probe_out).split("|"):
        k, v = kv.split("=", 1)
        parts[k] = v
    ranges = {}
    for ax in ("X", "Y", "Z"):
        lo_s, hi_s = parts[ax].split(",")
        ranges[ax] = (float(lo_s), float(hi_s))
    axis = max(ranges, key=lambda a: ranges[a][1] - ranges[a][0])
    lo, hi = ranges[axis]
    length = hi - lo
    log("[probe] 面数=%s  主轴=%s  长度=%.4f  各轴范围=%s"
        % (parts.get("NFACES"), axis, length, ranges))
except Exception as e:
    log("[FATAL] 解析几何范围失败: %s" % e)
    sys.exit(5)

if length <= 0:
    log("[FATAL] 几何长度异常")
    sys.exit(6)

# ============================ 7. 网格 =======================================
# 探测返回的坐标即 Mechanical 当前建模单位。轴类零件单位是 mm, 千万别按米处理!
elem_size_mm = max(length / 25.0, 0.5)   # 沿轴约 25 个单元
log("[unit] 几何坐标按 mm 处理: 轴长=%.3f, 单元尺寸=%.3f mm" % (length, elem_size_mm))
R(
    'mesh = Model.Mesh\n'
    'mesh.ElementSize = Quantity("' + ("%.4f" % elem_size_mm) + ' [mm]")\n'
    'mesh.GenerateMesh()\n'
    '"mesh: nodes={0}, elements={1}".format(mesh.Nodes, mesh.Elements)',
    "mesh",
)

# ============================ 8. 命名选择: 两端 + 中间 =======================
tol = max(0.05 * length, 1e-6)
mid = (lo + hi) / 2.0

CRIT_TPL = (
    'c = Ansys.ACT.Automation.Mechanical.NamedSelectionCriterion()\n'
    'c.Active = True\n'
    'c.Action = SelectionActionType.Add\n'
    'c.EntityType = SelectionType.GeoFace\n'
    'c.Criterion = SelectionCriterionType.Location%s\n'
    'c.Operator = SelectionOperatorType.RangeInclude\n'
    'c.LowerBound = Quantity("%.6f [mm]")\n'
    'c.UpperBound = Quantity("%.6f [mm]")\n'
    'ns.GenerationCriteria.Add(c)\n'
)

# 固定支撑只选两个端面圆盘。坐标范围法若容差太大, 会把端部附近的键槽/特征面一并
# 选入(多选成 3 个甚至更多面)。收紧到端部 +/-END_TOL mm 只取端面圆盘, 排除键槽面。
END_TOL = 3.0
ns_ends = (
    'ns = Model.AddNamedSelection()\n'
    'ns.ScopingMethod = GeometryDefineByType.Worksheet\n'
    + (CRIT_TPL % (axis, lo - 1e-6, lo + END_TOL))
    + (CRIT_TPL % (axis, hi - END_TOL, hi + 1e-6))
    + 'ns.Generate()\n'
    'ns.Name = "ShaftEnds"\n'
    'try:\n'
    '    n = len(list(ns.Location.Ids))\n'
    'except:\n'
    '    n = -1\n'
    '"NS ShaftEnds: faces={0}".format(n)'
)
R(ns_ends, "ns_ends")

ns_mid = (
    'ns = Model.AddNamedSelection()\n'
    'ns.ScopingMethod = GeometryDefineByType.Worksheet\n'
    + (CRIT_TPL % (axis, mid - tol, mid + tol))
    + 'ns.Generate()\n'
    'ns.Name = "MidBand"\n'
    'try:\n'
    '    n = len(list(ns.Location.Ids))\n'
    'except:\n'
    '    n = -1\n'
    '"NS MidBand: faces={0}".format(n)'
)
R(ns_mid, "ns_mid")

# ============================ 9. 边界条件: 两端固定 + 中间 1000N ============
# 力的方向取垂直于主轴的方向 (轴沿 X 则力沿 Y; 轴沿 Y 则力沿 Z)
force_comp = "ZComponent" if axis == "Y" else "YComponent"

bc = (
    'analysis = Model.Analyses[0]\n'
    'ns_end = [n for n in Model.NamedSelections.Children if n.Name == "ShaftEnds"][0]\n'
    'fixed = analysis.AddFixedSupport()\n'
    'fixed.Location = ns_end\n'
    'ns_mid = [n for n in Model.NamedSelections.Children if n.Name == "MidBand"][0]\n'
    'force = analysis.AddForce()\n'
    'force.Location = ns_mid\n'
    'force.DefineBy = LoadDefineBy.Components\n'
    'force.' + force_comp + '.Output.DiscreteValues = [Quantity("-1000 [N]")]\n'
    '"BCs: {0} on ShaftEnds, {1} on MidBand ({2} = -1000 N)".format('
    'fixed.Name, force.Name, "' + force_comp + '")'
)
R(bc, "bcs")

# ============================ 10. 求解 + 读结果 =============================
# 用对象引用读结果最大值, 规避中文界面下结果名("总变形"/"等效应力")匹配问题
log("[solve] 添加结果对象并开始求解...")
t1 = time.time()
solve_out = R(
    'analysis = Model.Analyses[0]\n'
    'solution = analysis.Solution\n'
    'td = solution.AddTotalDeformation()\n'
    'es = solution.AddEquivalentStress()\n'
    'analysis.Solve(True)\n'
    'solution.EvaluateAllResults()\n'
    '"SOLVED: MaxDef={0} | MaxEqvStress={1} | names={2}/{3}".format('
    'str(td.Maximum), str(es.Maximum), td.Name, es.Name)',
    "solve",
)
log("[solve] 耗时 %.1fs" % (time.time() - t1))

# ============================ 11. 显示云图 + 隐藏结果网格线 =================
# 结果云图上的网格线 = 结果的"边"(Edges) 显示, 由 ExtraModelDisplay 控制:
#   NoWireframe=无边框(隐藏网格线) / UndeformedWireframe=未变形线框 /
#   UndeformedModel=未变形实体 / ShowElements=显示单元(网格线)
# 注意: ExtAPI.Graphics.ShowMesh 与 ds.Graphics.ResultPrefs.edgeDisplay 在
#       PyMechanical 里均不可用(包装层不暴露), 必须用下面这条官方 API。
R(
    'solution = Model.Analyses[0].Solution\n'
    'c = solution.Children[solution.Children.Count - 1]\n'
    'c.Activate()\n'
    'rp = ExtAPI.Graphics.ViewOptions.ResultPreference\n'
    'try:\n'
    '    rp.ExtraModelDisplay = MechanicalEnums.Graphics.ExtraModelDisplay.NoWireframe\n'
    '    edge = str(rp.ExtraModelDisplay)\n'
    'except Exception as e1:\n'
    '    try:\n'
    '        rp.ExtraModelDisplay = 0\n'           # 0 = NoWireframe(枚举不可用时的回退)
    '        edge = str(rp.ExtraModelDisplay) + " (int)"\n'
    '    except Exception as e2:\n'
    '        edge = "FAIL: {0} | {1}".format(e1, e2)\n'
    '"contour activated: {0} | ExtraModelDisplay={1} (无边框=已隐藏结果网格)".format(c.Name, edge)',
    "contour",
)

# ---- 可选: 存盘 (SaveAs 不能覆盖已存在的 mechdat, 需先删; 不需要可跳过) ----
SAVE_ENABLED = False
if SAVE_ENABLED:
    R(
        'import System\n'
        'p = r"D:\\ansys_result\\shaft_static_result.mechdat"\n'
        'try:\n'
        '    if System.IO.File.Exists(p): System.IO.File.Delete(p)\n'
        'except: pass\n'
        'try:\n'
        '    for d in System.IO.Directory.GetDirectories(r"D:\\ansys_result", "shaft_static_result*"):\n'
        '        System.IO.Directory.Delete(d, True)\n'
        'except: pass\n'
        'try:\n'
        '    for f in System.IO.Directory.GetFiles(r"D:\\ansys_result", "shaft_static_result*.*"):\n'
        '        System.IO.File.Delete(f)\n'
        'except: pass\n'
        'ExtAPI.DataModel.Project.SaveAs(p)\n'
        '"project saved -> shaft_static_result.mechdat"',
        "save",
    )
else:
    log("[save] SKIPPED (SAVE_ENABLED=False)")

# ============================ 12. 保持窗口 + 退出 ============================
log("[DONE] 流程结束。Mechanical 将保持可见 %d 秒供查看结果..." % HOLD_SECONDS)
try:
    time.sleep(HOLD_SECONDS)
except KeyboardInterrupt:
    pass
log("[EXIT] done")
try:
    mech.exit()   # 正常关闭, 释放项目锁, 避免实例残留
    log("[EXIT] Mechanical 已关闭")
except Exception as ee:
    log("[EXIT] mech.exit 异常(忽略): %s" % ee)
