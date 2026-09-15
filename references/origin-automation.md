# Origin 自动化与独立图页

## 运行环境和会话

在当前机器检查 Origin 安装、版本和可用 Python/`originpro`。Codex 桌面可用 `load_workspace_dependencies` 获取捆绑 Python；其他环境使用已配置的解释器。若项目有独立安装的 originpro，可在新脚本中将该目录加入 `sys.path`，不必修改全局 Python。

已验证环境包括 Windows、OriginPro 2026、originpro 1.1.15。其他版本按实际接口适配；不要将作者的目录或盘符当成依赖。仓库 `requirements.txt` 提供示例脚本所需的 Python 包。

`Origin.Application` 创建新实例，`ApplicationSI`/`op.attach()` 可接入用户现有实例。[Origin 官方会话说明](https://docs.originlab.com/com/difference-of-application-applicationsi-and-applicationcomsi/)

批量新建/复制项目使用独立实例，**保存、重开核验、导出预览后，默认关闭本次实例**。文件留在输出目录；不能因为要展示预览就把自动化项目一直留在 Origin 中。只有用户明确要求继续在该窗口编辑，或尚需完成 PPT/OLE 粘贴时，才保留所需会话并说明原因。

新脚本使用 [origin_session.py](../scripts/origin_session.py) 的 `OwnedOrigin`。先定位本技能实际目录，将其 `scripts` 加入 Python 的模块搜索路径（不要硬编码作者路径），在**新的外部 Python 进程**中执行：

```python
from pathlib import Path
import originpro as op
from origin_session import OwnedOrigin

report = {}
with OwnedOrigin(op, report=report, report_path=Path('output/verification/session.json')):
    op.new()
    # 在独立实例中打开源项目、编辑、另存、重开核验和导出预览。
    # 必须检查 save/open/export 的结果；退出不会自动保存未保存的改动。
# 到这里才确认退出完成，或抛出明确的清理错误。
```

- 上下文内部不要另行 `attach()`、`detach()`、`exit()`，也不要替换全局连接。此 helper 拒绝复用同一 Python 进程里已存在的连接，也拒绝在 Origin 内置 Python 中运行；每个并行任务使用自己的 Python 进程及输出目录。
- helper 从它创建的 Origin 内部读取 PID，并持有该进程的只读等待句柄；不会用“新增了哪个 Origin 进程”猜测归属，也不会批量结束 Origin。这样另一个任务同时启动/退出也不会被误判为本任务实例。
- 正常完成、绘图异常、`SystemExit` 和可被 Python 捕获的 Ctrl+C 都执行清理。**先退出并核查，再写核验记录**，磁盘/权限错误不能跳过关闭。退出错误或等待超时使任务失败；原有绘图错误也予以保留。报告中的 `origin_session.exit_verified` 为真才表示已确认退出。
- 退出后不要再调用 `op` 查询版本、图页或导出预览：originpro 的延迟连接可能因此再启动一个实例。所有这些操作放在上下文内。
- 已验证 Windows、OriginPro 2026、originpro 1.1.15。helper 需要可用的 Origin 内置 Python 来读取本实例 PID；若接口/权限不支持，会尝试关闭已创建实例并明确报错，不能退回去附加其他实例。
- Python 被强制结束、系统崩溃、或 COM 调用卡死时，`finally` 无法保证执行；15 秒是退出调用返回后的等待时限，不是 COM 调用的强制超时。留下的实例须先确认归属和未保存内容，不得自动清除未知进程。

会话退出接口依据 [Origin 外部 Python 示例](https://docs.originlab.com/externalpython/external-python-code-samples/)；退出可靠性须以实际进程核查为准。

不要对未确认归属的实例执行 `op.new()`、关闭项目或终止进程。只有用户要求操作活动会话时才附加；附加后结束自动化应使用 `op.detach()` 释放连接，不能使用 `OwnedOrigin` 或顺手退出用户程序。COM 启动错误时先区分沙箱启动限制、位数/依赖和 Origin 注册问题；有证据支持权限原因时通过平台权限机制重试，不反复杀进程或重装软件。

## 原生二维散点图配方

这是接口配方，按当前数据调整，不是固定样式模板。`coords` 包含固定绘制顺序的 X、Y，`palette` 是分组→色号映射：

```python
book = op.new_book('w', lname='Plot coordinates and sample mapping')
book.name = 'Coordinates'
w = book[0]
w.name = 'PlotA'
xy = coords[['Dim1', 'Dim2']].copy()
xy['RGB'] = coords['group'].map(palette).map(op.ocolor)
xy['sample'] = coords['sample'].astype(str)
xy['group'] = coords['group']
w.from_df(xy)
w.cols_axis('XYNNN')
g = op.new_graph(lname='Descriptive title', template='scatter')
g.name = 'PlotA'
l = g[0]
p = l.add_plot(w, 1, 0, type='s')  # 列索引从 0 开始：Y=1, X=0
p.color = op.color_col(1, 'r')     # RGB 紧接 Y 列；换列布局须复核
p.symbol_kind = 2
p.symbol_size = 2.6
p.transparency = 15              # 15% 透明，即 85% 不透明
p.set_cmd('-kf 0', '-kh 0', '-paas 1')
l.lt_exec('layer.showFrame=0;')
l.axis('x').title = 'Dimension 1'
l.axis('y').title = 'Dimension 2'
```

同层追加曲线，不为每条曲线创建新图层：

```python
# ew 交替存储 X1,Y1,X2,Y2,...；每组一条原生 line plot。
ep = l.add_plot(ew, 2*j+1, 2*j, type='l')
ep.color = colour
ep.set_cmd('-wp 1.2', '-d 0')
```

`-wp` 线宽单位为 point；`-w` 使用不同缩放单位，不直接互换。[LabTalk set 命令](https://docs.originlab.com/labtalk/ref/set-cmd/ja/)

风格示例：页面 200×225 mm、方形绘图区 150 mm、Arial 8–9 pt 轴标/图例、点 2.6 pt、曲线 1.2 pt。应按最终出版尺寸和密度调整。物理等比例绘图区还需对应数据跨度，不能仅令 width=height 就声称等数据单位。

CSV 的 ID 保留为字符串，数值使用足够精度（如 pandas `float_precision='round_trip'`）。列名要清楚，避免自动导入丢失特征名；存原始矩阵、坐标、分组映射和必要方法参数，使项目尽量自包含。

## 将已有图拎出来

优先加载源 OPJU 并另存，不用坐标表重画来替代用户调整过的图。源文件有用户更新时核验当前文件，不拿历史哈希阻止合法更新。

辅助脚本 [extract_graph_pages.py](../scripts/extract_graph_pages.py)：

```text
python extract_graph_pages.py --source source.opju --graphs GraphA GraphB --output-dir selected
python extract_graph_pages.py --dependency-path /path/to/originpro-parent --source source.opju --graphs GraphA --output-dir selected --previews
```

运行前定位实际解释器、脚本和源文件，替换示例路径。脚本用独立隐藏实例按图名输出 OPJU，保留所有非图页以避免盲删公式/数据依赖，重开核对图层、plot 绑定和全部普通工作表。已存在目标文件时停止，不覆盖。`--previews` 导出检查 PNG。

它提取**整张图页**，不会把多图层合并页自动拆成单层；不验证外部链接已内嵌，也不自动解析跨图对象依赖，复杂链接图要单独审查。缩小项目需先确认依赖，再删除无关表并重开比对。

## 保存与核验

- `op.save(path)` 后 `op.new(); op.open(path)`；检查返回值。
- `list(op.pages('g'))` 是图页；`list(g)` 是图层；`l.plot_list()` 是同层散点/曲线。不要混淆三种数量。
- 用 `w.to_df()` 比对样本和数据，用 `plot.obj.GetDatasetName()` 检查绑定。普通 Y 数据绑定可与 `w.obj.Columns(y_index).GetDatasetName()` 对照；X、误差列等按当前图型补查。
- `g.save_fig(path, ...)` 预览须来自重开后的 Origin 项目。若另用 matplotlib 输出选图预览，标明来源，并核对坐标/配色一致。
- 不要将核验用的临时样式改动保存进交付文件。可在工作副本改点大小/线颜色，确认其他对象不变，再恢复或丢弃核验会话。
