# KuangK-vie-Video v1.01 · 2026-10-07

复刻自 huashu-art-motion（作者 alchaincyf / 花叔，MIT），保留引擎、35 张风格配方卡与 9 种动画语法，新增两层能力。

- 新增文稿升华（洗稿）层：`references/13-文稿升华与洗稿.md`，含材料关、说话位置、逐段推进、出声四步，以及硬禁令十条；配 `scripts/text/polish_check.py` 自动检查（翻案腔、破折号、冒号、黑话、路标词、对话残留、动词名词化）。同一行同一规则命中 3 处以上判为词表行并跳过，避免扫规则文档时误报。
- 新增视频理解增强层：`references/14-国产大模型视频理解增强.md`（元数据、镜头、帧、文字四层）与 `references/15-模型适配卡.md`（Kimi / 混元 Hy4 / Bunny 各自的喂法与短板，未实测项标【待实测】）。
- 新增 `scripts/vision/vid2pack.py`：视频拆成理解包，输出 manifest.json、分镜表.md、带时间码的关键帧、按模型调好的 prompt_pack.md。支持 `--model kimi|hy4|bunny` 调帧数与分辨率，OCR 双后端（`--ocr-backend auto|rapidocr|tesseract|none`），都不在场时跳过不失败。
- OCR 实测（2026-10-07）：用 0.5 秒洞穴壁画样片跑通，rapidocr 从镜头帧里认出「40,000 Cavepainting TEA ACROSS THE AGES」。tesseract 在本机装不上（winget 包是 GUI 交互安装器需提权，choco 依赖冲突），改用 pip 装 rapidocr-onnxruntime，中文效果更好且不需要管理员权限。
- 修上游 bug：引擎本地服务 `socketserver.TCPServer` 改为 `ThreadingTCPServer`（render.py、qa.py），修掉浏览器并发拉资源被拒导致的黑画布。
- SKILL.md 重写为三能力路由（艺术动画 / 文稿升华 / 视频理解增强），并加了三条串起来的标准走法。

# 发布包更新 · 2026-10-06

- 同步35种当前艺术风格目录和第9种讲解员语法；8种语法仍提供参数化片段。
- 加入口播整片代码快照、文字框景QA和浅底字幕区检查；说明需自备素材的范围。
- 私人反馈、角色源提示词、未公开依赖与开发Git历史不随包发布。
- 保留公开副本的思源黑体、原创示例配乐和角色使用边界；补齐第三方笔顺数据许可。

# CHANGELOG

- 2026-10-04 v0.1 · 从「艺术史速通」复刻沉淀：拆解法（01）、五层机制（02）、一帧先行四路线（03）、纯代码绘制（04）、节奏与配乐（05）、口播驱动草案（06）；16 张风格配方卡；完整引擎＋16 个场景；breakdown.py 拆解脚本（网格拟合取「80% 内点下最大步长」）；key_green.py 保坐标抠图；音轨合成模板。
- 2026-10-04 v0.3 · 迁移测试 A–D 回流进库：lib 拆出 brush.js（毛笔飞白/墨晕/流线长笔/水彩/厚涂/剪刀折线）、render.js（照片网点/点彩/赛璐珞/Kirby 阴影/体积/长影子/双版本光影/光照图/皮影/手剪位移/霓虹）、post.js（VHS/胶片/泛光/光晕/纹理叠角色/褪色）；RIG.limb 端帽修正、猫身与白胸平滑、drawGirl/drawCat 分层钩子、非等比拉长、刚体枢轴；角标可插拔且转场中点硬切；转场按 eras 自动加载、缓存可按段；霞鹜文楷子集＋font_subset.py＋U.assertGlyphs（查 cmap）；20 段新风格进 scenes/，全风格样片 eras_gallery.js（36 段，?film=gallery）；qa 加转场冒烟、--film。
- 2026-10-04 v0.4 · YouTube 解说动画语法 8 种（Kurzgesagt / Vox / 白板 / storytime / 动态文字 / 3b1b / 发布会 / 财经图表）收进 skill：
  lib 新增 motion（MO）、camera（CAM）、diagram（DG）、typo（TY）、chart（CH）、ui（UI）、collage（CL）、toon（TOON）八个库；transitions.js 新增 13 个解说转场（same / lensReveal / matchCut / whip / smash / fillZoom / bands / push / zoomThrough / blurPush / expandRect / slidePush / fadeShift）；
  引擎支持 window.BPM、段写 dur（秒）、transition.punch / window.PUNCH、SCENE_LIBS / SCENE_DIR、?film=demos/<语法>；8 支示范片进 demos/（与实验原片逐像素一致）；
  参数化片段 clip.html＋clips/<语法>.js＋render.py --spec（时长精确、竖屏、--alpha 出 ProRes 4444），给口播管线当动画段，8 份样例在 engine/examples/；
  字体：普惠体四字重与霞鹜文楷扩到 GB2312 全部汉字（font_subset.py --gb2312），CMU / Inter / Roboto Condensed / 思源子集；
  文档 references/09-视频动画语法.md（总览、选语法决策表、跨语法通用规律、库速查、片段契约），语法卡 8 张进 references/动画语法/、总览图进 assets/动画语法/。

- 2026-10-05 00:34:23 +0800：一支口播片实战回流：按解释任务混用Vox与3b1b、固定音轨字幕后重构画面，证据与边界见07号新条目。

- 2026-10-05 v0.5 · 开源整理：去掉本机路径与合作项目信息；中文黑体换成思源黑体 Noto Sans SC（family 名沿用 PuHui-*），补字体许可清单；全风格样片移到 Release；加 README / LICENSE。
- 2026-10-05 v0.6 · 开源第二轮：Vox 示范片的人物改用卡通帧，写实人像不再随仓库；配乐脚本换成原创示例乐谱，音轨文档改成「方法＋原创示例」；洞穴段标题换成原创文字；收进长卷穿越片示范 demos/long_scroll（骨架＋埃及、莫奈、8-bit 三段）与 11 号文档。
