# Origin 可编辑科研作图

把科研数据、参考样式或已有 Origin 图，整理成带有绘图数据、可继续编辑的 Origin / OriginPro 原生项目。

**技能名：`origin-editable-figures`**

![GO enrichment example](examples/go-enrichment/preview.png)

## 能做什么

- 根据数据和参考图创建原生可编辑图，分别调整数据点、线、误差线、坐标轴、图例和文字。
- 整理 PCA、t-SNE、UMAP 等科研图，核对坐标、分组、配色与数据来源。
- 将选定图页拆成独立 OPJU，携带必要数据，并保留已有样式。
- 按任务需要处理 Origin → PowerPoint 的 OLE 嵌入与回写核验。
- 保存后重新打开，核验数据绑定并从 Origin 导出预览。

参考图片用于指导外观。准确重建数据图需要对应数据；技能没有承诺从任意截图无损恢复原始数据。

## 使用条件

- 可以访问本机文件和桌面软件的 Codex。
- Windows，以及已安装、可正常运行的 Origin / OriginPro。
- 用于自动化的 Python 环境，安装 `originpro` 及本任务需要的数据处理依赖。
- PowerPoint 仅在需要 PPT 嵌入时使用。PPT 文件编辑可配合可用的演示文稿技能；本仓库不捆绑 PowerPoint 或其他技能。

本仓库的 GO 示例在 Windows、OriginPro 2026 和 Python 3.12 上验证。其他版本需要检查实际接口和导出效果。

## 安装技能

### 下载 ZIP

1. 在仓库页面点击 **Code → Download ZIP**，解压。
2. 将包含 `SKILL.md` 的整个文件夹改名为 `origin-editable-figures`。
3. 放入自己的用户目录：`.agents/skills/origin-editable-figures/`。
4. 在 Codex 中输入 `$origin-editable-figures`。如果尚未显示，重启 Codex。

Windows 下目录形如 `%USERPROFILE%\.agents\skills\origin-editable-figures\SKILL.md`。

也可以把本仓库地址提供给 Codex，让 `$skill-installer` 从该仓库安装。私有仓库需要先获得访问权限并登录自己的 GitHub 账号。

[Codex 官方技能安装与发现说明](https://learn.chatgpt.com/docs/build-skills)

### 配置 Python

在准备运行 Origin 自动化的同一个 Python 环境中执行：

```powershell
python -m pip install -r requirements.txt
```

技能文件和 Python 依赖分别安装。Origin 软件由使用者自行安装和配置。

## 在 Codex 中使用

提供数据文件与参考图，再输入：

> 用 `$origin-editable-figures`，根据这份数据和参考图制作可编辑的 Origin 图。保留原始数值和分组，每张图独立成页，保存后重新打开核验。

或：

> 用 `$origin-editable-figures`，从这个 OPJU 中将 GraphA 和 GraphB 拆成两个独立文件，保留样式和数据。

## 运行 GO 柱形图示例

示例数据包含 30 个 GO 条目，BP、CC、MF 各 10 个。数值用于演示作图，不在此执行 GO 富集分析。

在仓库目录执行：

```powershell
python scripts/plot_go_enrichment.py --input examples/go-enrichment/demo.csv --validate-only
python scripts/plot_go_enrichment.py --input examples/go-enrichment/demo.csv --output-dir outputs/go-demo
```

输出：

- `go_enrichment.opju`：一个图页、一个图层、三个原生柱形系列，内嵌数据。
- `go_enrichment.png`：从重开后的 Origin 项目导出的预览。
- `verification/verification.json`：数据与图形结构核验记录。

输出目录须为新目录或空目录。更换自己的数据时，支持 `.csv` 和 `.xlsx`，列名为 `GOterm`、`subgroup`、`Enrichment score`。组内保持输入顺序，图中按 BP、CC、MF 排列；不会自动筛选 Top N、重新排序或转换得分。三个分组都需要有数据，各组条目数可以不同。

`--label-size`、`--rotation`、`--page-width`、`--page-height`、`--y-max` 和 `--y-step` 可调整样式。修改条目数或名称长度后，需要检查预览中的文字和分组框。

完整参数：`python scripts/plot_go_enrichment.py --help`。

## 样式与视觉检查

技能按当前参考确定尺寸、字体、点线、配色和布局，先校准代表图，再批量制作。模型需要打开真实导出的预览，针对具体缺陷修正并重新检查；通过即可结束，没有固定检查轮数。小修改沿用已有文件，不重新设计整组图。

脚本的 `review_status` 将数据检查与视觉、交互编辑检查分开：脚本自动通过的数据核验，不会自动把后两项标为通过。成功导出PNG也不代表模型已经查看过它。程序退出状态和 `task_status` 只说明脚本运行情况，完整交付还需相应视觉及编辑验收。

[视觉检查流程](references/visual-quality.md)包含长标签、热图、ROC、散点及组图的检查方向；[样式记录示例](references/style-profile.example.json)用于保存当前任务的参数，不会被绘图脚本自动执行，也不是所有图的默认版式。

## 自动关闭与并行使用

示例脚本保存、重新打开核验和导出预览后，会关闭自己创建的独立 Origin 实例。核验记录包含该实例的 PID 和 `origin_session.exit_verified`；关闭失败不会报告任务完成。绘图报错、可捕获的 Ctrl+C、核验记录写入失败也会执行清理。需要继续编辑时，重新打开输出的 OPJU 即可。

其他项目可同时使用技能，但每个任务需要独立 Python 进程、Origin 实例和输出目录。不会附加或关闭你已打开的 Origin 项目，也不会强制结束未知进程。强制结束 Python 或 COM 卡死仍可能使清理无法执行，详见 [会话管理说明](references/origin-automation.md)。

更新前保留自己的修改；正在运行的脚本不会自动切换到新代码。已开始的 Codex 对话可能还持有旧说明，下次作图前让它重新读取技能即可，无需中断当前作图。

开发者可运行 `python -m unittest discover -s tests -v` 检查异常清理逻辑；这些单元测试不代替实际 Origin 验证。

## 在 Origin 中继续编辑

- `GOData` → `PlotData` 中的 BP / CC / MF 列控制柱高；空白表示该条目不属于相应系列。
- `Tick label` 列控制横轴显示文字，带有 Origin 颜色格式。保留格式，修改其中的名称即可。
- `Source` 表是原始输入快照。绘图修改使用 `PlotData` 表。
- 双击柱形调整系列样式；双击坐标轴调整范围和刻度。分组框、分组名称与纵轴标题均可编辑。
- 图例关联三个数据系列；外部 OPJU 与 PPT 中的嵌入副本不会自动同步。

## 仓库内容

| 文件或目录 | 用途 |
| --- | --- |
| `SKILL.md` | 技能入口与工作规则 |
| `agents/openai.yaml` | Codex 界面名称与调用提示 |
| `references/` | 原生绘图、降维、GO 示例与 PPT 嵌入说明 |
| `scripts/plot_go_enrichment.py` | 可配置输入路径的 GO 作图示例 |
| `scripts/extract_graph_pages.py` | 从已有项目拆出独立图页 |
| `scripts/origin_session.py` | 独立实例的关闭、退出核查及异常清理 |
| `examples/go-enrichment/` | 示例数据和原生导出预览 |

上传版不依赖作者机器的用户名、软件安装目录或研究项目路径。
