# Origin 可编辑科研作图

根据科研数据、参考样式或已有 Origin 项目，创建和修改 **Origin / OriginPro 原生可编辑图**，保留绘图数据，核对数值与样式，并按需要交付独立图页或可在 PowerPoint 中返回 Origin 编辑的对象。

**技能名：`origin-editable-figures`**

适用于多种科研图的制作、样式复现和后续编辑。GO 分组柱形图是仓库中的一个可运行示例；技能的工作范围由当前数据、图型和交付要求决定。

## 适用任务

| 任务 | 提供什么 | 技能处理的重点 |
| --- | --- | --- |
| 根据数据和参考图作图 | 数据表、参考图片或原生项目、所需样式 | 核对列和单位，选择原生图型，调整坐标轴、配色、图例和文字 |
| 散点与降维图 | XY 坐标、样本和分组；需要分析时另提供原始数据与方法 | 样本映射、PCA/t-SNE/UMAP 坐标、点样式及椭圆含义 |
| 折线、时间序列与 ROC 曲线 | 曲线数据、系列名称和已有统计结果 | 曲线顺序、范围、参照线、单位和指标标签 |
| 柱形图与误差线 | 类别、数值、分组和误差定义 | 组序、系列颜色、误差范围与长标签；可用于富集结果等数据 |
| 热图 | 数值矩阵、行列标签、色标要求 | 行列对应、缺失值、色标范围及格内数字的可读性 |
| 修改或拆分已有图 | 最新保存的 OPJU 和具体修改要求 | 保留用户已有调整，局部修改，或把选定图页另存为独立 OPJU |
| Origin → PowerPoint | 原生图和组装要求 | Origin OLE 嵌入、实际页面检查及编辑回写；复杂组图可配合 `origin-ppt-assembly` |

这是供 Codex 使用的技能：它依据当前任务编写或调整 Origin 自动化流程。仓库内的固定脚本覆盖 GO 示例和图页提取，其他图型需要按实际 Origin 接口适配、运行和验收。参考图片提供外观依据；准确绘图仍需要对应数值，不能从任意截图无损恢复原始数据。

## 通常怎样完成一张图

1. **确认数据与样式**：读取数据、分组及单位；从参考图或原生文件确定尺寸、字体、点线、轴和布局。只改样式时保留已有数值和统计结果。
2. **制作原生图**：把必要数据写入 Origin 项目，建立可分别编辑的数据系列、坐标轴、图例和文字。批量新图先校准代表图。
3. **查看实际预览并修正**：从 Origin 导出并打开预览，检查长标签、遮挡、裁切和对齐；有具体问题时修改后复查，通过即可结束，没有固定检查轮数。
4. **重开核验与交付**：重新打开 OPJU，核对数据绑定、图页结构和所需编辑能力，交付文件与必要说明，关闭本任务创建的 Origin 实例。

常见交付为 OPJU、预览图和简短使用说明。独立单图、批量选图页、PPT/OLE 或额外导出格式按任务需要提供。

## 使用条件

- 可以访问本机文件和桌面软件的 Codex。
- Windows，以及已安装、可正常运行的 Origin / OriginPro。
- 用于自动化的 Python 环境，安装 `originpro` 及本任务需要的数据处理依赖。
- PowerPoint 仅在需要 PPT 嵌入时使用。本仓库不捆绑 PowerPoint 或其他技能。

已验证的自动化环境包括 Windows、OriginPro 2026、Python 3.12 和 originpro 1.1.15。其他版本需要核对实际接口和导出效果；运行环境验证不等于每一种图型都已在该版本测试。

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

将自己的数据和参考文件提供给 Codex，并描述图型、样式和所需输出。例如：

> 用 `$origin-editable-figures`，根据这份 XY 数据和分组表，按参考图的配色与布局制作可编辑散点图。保留数值和样本对应关系，每张图独立成页，保存后重新打开核验。

> 用 `$origin-editable-figures`，把这份曲线数据画成 Origin 折线图，使用参考图的线型、坐标轴和图例。保留曲线原始坐标，并提供实际 Origin 导出预览。

> 用 `$origin-editable-figures`，把这份矩阵制作成可编辑热图。保留行列顺序和数值，按参考图设置色标，并检查长名称与格内数字。

> 用 `$origin-editable-figures`，仅修改这个 OPJU 的字体和线宽，保留我已经调整的配色、位置和轴范围；然后将 GraphA 和 GraphB 拆成独立文件。

## 质量检查与后续编辑

数据正确性、视觉质量和原生可编辑性分别验收。文件保存成功或成功导出 PNG，均不能代替实际看图；PPT 获得 Origin 嵌入对象，也不等于已经验证双击编辑回写。

配套脚本的 `review_status` 将数据检查与视觉、交互编辑检查分开；未执行的检查保持 `not_tested`。详细检查方法见 [样式、预览与修正](references/visual-quality.md)。[样式记录示例](references/style-profile.example.json)只展示记录格式，不会被绘图脚本自动执行，也不是统一默认版式。

在 Origin 中，可通过图的工作表修改绘图数据，双击数据系列、轴、图例或文字调整对应对象。表名和列用途以当前交付说明为准；预计算坐标或曲线是否随源数据变化自动重算，需要单独确认。PPT 内嵌副本与外部 OPJU 不会自动同步。

## 自动关闭与并行使用

配套脚本保存、重开核验并导出预览后，会关闭自己创建的独立 Origin 实例，核查实际退出结果。异常和可捕获的中断也会执行清理；关闭失败不会报告任务完成。

其他项目可同时使用技能，每个任务应使用独立 Python 进程、Origin 实例和输出目录。不会附加或关闭已打开的用户项目，也不会强制结束未知进程。强制结束 Python 或 COM 卡死仍可能使清理无法执行，详见 [Origin 自动化与会话管理](references/origin-automation.md)。

更新前保留自己的修改。正在运行的脚本继续使用已加载的代码；已经读取旧技能说明的对话，在下次作图前重新读取即可。

## 可运行示例与参考

- [GO 分组柱形图示例](references/go-enrichment.md)：合成数据、运行命令、原生预览及编辑方法，演示分组柱形图这一种用法。
- [Origin 自动化](references/origin-automation.md)：独立实例、原生散点与曲线、图页提取、保存后重开核验。
- [降维、椭圆与选图交付](references/ordination-and-delivery.md)：坐标与样本映射、椭圆含义、本地选图页。
- [PowerPoint OLE](references/ppt-ole.md)：复制页面、原生嵌入与编辑回写的验证边界。

| 文件或目录 | 用途 |
| --- | --- |
| `SKILL.md` | 通用技能入口与工作规则 |
| `agents/openai.yaml` | Codex 界面名称与调用提示 |
| `references/` | 按任务选读的工作方法与示例 |
| `scripts/extract_graph_pages.py` | 从已有项目提取独立图页 |
| `scripts/origin_session.py` | 独立实例的关闭、退出核查及异常清理 |
| `scripts/plot_go_enrichment.py` | GO 分组柱形图的专项示例脚本 |
| `examples/go-enrichment/` | 合成演示数据和对应的 Origin 原生导出预览 |
| `tests/` | 会话清理逻辑的单元测试 |

开发者可运行 `python -m unittest discover -s tests -v`；单元测试不代替实际 Origin 验证。

## 数据与发布边界

- 当前演示数据使用明确标注的虚构条目和人为设置的数值，不代表真实实验、真实 GO 条目或富集分析结论。
- 使用自己的数据时，建议把输入、输出和核验记录放在仓库外。OPJU、PPT、预览图和日志也可能包含数据、样本名称或本机路径，需要作为数据文件审查。
- 账号凭据、API 密钥、环境配置和私人研究文件不应提交到仓库。凭据由使用者在本机配置；技能不要求作者的账号、安装目录或研究项目路径。
- `.gitignore` 降低误提交风险，不能移除已跟踪文件或 Git 历史内容。分享或更新仓库前检查实际提交文件和示例来源；曾公开的凭据需要撤销，删除当前文件不能使旧凭据失效。
