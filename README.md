# KuangK-vie-Video v1.01

一套把「文稿到画面到成片」和「成片到理解」两头打通的视频技能。基于花叔的 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)（MIT）复刻，补了文稿层和国产模型理解层。

## 三件事

**一、艺术动画。** 用代码（Canvas）画 35 种艺术风格并让画动起来。梵高、莫奈、敦煌、水墨、蒸汽波、吉卜力、包豪斯都在库里，还有 9 种解说动画语法（Kurzgesagt / Vox / 3b1b / 白板 / 财经图表那类）、8 种可按口播参数渲时长精确片段的库、长卷穿越片骨架。画面里要出现人时走 AI 生帧加代码合成。

**二、文稿升华（洗稿）。** 升华不是把词换一遍，是把稿子重新放回一个具体的人嘴里。材料关、说话位置、逐段推进、出声四步，配硬禁令十条和自动检查脚本。

**三、视频理解增强。** 让 Kimi、混元 Hy4、Bunny 这类国产模型把一段视频看准。做法是不让模型啃 mp4，先拆成它吃得下的包：元数据、分镜表、带时间码的关键帧、画面 OCR 文字，加一份按模型调好的提示脚手架。

## 装依赖

```sh
# 必需
winget install Gyan.FFmpeg                  # ffmpeg，出片、拆解、抽帧都要
uv run --with playwright playwright install chromium

# 可选，画面 OCR（中文效果好，不需要管理员权限）
pip install rapidocr-onnxruntime
```

## 用起来

```sh
# 渲一段艺术动画
E=<项目>/代码工程
uv run --with playwright python $E/render.py --out 成片.mp4 --audio 配乐.wav

# 把视频拆成国产模型读得懂的包
python scripts/vision/vid2pack.py --video 成片.mp4 --out 拆解包/ --model kimi

# 稿子交稿前查一遍
python scripts/text/polish_check.py 稿件.md
```

`vid2pack.py` 产出四样：`manifest.json`、`分镜表.md`、`frames/`（关键帧文件名带时间码）、`prompt_pack.md`。

## 目录

```
references/13-文稿升华与洗稿.md              文稿四步加硬禁令十条
references/14-国产大模型视频理解增强.md       元数据、镜头、帧、文字四层
references/15-模型适配卡.md                  Kimi / 混元 Hy4 / Bunny 喂法
scripts/text/polish_check.py               去 AI 味自动检查
scripts/vision/vid2pack.py                 视频理解包生成器
scripts/engine/                            上游渲染引擎（35 风格场景加语法库）
```

## 已知问题

上游引擎的本地服务原为单线程 `socketserver.TCPServer`，浏览器并发拉资源会被拒，表现为画面全黑加 `ERR_CONNECTION_REFUSED`。本版已改为 `ThreadingTCPServer`（`render.py`、`qa.py`）。从上游同步更新时会覆盖这个补丁，需要重打。

## 许可与署名

引擎、35 张风格配方卡、动画语法均来自 [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion)，作者 alchaincyf（花叔），MIT，许可见 `LICENSE`。文稿升华和视频理解增强两层为本项目新增。字体许可见 `scripts/engine/lib/fonts/LICENSES.md`。
