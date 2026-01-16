#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute key summary statistics for zhipi_comments_dataset_github_polished.csv.

Usage:
  python compute_summary_stats.py \
    --input zhipi_comments_dataset_github_polished.csv \
    --output DATA_SUMMARY_REPORT.md

The script is intentionally dependency-light (pandas only) and writes a Markdown
report suitable for GitHub.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


def _pct(n: int, total: int) -> str:
    if total <= 0:
        return f"{n}"
    return f"{n} ({n / total * 100:.1f}%)"


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Render a simple Markdown table (no alignment control)."""
    def esc(x: Any) -> str:
        if x is None:
            return ""
        s = str(x)
        return s.replace("\n", " ").replace("|", "\\|")

    out: List[str] = []
    out.append("| " + " | ".join(esc(h) for h in headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(esc(v) for v in r) + " |")
    return "\n".join(out)


def _vc_table(series: pd.Series, total: int, top_n: int = 10, dropna: bool = False) -> str:
    vc = series.value_counts(dropna=dropna)
    if top_n is not None:
        vc = vc.head(top_n)
    rows = []
    for k, v in vc.items():
        label = "(missing)" if pd.isna(k) else str(k)
        rows.append([label, v, f"{v / total * 100:.1f}%"])
    return _md_table(["value", "n", "%"], rows)


def _num_describe(series: pd.Series, percentiles=(0.1, 0.25, 0.5, 0.75, 0.9, 0.95)) -> Dict[str, Any]:
    s = series.dropna()
    if len(s) == 0:
        return {"count": 0}
    desc = s.describe(percentiles=list(percentiles))
    # normalize keys for stable printing
    out: Dict[str, Any] = {}
    for k, v in desc.items():
        out[str(k)] = float(v) if isinstance(v, (int, float)) else v
    return out


def _num_table(name: str, d: Dict[str, Any]) -> str:
    if d.get("count", 0) == 0:
        return f"- `{name}`: no non-missing values."

    keys = ["count", "mean", "std", "min", "10%", "25%", "50%", "75%", "90%", "95%", "max"]
    rows = []
    for k in keys:
        if k in d:
            v = d[k]
            if k == "count":
                rows.append([k, int(round(v))])
            else:
                rows.append([k, f"{v:.3f}"])
    return _md_table([name, "value"], rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input CSV path")
    ap.add_argument("--output", required=True, help="Output Markdown report path")
    ap.add_argument("--top-n", type=int, default=10, help="Top-N categories to show")
    args = ap.parse_args()

    inp = Path(args.input)
    out = Path(args.output)

    df = pd.read_csv(inp)
    n = len(df)

    lines: List[str] = []
    lines.append("# 脂批数据集：关键汇总统计（Key Summary Statistics）")
    lines.append("")
    lines.append(f"- 数据文件: `{inp.name}`")
    lines.append(f"- 行数（批语单元）: **{n:,}**")
    lines.append(f"- 列数: **{df.shape[1]}**")
    lines.append(f"- `comment_id` 唯一值: **{df['comment_id'].nunique():,}**（重复: {n - df['comment_id'].nunique():,}）")
    lines.append("")

    # -------------------- A. Factual fields --------------------
    lines.append("## A. 文档结构与定位字段（factual）")
    lines.append("")

    for col in ["doc_part", "is_toc_entry", "section"]:
        if col in df.columns:
            lines.append(f"### `{col}`")
            lines.append("")
            lines.append(_vc_table(df[col], total=n, top_n=args.top_n, dropna=False))
            lines.append("")

    # Chapter coverage
    if "chapter_number" in df.columns:
        lines.append("### `chapter_number`（回目覆盖）")
        lines.append("")
        ch = df["chapter_number"]
        rows = [
            ["min", int(ch.min())],
            ["max", int(ch.max())],
            ["unique", int(ch.nunique(dropna=True))],
        ]
        lines.append(_md_table(["stat", "value"], rows))
        lines.append("")
        # comments per chapter top/bottom
        ccounts = df.groupby("chapter_number")["comment_id"].size().sort_values(ascending=False)
        top = ccounts.head(10)
        bot = ccounts.tail(10)
        lines.append("**每回批语条数（Top 10）**")
        lines.append("")
        lines.append(_md_table(["chapter_number", "n", "%"], [[int(i), int(v), f"{v/n*100:.1f}%"] for i, v in top.items()]))
        lines.append("")
        lines.append("**每回批语条数（Bottom 10）**")
        lines.append("")
        lines.append(_md_table(["chapter_number", "n", "%"], [[int(i), int(v), f"{v/n*100:.1f}%"] for i, v in bot.items()]))
        lines.append("")

    # Manuscript & type
    for col in ["manuscript_version", "comment_type", "label_norm"]:
        if col in df.columns:
            lines.append(f"### `{col}`")
            lines.append("")
            lines.append(_vc_table(df[col], total=n, top_n=args.top_n, dropna=False))
            lines.append("")

    if set(["manuscript_version", "comment_type"]).issubset(df.columns):
        lines.append("### `manuscript_version` × `comment_type`（交叉分布）")
        lines.append("")
        ct = pd.crosstab(df["manuscript_version"].fillna("(missing)"), df["comment_type"].fillna("(missing)"))
        # keep only the most frequent comment_type columns to limit width
        col_order = ct.sum(axis=0).sort_values(ascending=False).index.tolist()
        ct = ct[col_order]
        # limit to top 8 comment types to keep readable
        ct = ct.iloc[:, :8]
        rows = []
        for idx, row in ct.iterrows():
            rows.append([idx] + [int(x) for x in row.tolist()])
        lines.append(_md_table(["manuscript_version"] + list(ct.columns), rows))
        lines.append("")

    # -------------------- B. Deterministic derived --------------------
    lines.append("## B. 署名、日期与文本长度（derived; deterministic）")
    lines.append("")

    if "has_signature" in df.columns:
        signed_n = int(df["has_signature"].fillna(0).astype(int).sum())
        lines.append("### 署名识别概览")
        lines.append("")
        lines.append(_md_table(
            ["metric", "value"],
            [
                ["has_signature = 1", _pct(signed_n, n)],
                ["has_signature = 0", _pct(n - signed_n, n)],
            ],
        ))
        lines.append("")

    for col in ["signature_position", "signature_source", "signature_norm", "commenter_standard", "commenter_confidence"]:
        if col in df.columns:
            lines.append(f"### `{col}`")
            lines.append("")
            lines.append(_vc_table(df[col], total=n, top_n=args.top_n, dropna=False))
            lines.append("")

    # Date fields
    if "has_date" in df.columns:
        has_date_n = int(df["has_date"].fillna(0).astype(int).sum())
        lines.append("### 日期识别概览")
        lines.append("")
        lines.append(_md_table(
            ["metric", "value"],
            [
                ["has_date = 1", _pct(has_date_n, n)],
                ["has_date = 0", _pct(n - has_date_n, n)],
            ],
        ))
        lines.append("")

    for col in ["date_ganzhi", "date_year_est", "date_qianlong_year_est", "comment_period_est"]:
        if col in df.columns:
            if col in ("date_year_est", "date_qianlong_year_est"):
                desc = _num_describe(df[col])
                lines.append(f"### `{col}`")
                lines.append("")
                lines.append(_num_table(col, desc))
                lines.append("")
            else:
                lines.append(f"### `{col}`")
                lines.append("")
                lines.append(_vc_table(df[col], total=n, top_n=args.top_n, dropna=False))
                lines.append("")

    # Text length
    if "char_len" in df.columns:
        lines.append("### `char_len`（批语文本长度；基于 `comment_text_clean`）")
        lines.append("")
        desc = _num_describe(df["char_len"], percentiles=(0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99))
        # Add 99% if present
        lines.append(_num_table("char_len", desc))
        lines.append("")

        # Signed vs unsigned comparison
        if "has_signature" in df.columns:
            rows = []
            for hs, label in [(0, "unsigned"), (1, "signed")]:
                s = df.loc[df["has_signature"].fillna(0).astype(int) == hs, "char_len"].dropna()
                if len(s) == 0:
                    continue
                rows.append([
                    label,
                    len(s),
                    f"{s.mean():.2f}",
                    f"{s.median():.1f}",
                    f"{s.quantile(0.9):.1f}",
                    int(s.max()),
                ])
            if rows:
                lines.append("**署名 vs 未署名（`char_len`）**")
                lines.append("")
                lines.append(_md_table(["group", "n", "mean", "median", "p90", "max"], rows))
                lines.append("")

    # Bracket structure
    if set(["bracket_spans_paragraphs", "doc_global_start", "doc_global_end"]).issubset(df.columns):
        lines.append("### 括号块结构（【…】）")
        lines.append("")
        lines.append(_vc_table(df["bracket_spans_paragraphs"], total=n, top_n=None, dropna=False))
        lines.append("")
        bracket_len = df["doc_global_end"] - df["doc_global_start"]
        lines.append("**括号块全局长度（doc_global_end - doc_global_start）**")
        lines.append("")
        lines.append(_num_table("bracket_len", _num_describe(bracket_len, percentiles=(0.1,0.25,0.5,0.75,0.9,0.95,0.99))))
        lines.append("")

    # Context window lengths
    for col in ["anchor_before", "anchor_after", "paragraph_main_text", "context_before_60", "context_after_60"]:
        if col in df.columns:
            lens = df[col].astype(str).where(~df[col].isna(), "")
            lens = lens.map(len)
            lines.append(f"### `{col}` 长度（字符数）")
            lines.append("")
            lines.append(_num_table(col + "_len", _num_describe(lens)))
            lines.append("")

    # Duplicates in cleaned text
    if "comment_text_clean" in df.columns:
        dup_n = int(df.duplicated(subset=["comment_text_clean"]).sum())
        uniq_n = int(df["comment_text_clean"].nunique(dropna=True))
        lines.append("### 文本去重信息")
        lines.append("")
        lines.append(_md_table(
            ["metric", "value"],
            [
                ["unique comment_text_clean", f"{uniq_n:,}"],
                ["duplicated rows (by comment_text_clean)", f"{dup_n:,}"],
            ],
        ))
        lines.append("")

    # -------------------- C. Probabilistic fields --------------------
    lines.append("## C. 先验/概率字段（probabilistic; not ground truth）")
    lines.append("")

    for col in ["prior_zhi_dom", "prior_jihu_dom", "prior_other_dom"]:
        if col in df.columns:
            lines.append(f"### `{col}`")
            lines.append("")
            lines.append(_num_table(col, _num_describe(df[col])))
            lines.append("")

    for col in ["prior_label_dom", "prior_basis_dom"]:
        if col in df.columns:
            lines.append(f"### `{col}`")
            lines.append("")
            lines.append(_vc_table(df[col], total=n, top_n=args.top_n, dropna=False))
            lines.append("")

    # Prior sanity check
    if set(["prior_zhi_dom", "prior_jihu_dom", "prior_other_dom"]).issubset(df.columns):
        s = (df["prior_zhi_dom"] + df["prior_jihu_dom"] + df["prior_other_dom"]).dropna()
        lines.append("### 先验概率求和校验")
        lines.append("")
        lines.append(_num_table("prior_sum", _num_describe(s)))
        lines.append("")

    # -------------------- Missingness --------------------
    lines.append("## D. 缺失值概览（missingness）")
    lines.append("")
    miss_n = df.isna().sum()
    miss_pct = (miss_n / n * 100).round(3)
    miss = (
        pd.DataFrame({"missing_n": miss_n, "missing_pct": miss_pct})
        .sort_values(["missing_pct", "missing_n"], ascending=False)
    )
    miss = miss[miss["missing_n"] > 0]
    if len(miss) == 0:
        lines.append("本数据集中不存在缺失值。")
    else:
        top = miss.head(20)
        rows = [[idx, int(r.missing_n), f"{r.missing_pct:.3f}%"] for idx, r in top.iterrows()]
        lines.append("**缺失值最多的前 20 列**")
        lines.append("")
        lines.append(_md_table(["column", "missing_n", "missing_pct"], rows))
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
