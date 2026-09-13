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
| `examples/go-enrichment/` | 示例数据和原生导出预览 |

上传版不依赖作者机器的用户名、软件安装目录或研究项目路径。
