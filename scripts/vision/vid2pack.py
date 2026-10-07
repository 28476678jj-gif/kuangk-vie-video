#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""vid2pack · 把一段视频拆成国产大模型吃得下的理解包

产出四样东西
    manifest.json   机器读，喂给 Kimi / 混元 Hy4 / Bunny 的结构化输入
    分镜表.md       人和模型都能读的镜头表，带时间码
    frames/         带时间码的关键帧（每镜头代表帧 + 全局均匀采样）
    prompt_pack.md  按 --model 调好的提示脚手架，可直接粘贴

用法
    python vid2pack.py --video 参考.mp4 --out 拆解包/
    python vid2pack.py --video 参考.mp4 --out 拆解包/ --model kimi
    python vid2pack.py --video 参考.mp4 --out 拆解包/ --threshold 0.25 --no-audio

依赖 ffmpeg / ffprobe。OCR 依赖 tesseract，没装就跳过并在 manifest 里标注。
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 各模型的喂法上限。标【待实测】的数值按保守值先给，实测后回来改这里。
MODEL_PROFILES = {
    "kimi": {"max_frames": 12, "width": 768, "note": "长文本强，单帧细节弱。给文本包配少量帧。"},
    "hy4": {"max_frames": 16, "width": 1024, "note": "跟 schema 稳。输出要求回 JSON。"},
    "bunny": {"max_frames": 24, "width": 640, "note": "批量过帧做粗筛，读字不可用，靠 OCR 补。"},
}
DEFAULT_PROFILE = {"max_frames": 12, "width": 768, "note": "通用喂法。"}

# winget 装完 ffmpeg 之后，旧的 shell 里 PATH 还没刷新，兜底找一下
WINGET_FFMPEG_DIRS = [
    Path(r"C:\Users\28476\AppData\Local\Microsoft\WinGet\Packages"),
]


def find_tool(name):
    """找 ffmpeg / ffprobe，PATH 找不到就去 winget 目录里翻"""
    p = shutil.which(name)
    if p:
        return p
    exe = f"{name}.exe"
    for base in WINGET_FFMPEG_DIRS:
        if not base.exists():
            continue
        for hit in base.rglob(exe):
            if "bin" in hit.parent.name.lower():
                return str(hit)
    return None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          errors="replace", **kw)


def probe(ffprobe, video):
    r = run([ffprobe, "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", video])
    if r.returncode != 0:
        sys.exit(f"ffprobe 读不出这个视频：{video}\n{r.stderr[:300]}")
    d = json.loads(r.stdout)
    vs = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    if not vs:
        sys.exit("这个视频里没有视频流。")
    fps = 25.0
    rate = vs.get("r_frame_rate", "25/1")
    if "/" in rate:
        n, _, den = rate.partition("/")
        try:
            fps = float(n) / float(den) if float(den) else 25.0
        except ValueError:
            fps = 25.0
    duration = float(d.get("format", {}).get("duration", 0) or vs.get("duration", 0) or 0)
    return {
        "path": str(Path(video).resolve()),
        "duration": round(duration, 3),
        "fps": round(fps, 3),
        "width": int(vs.get("width", 0)),
        "height": int(vs.get("height", 0)),
        "has_audio": any(s.get("codec_type") == "audio" for s in d.get("streams", [])),
    }


def detect_cuts(ffmpeg, video, threshold):
    """返回切点时间列表（秒，不含 0）"""
    r = run([ffmpeg, "-hide_banner", "-i", video,
             "-filter:v", f"select='gt(scene,{threshold})',showinfo",
             "-f", "null", "-"])
    times = []
    for line in (r.stderr or "").splitlines():
        if "pts_time" in line:
            m = re.search(r"pts_time:([0-9]+\.?[0-9]*)", line)
            if m:
                t = float(m.group(1))
                if t > 0.04:
                    times.append(round(t, 3))
    return sorted(set(times))


def grab(ffmpeg, video, t, out_png, width):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    r = run([ffmpeg, "-v", "error", "-ss", f"{t:.3f}", "-i", video,
             "-frames:v", "1", "-vf", f"scale={width}:-1", "-y", str(out_png)])
    return r.returncode == 0 and out_png.exists()


_RAPID = None


def pick_ocr_backend(want):
    """挑一个能用的 OCR 后端，返回 (名字, 可用)

    rapidocr 走 pip 装（rapidocr-onnxruntime），中文效果好且不需要管理员权限；
    tesseract 走系统安装。都没有就返回 none，脚本不硬失败。
    """
    global _RAPID
    if want == "none":
        return ("none", False)
    if want in ("auto", "rapidocr"):
        try:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID = RapidOCR()
            return ("rapidocr", True)
        except Exception:
            if want == "rapidocr":
                return ("rapidocr", False)
    if want in ("auto", "tesseract"):
        if shutil.which("tesseract"):
            return ("tesseract", True)
    return ("none", False)


def ocr_frame(png, backend, lang="chi_sim+eng"):
    """识别一帧里的画面文字，返回字符串或 None"""
    if backend == "none":
        return None
    if backend == "rapidocr" and _RAPID is not None:
        try:
            res, _ = _RAPID(str(png))
            if not res:
                return None
            return " ".join(str(r[1]) for r in res).strip() or None
        except Exception:
            return None
    if backend == "tesseract":
        t = shutil.which("tesseract")
        if not t:
            return None
        r = run([t, str(png), "stdout", "-l", lang])
        if r.returncode != 0:
            return None
        return " ".join((r.stdout or "").split()).strip() or None
    return None


def main():
    ap = argparse.ArgumentParser(description="vid2pack · 视频理解包生成器")
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="auto",
                    choices=["auto", "kimi", "hy4", "bunny"])
    ap.add_argument("--threshold", type=float, default=0.30,
                    help="场景切分阈值，越小切得越碎，默认 0.30")
    ap.add_argument("--no-audio", action="store_true", help="不抽音轨")
    ap.add_argument("--no-ocr", action="store_true", help="不做画面 OCR")
    ap.add_argument("--ocr-backend", default="auto",
                    choices=["auto", "rapidocr", "tesseract", "none"],
                    help="OCR 后端，默认 auto（rapidocr 优先，其次 tesseract）")
    a = ap.parse_args()

    ffmpeg = find_tool("ffmpeg")
    ffprobe = find_tool("ffprobe")
    if not ffmpeg or not ffprobe:
        sys.exit("没找到 ffmpeg / ffprobe。先装 ffmpeg（winget install Gyan.FFmpeg），"
                 "新开一个终端再跑。")

    prof = MODEL_PROFILES.get(a.model, DEFAULT_PROFILE)
    video = a.video
    if not Path(video).exists():
        sys.exit(f"视频不存在：{video}")

    out = Path(a.out)
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"探测 {video}")
    meta = probe(ffprobe, video)
    print(f"  {meta['duration']}s  {meta['width']}x{meta['height']}  {meta['fps']}fps  "
          f"{'有音轨' if meta['has_audio'] else '无音轨'}")

    print(f"场景切分（阈值 {a.threshold}）")
    cuts = detect_cuts(ffmpeg, video, a.threshold)
    bounds = [0.0] + [t for t in cuts if t < meta["duration"]] + [meta["duration"]]
    shots = []
    for i in range(len(bounds) - 1):
        t0, t1 = bounds[i], bounds[i + 1]
        if t1 - t0 < 0.05:
            continue
        shots.append({"id": len(shots) + 1, "t0": round(t0, 3), "t1": round(t1, 3),
                      "duration": round(t1 - t0, 3)})
    if not shots:
        shots = [{"id": 1, "t0": 0.0, "t1": meta["duration"],
                  "duration": meta["duration"]}]
    print(f"  切出 {len(shots)} 个镜头")

    backend, do_ocr = pick_ocr_backend("none" if a.no_ocr else a.ocr_backend)
    if a.no_ocr:
        print("  按参数跳过画面 OCR")
    elif do_ocr:
        print(f"  画面 OCR 后端 {backend}")
    else:
        print("  没有可用的 OCR 后端，跳过画面 OCR"
              "（pip install rapidocr-onnxruntime 或装 tesseract 后可启用）")

    print("抽关键帧")
    for s in shots:
        mid = (s["t0"] + s["t1"]) / 2
        png = frames_dir / f"shot{s['id']:02d}_t{mid:.2f}.png"
        if grab(ffmpeg, video, mid, png, prof["width"]):
            s["keyframe"] = str(png.relative_to(out)).replace("\\", "/")
            s["ocr"] = ocr_frame(png, backend) if do_ocr else None
        else:
            s["keyframe"] = None
            s["ocr"] = None

    n_uniform = min(prof["max_frames"], max(4, len(shots) * 2))
    uniform = []
    dur = max(meta["duration"], 0.1)
    for i in range(n_uniform):
        t = dur * (i + 0.5) / n_uniform
        png = frames_dir / f"u{i:02d}_t{t:.2f}.png"
        if grab(ffmpeg, video, t, png, prof["width"]):
            uniform.append(str(png.relative_to(out)).replace("\\", "/"))
    print(f"  {len([s for s in shots if s.get('keyframe')])} 张镜头帧 + "
          f"{len(uniform)} 张均匀采样帧")

    audio_wav = None
    if meta["has_audio"] and not a.no_audio:
        wav = out / "audio_16k.wav"
        r = run([ffmpeg, "-v", "error", "-i", video, "-vn",
                 "-ac", "1", "-ar", "16000", "-y", str(wav)])
        if r.returncode == 0 and wav.exists():
            audio_wav = "audio_16k.wav"
            print("  音轨已抽出（16k 单声道，供后续 ASR）")

    manifest = {
        "generated_by": "KuangK-vie-Video v1.01 vid2pack",
        "model": a.model,
        "model_note": prof["note"],
        "video": meta,
        "shots": shots,
        "uniform_frames": uniform,
        "audio": audio_wav,
        "ocr_available": do_ocr,
        "ocr_backend": backend,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = ["| 镜号 | 起止 | 时长 | 关键帧 | 画面文字 |", "|---|---|---|---|---|"]
    for s in shots:
        kf = f"`{s['keyframe']}`" if s.get("keyframe") else "（抽帧失败）"
        txt = (s.get("ocr") or "")[:40].replace("|", "/")
        rows.append(f"| {s['id']} | {s['t0']:.2f} 到 {s['t1']:.2f} | "
                    f"{s['duration']:.2f}s | {kf} | {txt} |")
    (out / "分镜表.md").write_text(
        "# 分镜表\n\n" + "\n".join(rows) +
        f"\n\n共 {len(shots)} 个镜头，总长 {meta['duration']} 秒。\n"
        f"均匀采样帧 {len(uniform)} 张，见 frames/。\n", encoding="utf-8")

    schema = json.dumps({
        "shots": [{"id": 1, "t0": 0.0, "t1": 0.0, "画面内容": "",
                   "出现的文字": "", "可提炼的点": "", "对应口播": "",
                   "把握程度": "画面可见/推测"}],
        "整体判断": "", "存疑处": "",
    }, ensure_ascii=False, indent=2)
    prompt = f"""你是视频分析助手。下面是一段视频的结构化信息，请基于它回答问题。

## 视频元数据
时长 {meta['duration']} 秒，{meta['width']}x{meta['height']}，{meta['fps']} fps，{'有音轨' if meta['has_audio'] else '无音轨'}。

## 分镜表
{chr(10).join(rows)}

## 模型注意
{prof['note']}

## 要求
1. 每条结论必须带时间码。没有时间码的结论视为无来源，会被打回。
2. 区分「画面可见」和「推测」，这两类分开写。
3. 按下面的 schema 回 JSON，不要写散文。

{schema}
"""
    (out / "prompt_pack.md").write_text(prompt, encoding="utf-8")

    print()
    print(f"产出在 {out.resolve()}")
    for f in ["manifest.json", "分镜表.md", "prompt_pack.md", "frames/"]:
        print(f"  {f}")
    if not do_ocr:
        print("\n提示：装 OCR 后端后可以自动补画面文字（pip install rapidocr-onnxruntime），"
              "国产模型读画面小字普遍不准，这一层很值。")


if __name__ == "__main__":
    main()
