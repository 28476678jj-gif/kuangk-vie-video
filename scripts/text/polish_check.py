#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文稿升华检查器

按 references/13-文稿升华与洗稿.md 的硬禁令十条逐条扫一遍中文稿件。
脚本只能抓字面，翻案腔的改写变体和段落推进逻辑要人工过。

用法
    python polish_check.py 稿件.md [稿件2.md ...]
    python polish_check.py 稿件.md --json        # 机器可读输出

退出码
    0  没有硬命中
    1  存在硬命中，不能交稿
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 硬命中：命中即不能交稿
HARD_PATTERNS = [
    ("破折号", re.compile(r"——|—|–")),
    ("翻案腔", re.compile(
        r"不是.{1,12}而是|并非.{1,12}而是|不在于.{1,12}而在于|与其说.{1,12}不如说"
        r"|表面.{1,12}实际|看似.{1,12}实则|你以为.{1,12}其实|说到底|答案恰恰相反"
        r"|不重要.{1,8}重要的是")),
    ("黑话", re.compile(
        r"赋能|抓手|商业闭环|价值闭环|能力沉淀|拉通|底层逻辑|顶层设计|认知跃迁"
        r"|价值释放|能力建设|降本增效|内容矩阵|全链路|组合拳|打开想象空间"
        r"|结构性机会|关键命题|深层逻辑|技术底座|公共底座|技术主权|单点风险"
        r"|主脊柱|材料锚点|认知增量|迭代闭环")),
    ("模型路标词", re.compile(
        r"更微妙的是|还有一层|只说对了一半|值得注意的是|需要指出的是|从某种意义上说")),
    ("对话残留", re.compile(
        r"希望对你有帮助|这是个好问题|你想让我继续吗|让我知道|总体来说|综上所述")),
    ("动词名词化", re.compile(
        r"完成了对.{1,10}的(优化|改造|升级|梳理|整合)"
        r"|实现了.{1,10}的(提升|增长|突破|飞跃)"
        r"|进行了.{1,10}的(优化|调整|探讨|分析)")),
]

# 提醒：需要结合上下文判断，不直接判死
SOFT_PATTERNS = [
    ("冒号(仅原话可用)", re.compile(r"：|:")),
    ("抒情衣服词", re.compile(
        r"安放|抵达|微光|褶皱|丰盈|滚烫|轻盈|赤裸|剥开|锋利|坚硬|柔软")),
]

# 三项以上同构排比：同一行里出现 3 段以上用顿号或分号串起来的短语
SERIES_RE = re.compile(r"[^。！？；\n]{2,12}[、；](?:[^。！？；、；\n]{2,12}[、；]){2,}")

CODE_FENCE_RE = re.compile(r"^\s*```")
URL_RE = re.compile(r"https?://|www\.|[\w./-]+\.(?:py|js|md|json|sh|html)\b")


def scan_text(text, path):
    """返回 (hard_hits, soft_hits, skipped)"""
    hard, soft, skipped = [], [], []
    in_fence = False

    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue
        # 代码、网址、机器字段里的冒号不算
        machine_line = URL_RE.search(line) is not None or stripped.startswith("|")

        # 同一行同一规则命中 3 次以上，基本是在列举禁用词本身（规则文档），
        # 不是在正文里用它，跳过避免误伤
        line_rule_hits = {}
        for name, pat in HARD_PATTERNS:
            ms = list(pat.finditer(line))
            if ms:
                line_rule_hits[name] = ms
        for name, ms in line_rule_hits.items():
            if len(ms) >= 3:
                skipped.append({
                    "file": str(path), "line": lineno,
                    "rule": name, "hit": f"{len(ms)} 处（疑似词表行，已跳过）",
                    "context": stripped[:80],
                })
                continue
            for m in ms:
                hard.append({
                    "file": str(path), "line": lineno,
                    "rule": name, "hit": m.group(0),
                    "context": stripped[:80],
                })

        for name, pat in SOFT_PATTERNS:
            if name.startswith("冒号") and machine_line:
                continue
            for m in pat.finditer(line):
                soft.append({
                    "file": str(path), "line": lineno,
                    "rule": name, "hit": m.group(0),
                    "context": stripped[:80],
                })

        if SERIES_RE.search(line):
            soft.append({
                "file": str(path), "line": lineno,
                "rule": "三项以上同构排比", "hit": SERIES_RE.search(line).group(0)[:40],
                "context": stripped[:80],
            })

    return hard, soft, skipped


def main():
    ap = argparse.ArgumentParser(description="文稿升华检查器（去 AI 味硬禁令）")
    ap.add_argument("files", nargs="+", help="待检查的 .md / .txt 文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    all_hard, all_soft, all_skipped = [], [], []
    for f in a.files:
        p = Path(f)
        if not p.exists():
            print(f"文件不存在：{f}", file=sys.stderr)
            continue
        h, s, k = scan_text(p.read_text(encoding="utf-8", errors="replace"), p)
        all_hard += h
        all_soft += s
        all_skipped += k

    if a.json:
        print(json.dumps({"hard": all_hard, "soft": all_soft,
                          "skipped": all_skipped},
                         ensure_ascii=False, indent=2))
        return 1 if all_hard else 0

    print(f"扫了 {len(a.files)} 个文件")
    print()
    if all_hard:
        print(f"硬命中 {len(all_hard)} 条（不能交稿）：")
        for x in all_hard:
            print(f"  [{x['rule']}] {Path(x['file']).name}:{x['line']}  "
                  f"命中「{x['hit']}」")
    else:
        print("硬命中 0 条")

    print()
    if all_soft:
        print(f"需人工确认 {len(all_soft)} 条：")
        for x in all_soft:
            print(f"  [{x['rule']}] {Path(x['file']).name}:{x['line']}  "
                  f"命中「{x['hit']}」")
    else:
        print("需人工确认 0 条")

    print()
    if all_skipped:
        print(f"词表行跳过 {len(all_skipped)} 处（疑似在列举禁用词本身）：")
        for x in all_skipped:
            print(f"  [{x['rule']}] {Path(x['file']).name}:{x['line']}  {x['hit']}")

    print()
    if all_hard:
        print("结论：有硬命中，改到清零再交。")
        return 1
    print("结论：字面检查通过。翻案腔变体和段落推进仍需人工过一遍。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
