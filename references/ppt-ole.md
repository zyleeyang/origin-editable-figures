# 复制到 PowerPoint 并返回 Origin 编辑

## 目标和用户操作

目标是 PPT 中的 Origin **嵌入 OLE 对象**，双击可进入 Origin 编辑，结束后用“文件 → 退出并返回……”更新 PPT。嵌入的是副本，修改外部 OPJU 不等于自动更新 PPT。只有明确需要外部文件联动时才采用链接对象。[Origin OLE 文档](https://docs.originlab.com/origin-help/paste-embed-ole)

1. 在 Origin 激活图页，使用“编辑 → 复制页面”（Ctrl+J）。
2. 在 PPT 粘贴；如默认只成为图片，用“选择性粘贴 → Origin Graph Object / Origin 图形对象”。
3. 双击进入 Origin，改完后“退出并返回”以更新嵌入图。

“复制图为图片”、PNG、EMF、SVG、PDF 不能满足返回 Origin 的目标。即使 EMF 可在 PPT 拆为形状，也不是 Origin OLE。

## Ctrl+C 默认设置

用户要求将图页 Ctrl+C 设为“复制页面”时，在 Origin Preferences/Options → Page 页检查 Copy (Ctrl+C) 选择项；它是本机用户设置，不是每个 OPJU 随身携带的属性。保留已有用户偏好，别把图页脚本赋值误称为已永久设置。[Origin Page 选项](https://docs.originlab.com/origin-help/options-dialog-page-tab/)

在 Origin 2026 的一次验证中，`@CPP` 从 32 改为 0 后，Ctrl+C 对应复制页面，并通过新实例重开核验；这是版本相关的观察。先核对当前版本的实际选项，不无条件改注册表或抹掉其他位设置。用户要求设默认且当前授权充分时完成设置并核验；否则用显式“复制页面”完成当前复制。

程序可激活图页执行 `page.copy(OLE);`，或使用适用版本的 `g.copy_page('OLE')`，显式指定当前复制格式。[Origin 接口发布说明](https://cloud.originlab.com/ReleaseNotes/detail.aspx?id=2022b6ORG-25082)

## “灰色”“无反应”“只能粘图片”的排查

先复现指定图和复制路径，不直接归因于数据量或文件损坏：

- 图页是否激活？是否仍在文本、单元格或对象编辑状态？
- 实际是复制页面还是复制图片？Ctrl+C 当前映射是什么？
- 剪贴板是否含 `Embed Source`、`Object Descriptor` 等对象格式？只有位图/EMF 不能说明有 OLE。
- PPT 是否在可编辑幻灯片中？先在自己新建的临时演示文稿测试，避免动用户现有内容。
- 图是否使用 Origin Master Page/Master Items？官方说明其 OLE 不受支持，含 master items 的图可能转成图片；保留 OLE 时在副本改用普通原生图页对象并验证。[Origin 发布与导出](https://docs.originlab.com/user-guide/publishing-and-export/)
- 显式 OLE 复制与临时 PPT 测试仍失败，才进一步查 COM/OLE 注册、版本和安装。修复安装、系统注册或重启须依据实际故障和授权，不作为常规建图步骤。

## 自动化验收

Windows PowerPoint 中 `Shapes.PasteSpecial(10)` 尝试 OLE 粘贴。核对 shape 的 `Type == 7`（嵌入 OLE）以及 `OLEFormat.ProgID` 为 Origin 图形类。一种已验证值为 `Origin95.Graph`；版本可能不同，不要求所有机器同一 ProgID。

将“剪贴板有对象格式”“PPT 得到 OLE”“激活后改动并回写成功”分开记录，做到哪一步报告哪一步。双击验证可在测试 deck 上激活 OLE、做可恢复的小样式修改、退出返回并确认更新。涉及 PPT 读写时使用当前环境的 presentations skill（若可用）。

测试只关闭自己新建的演示文稿，不退出用户 PowerPoint。剪贴板会被临时替换：能保留原 OLE 数据对象时先保留，只在剪贴板序列号仍是本次写入时恢复，避免覆盖用户新复制的内容。不能把仅保存图片称为完整剪贴板备份。

未实际测试时提供复制步骤和未验收范围，不宣称已解决本机 OLE 故障。
