#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按需拉取渲染引擎（scripts/engine）

完整引擎含 16MB 中文字体，整体约 23MB，超过 SkillHub 的 10MB 发布上限，
所以发布包里不带引擎，用这份脚本按需拉。引擎来自上游
huashu-art-motion（MIT，作者 alchaincyf / 花叔），拉完会自动打上
ThreadingTCPServer 补丁（修浏览器并发拉资源被拒导致的黑画布）。

用法
    python scripts/setup_engine.py              # 拉到本脚本所在 skill 的 scripts/engine
    python scripts/setup_engine.py --force      # 已存在也覆盖

网络走环境变量里的代理（HTTP_PROXY / HTTPS_PROXY），国内网络通常要配。
"""

import argparse
import io
import os
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

UPSTREAM_TARBALL = (
    "https://codeload.github.com/alchaincyf/huashu-art-motion"
    "/tar.gz/refs/heads/main"
)
ENGINE_SUBPATH = "scripts/engine"

# 上游 bug：单线程服务扛不住浏览器并发连接
PATCHES = [
    ("scripts/engine/render.py",
     "srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))",
     "srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))\n"
     "srv.daemon_threads = True"),
    ("scripts/qa.py",
     "srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root))); port = srv.server_address[1]",
     "srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Q, directory=str(root)))\n"
     "srv.daemon_threads = True; port = srv.server_address[1]"),
]


def download(url):
    print(f"下载 {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "kuangk-vie-video"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser(description="拉取 KuangK-vie-Video 渲染引擎")
    ap.add_argument("--force", action="store_true", help="已存在也覆盖")
    a = ap.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    dest = skill_root / "scripts" / "engine"
    if dest.exists() and not a.force:
        print(f"引擎已经在了：{dest}")
        print("要重装加 --force")
        return 0

    raw = download(UPSTREAM_TARBALL)
    print(f"下载完成 {len(raw) / 1048576:.1f} MB，解包中")

    tmp = skill_root / "scripts" / "_engine_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
            members = [m for m in tf.getmembers()
                       if (m.name.split("/", 2)[-1].startswith(ENGINE_SUBPATH)
                           or "/" + ENGINE_SUBPATH + "/" in "/" + m.name)]
            if not members:
                print("压缩包里没找到 scripts/engine，上游目录结构可能变了", file=sys.stderr)
                return 1
            tf.extractall(tmp, members=members)

        extracted = None
        for p in tmp.rglob("engine"):
            if p.is_dir() and (p / "render.py").exists():
                extracted = p
                break
        if not extracted:
            print("解出来的目录里没有 render.py", file=sys.stderr)
            return 1

        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(extracted), str(dest))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    patched = 0
    for rel, old, new in PATCHES:
        f = skill_root / rel
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        if old in t:
            f.write_text(t.replace(old, new), encoding="utf-8")
            patched += 1
            print(f"  已打补丁 {rel}")

    print()
    print(f"引擎就位：{dest}")
    print(f"补丁 {patched}/{len(PATCHES)} 处")
    print()
    print("下一步：")
    print("  uv run --with playwright playwright install chromium")
    print("  uv run --with playwright python scripts/engine/render.py --solo 01_cave "
          "--stills 0,0.3 --out 渲染/01_cave")
    return 0


if __name__ == "__main__":
    sys.exit(main())
