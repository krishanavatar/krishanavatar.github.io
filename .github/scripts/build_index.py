#!/usr/bin/env python3
"""Regenerate the homepage article list from per-post metadata.

Scans every <slug>/post.json, sorts newest first, and rewrites the block
between the POSTS:START and POSTS:END markers in index.html. The article
count is derived from the number of posts, never hand-typed.

Idempotent: running again with no content change writes nothing.
"""
import glob
import html
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX = os.path.join(ROOT, "index.html")

# tag -> css suffix used for the coloured strip + badge in index.html
TAG_CLASS = {
    "LLM Engineering": "llm",
    "Architecture": "ai",
    "Document AI": "idp",
}


def load_posts():
    posts = []
    for path in glob.glob(os.path.join(ROOT, "*", "post.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["slug"] = os.path.basename(os.path.dirname(path))
        posts.append(data)
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    return posts


def fmt_date(iso):
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
    except ValueError:
        return iso
    return f"{dt.strftime('%b')} {dt.day}, {dt.year}"


def render(posts):
    n = len(posts)
    label = "essay" if n == 1 else "essays"
    out = [
        f'      <div class="posts-count"><span class="pc-num">{n}</span> {label} published</div>',
        '      <div class="articles-list">',
    ]
    for p in posts:
        cls = TAG_CLASS.get(p.get("tag", ""), "n")
        title = html.escape(p.get("title", p["slug"]))
        summary = html.escape(p.get("summary", ""))
        tag = html.escape(p.get("tag", ""))
        date = html.escape(fmt_date(p.get("date", "")))
        rt = html.escape(p.get("readingTime", ""))
        out += [
            f'        <a class="art-row art-{cls}" href="/{p["slug"]}/">',
            '          <span class="art-strip"></span>',
            '          <div class="art-body">',
            '            <div class="art-top">',
            f'              <span class="art-badge badge-{cls}">{tag}</span>',
            f'              <span class="art-title">{title}</span>',
            '            </div>',
            f'            <p class="art-desc">{summary}</p>',
            '          </div>',
            '          <div class="art-meta">',
            f'            <span class="art-date">{date}</span>',
        ]
        if rt:
            out.append(f'            <span class="art-rt">{rt}</span>')
        out += [
            '            <span class="art-link">Read &rarr;</span>',
            '          </div>',
            '        </a>',
        ]
    out.append('      </div>')
    return "\n".join(out)


def main():
    posts = load_posts()
    block = render(posts)
    with open(INDEX, encoding="utf-8") as f:
        src = f.read()
    pattern = re.compile(r"(<!-- POSTS:START -->)(.*?)(<!-- POSTS:END -->)", re.DOTALL)
    if not pattern.search(src):
        raise SystemExit("index.html: POSTS markers not found")
    new = pattern.sub(lambda m: f"{m.group(1)}\n{block}\n      {m.group(3)}", src)
    if new != src:
        with open(INDEX, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"index.html rebuilt: {len(posts)} post(s)")
    else:
        print("index.html already up to date")


if __name__ == "__main__":
    main()
