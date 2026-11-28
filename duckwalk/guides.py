"""Buying guides: our own written content, kept in content/guides/*.md (stdlib only).

Each guide is a Markdown file with a small front-matter block:

    ---
    title: ...            # <title> and Article headline
    slug: ...             # URL is /guides/<slug>/
    description: ...      # meta description
    published: YYYY-MM-DD
    modified: YYYY-MM-DD
    match: regex          # picks the in-stock models shown under the guide (matched against model names)
    store_query: ...      # eBay store search used by the closing button
    summary: ...          # one-liner for the index page
    ---

Guides are our own words. They hold no eBay data: no photos, prices, sizes, reviews or feedback.
The only eBay Content on a guide page is the "pairs in stock now" box, which reuses the same
labeled card block the home and brand pages use (live listings only, refreshed every build).
"""
import glob
import json
import os
import re
from html import escape as e

from .links import store_search_url
from .models import slugify

FM_KEYS = ("title", "slug", "description", "published", "modified", "match", "store_query", "summary")


def load_guides(root):
    guides = []
    for path in sorted(glob.glob(os.path.join(root, "content", "guides", "*.md"))):
        text = open(path, encoding="utf-8").read()
        m = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S)
        if not m:
            raise SystemExit(f"{path}: missing front matter")
        meta = {}
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        for k in FM_KEYS:
            if not meta.get(k):
                raise SystemExit(f"{path}: front matter is missing '{k}'")
        meta["slug"] = slugify(meta["slug"])
        meta["body_md"] = m.group(2).strip() + "\n"
        meta["path"] = f"/guides/{meta['slug']}/"
        guides.append(meta)
    guides.sort(key=lambda g: (g["published"], g["slug"]))
    return guides


# ---------- tiny Markdown subset: ## headings, paragraphs, -/1. lists, tables, **bold**, [text](/path/) ----------

def _inline(text, links, strip=()):
    out = e(text)

    def link(mo):
        label, href = mo.group(1), mo.group(2)
        links.append(href.replace("&amp;", "&"))
        if href in strip:  # target page does not exist in this build: keep the words, drop the dead link
            return label
        return f'<a href="{href}">{label}</a>'
    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def render_markdown(md, links, strip=()):
    html, para, lst, table = [], [], None, []

    def flush_para():
        if para:
            html.append("<p>" + _inline(" ".join(para), links, strip) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            html.append(f"<{tag}>" + "".join(f"<li>{_inline(i, links, strip)}</li>" for i in items) + f"</{tag}>")
            lst = None

    def flush_table():
        if table:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table
                    if not re.match(r"^\|?\s*-{2,}", r.strip())]
            head, body = rows[0], rows[1:]
            th = "".join(f"<th>{_inline(c, links, strip)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{_inline(c, links, strip)}</td>" for c in r) + "</tr>" for r in body)
            html.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
            table.clear()

    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            flush_para(); flush_list(); table.append(s); continue
        flush_table()
        if not s.strip():
            flush_para(); flush_list(); continue
        if s.startswith("## "):
            flush_para(); flush_list()
            html.append(f"<h2>{_inline(s[3:].strip(), links, strip)}</h2>"); continue
        mo = re.match(r"^(-|\d+\.)\s+(.*)", s)
        if mo:
            flush_para()
            tag = "ul" if mo.group(1) == "-" else "ol"
            if lst and lst[0] != tag:
                flush_list()
            lst = lst or (tag, [])
            lst[1].append(mo.group(2)); continue
        para.append(s.strip())
    flush_para(); flush_list(); flush_table()
    return "\n".join(html)


def word_count(md):
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    return len(re.sub(r"[|#*]+|(?<!\w)-+(?!\w)", " ", t).split())


def matching_models(g, models, limit=8):
    """In-stock models whose name matches the guide's regex, most pairs first."""
    rx = re.compile(g["match"], re.I)
    hits = [m for m in models if m["in_stock"] and rx.search(m["name"])]
    hits.sort(key=lambda m: (-len(m["listings"]), m["name"], m["slug"]))
    # Mix model names (e.g. R4, TL and NZ) instead of showing eight colorways of one model.
    by_name = {}
    for m in hits:
        by_name.setdefault(m["name"], []).append(m)
    out, rows = [], list(by_name.values())
    while rows and len(out) < limit:
        for r in rows:
            if len(out) < limit:
                out.append(r.pop(0))
        rows = [r for r in rows if r]
    return out


def guides_for_model(m, guides):
    rx_hits = [g for g in guides if re.search(g["match"], m["name"], re.I)]
    return rx_hits[:2]
