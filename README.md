# KuangK-vie-Video v1.01

用代码画 35 种艺术风格并让画动起来，把 AI 味的稿子改回人话，让 Kimi / 混元 Hy4 / Bunny 把一段视频真正看懂。

基于花叔的 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)（MIT）复刻，补了文稿层和国产模型理解层。

## 你能拿它做什么

**给一段口播做艺术动画。** 你说主题，它出分镜、定风格、用 Canvas 把画面画出来并让画面动起来。梵高的星空真的在转，莫奈的水面真的在荡。支持抖音、小红书、B站、视频号、公众号、YouTube 这些平台的画幅和节奏。

**把一段动画复刻成自己的。** 丢一个参考视频进去，它拆出场景骨架、运动规律和转场语言，再用代码重写一遍。学的是机制，不是逐像素抄。

**把稿子从 AI 味里捞出来。** 材料关、说话位置、逐段推进、出声，四步走完再交。硬禁令十条加自动检查脚本，命中一条就不许交稿。

**让国产模型看懂一段视频。** Kimi、混元 Hy4、Bunny 直接啃 mp4 基本只能给出一句笼统描述，时间码全靠编。这个技能先把视频拆成元数据、分镜表、带时间码的关键帧、画面 OCR 文字，再配一份按模型调好的提示脚手架喂进去。

## 三块能力

**一、艺术动画。** 35 种艺术风格（岩洞壁画、古埃及、希腊、哥特、文艺复兴、印象派、立体主义、水墨、敦煌、克里姆特、蒙克、草间弥生、达利、霍珀、吉卜力、蒸汽波、漫威 Kirby、修拉、马蒂斯、哈林、伦勃朗、橡皮管卡通、皮影、新海诚、毕加索蓝色时期等），9 种解说动画语法（Kurzgesagt / Vox / 3b1b / 白板 / 动态文字 / storytime / 发布会 / 财经图表），8 种可按口播参数渲时长精确片段的库，长卷穿越片骨架。画面里要出现人时走 AI 生帧加代码合成。

**二、文稿升华（洗稿）。** 升华不是同义词替换，是把稿子放回一个具体的人嘴里。配 `polish_check.py` 自动检查，翻案腔、破折号、黑话、模型路标词、对话残留逐条扫，硬命中清零才交。

**三、视频理解增强。** `vid2pack.py` 一条命令出四样东西：`manifest.json`（机器读）、`分镜表.md`（人和模型都能读）、`frames/`（关键帧文件名带时间码）、`prompt_pack.md`（按模型调好的提示脚手架）。三个模型有各自的喂法卡：Kimi 长文本强做归纳，混元 Hy4 跟 schema 稳做结构化分镜，Bunny 批量过帧做粗筛。

## 五分钟跑起来

```sh
# 1. 装依赖
winget install Gyan.FFmpeg                                   # ffmpeg，必需
uv run --with playwright playwright install chromium         # 渲染用的浏览器
pip install rapidocr-onnxruntime                             # 画面 OCR，可选但很值

# 2. 精简包要先拉一次引擎（含中文字体，共约 23MB）
python scripts/setup_engine.py

# 3. 渲一段看看
uv run --with playwright python scripts/engine/render.py \
  --solo 01_cave --stills 0,0.3 --out 渲染/01_cave

# 4. 把成片或参考片拆成国产模型读得懂的包
python scripts/vision/vid2pack.py --video 成片.mp4 --out 拆解包/ --model kimi

# 5. 稿子交稿前查一遍
python scripts/text/polish_check.py 稿件.md
```

## 目录

```
SKILL.md                                    路由，先判断任务走哪条
references/13-文稿升华与洗稿.md              文稿四步加硬禁令十条
references/14-国产大模型视频理解增强.md       元数据、镜头、帧、文字四层
references/15-模型适配卡.md                  Kimi / 混元 Hy4 / Bunny 喂法
references/01-12*, 动画语法/, 风格配方/      上游的拆解、机制、语法与 35 张配方卡
scripts/text/polish_check.py               去 AI 味自动检查
scripts/vision/vid2pack.py                 视频理解包生成器
scripts/setup_engine.py                    按需拉引擎并自动打补丁
scripts/engine/                            渲染引擎（35 风格场景加语法库，拉完才有）
```

## 常见情况

**引擎没随包附带。** 完整引擎含 16MB 中文字体，整体约 23MB，超过 SkillHub 的 10MB 发布上限，所以精简包不带。跑 `python scripts/setup_engine.py` 即可，脚本会自动取引擎并打上 `ThreadingTCPServer` 补丁。GitHub 这个仓库里引擎是完整的，直接 clone 就有。

**画面全黑只剩角标。** 上游引擎的本地服务是单线程 `socketserver.TCPServer`，浏览器并发拉资源会被拒。本版已改成 `ThreadingTCPServer`。如果你同步了上游更新，补丁会被覆盖，需要重打。

**OCR 没生效。** 装 `rapidocr-onnxruntime`（pip，中文好，不需要管理员权限）或系统装 tesseract，任一在场就自动启用。两个都没有时脚本跳过并在 `manifest.json` 里标 `ocr_backend: none`，不会硬失败。tesseract 在 Windows 上要管理员权限，装不上就用 rapidocr。

**模型规格没写全。** `15-模型适配卡.md` 里标【待实测】的是上下文上限、单次图片张数这些本机验证不了的项目。你实测完请把卡改对。

## 依赖

`uv`、ffmpeg、Playwright Chromium 是必需的。OCR（rapidocr-onnxruntime 或 tesseract）可选。

## 许可与署名

引擎、35 张风格配方卡、动画语法来自 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)，作者 alchaincyf（花叔），MIT，见 `LICENSE`。文稿升华和视频理解增强两层为本项目新增。字体许可见 `scripts/engine/lib/fonts/LICENSES.md`。
