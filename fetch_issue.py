import os
import re
import time
import requests
import xml.etree.ElementTree as ET
import sys

# ---------- 配置 ----------
REPO = "luohongk/Embodied-AI-Daily"
ARXIV_API = "http://export.arxiv.org/api/query"
ABSTRACT_LEN = 320          # 每条 abstract 截多少字，微信别太长
REQUEST_TIMEOUT = 25
SLEEP_BETWEEN = 3           # arXiv 礼貌间隔，别被封

# ---------- 1. 取最新 Issue ----------
print(f"📡 从 {REPO} 取最新 Issue...")
r = requests.get(
    f"https://api.github.com/repos/{REPO}/issues",
    params={"per_page": 1, "state": "all"},
    headers={"Accept": "application/vnd.github+json"},
    timeout=REQUEST_TIMEOUT,
)
r.raise_for_status()
issue = r.json()[0]
print(f"✅ Issue: {issue['title']}")

body = issue.get("body", "") or ""

# ---------- 2. 工具函数 ----------
def extract_arxiv_id(text):
    """从一行里抠 arxiv ID，支持 /abs/ 和 /pdf/ 两种链接"""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", text)
    return m.group(1) if m else None

def fetch_abstract(arxiv_id):
    """调 arXiv API 拿 summary"""
    try:
        resp = requests.get(
            ARXIV_API,
            params={"id_list": arxiv_id, "max_results": 1},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(resp.text)
        entry = root.find("atom:entry", ns)
        if entry is None:
            return ""
        summary = entry.find("atom:summary", ns)
        if summary is None or not summary.text:
            return ""
        # 去掉多余空白
        text = " ".join(summary.text.strip().split())
        return text
    except Exception as e:
        print(f"  ⚠️ 抓 abstract 失败 {arxiv_id}: {e}")
        return ""

# ---------- 3. 解析 Issue 表格并补 abstract ----------
lines = body.splitlines()
output = []
paper_count = 0

for line in lines:
    line = line.strip()
    if not line:
        continue

    # 跳过表头 / 分隔线
    if re.match(r"^\|?\s*(Title|Date|Comment)\b", line, re.I):
        continue
    if re.match(r"^\|?\s*[-:\s\|]+\|?\s*$", line):
        continue

    # 表格数据行
    if line.startswith("|") and line.endswith("|"):
        parts = [p.strip() for p in line[1:-1].split("|")]
        if not parts or not parts[0]:
            continue

        title_md = parts[0]          # 形如 [标题](链接)
        date_str = parts[1] if len(parts) > 1 else ""
        comment_str = parts[2] if len(parts) > 2 else ""

        # 抽标题和链接
        t_match = re.match(r"\[(.+?)\]\((.+?)\)", title_md)
        if t_match:
            paper_title = t_match.group(1)
            paper_url = t_match.group(2)
            title_line = f"📄 [{paper_title}]({paper_url})"
        else:
            paper_title = title_md
            paper_url = ""
            title_line = f"📄 {paper_title}"

        output.append(title_line)
        if date_str:
            output.append(f"🗓 {date_str}")
        if comment_str:
            output.append(f"💬 {comment_str}")

        # ---- 关键：抓 abstract ----
        arxiv_id = extract_arxiv_id(title_md + " " + paper_url)
        if arxiv_id:
            print(f"  🔍 抓 abstract: {arxiv_id}")
            abstract = fetch_abstract(arxiv_id)
            if abstract:
                if len(abstract) > ABSTRACT_LEN:
                    abstract = abstract[:ABSTRACT_LEN].rstrip() + "…"
                output.append(f"📝 {abstract}")
            else:
                output.append("📝 (abstract 暂不可用)")
            time.sleep(SLEEP_BETWEEN)   # 礼貌爬取
        else:
            output.append("📝 (非 arXiv 链接，无 abstract)")

        output.append("")
        output.append("---")
        output.append("")
        paper_count += 1

print(f"📊 共解析 {paper_count} 篇论文")

# ---------- 4. 组装并发送 ----------
pretty_body = "\n".join(output)
if len(pretty_body) > 3500:
    pretty_body = pretty_body[:3500] + "\n\n...（更多见 GitHub Issue）"

content = f"## {issue['title']}\n\n{pretty_body}\n\n> [查看 GitHub 原文]({issue['html_url']})"

token = os.environ.get("PUSHPLUS_TOKEN")
if not token:
    print("❌ 没找到 PUSHPLUS_TOKEN")
    sys.exit(1)

print("📤 发送到 PushPlus...")
resp = requests.post(
    "https://www.pushplus.plus/send",
    data={
        "token": token,
        "title": "具身智能论文早报",
        "content": content,
        "template": "markdown",
    },
    timeout=REQUEST_TIMEOUT,
)
print(f"PushPlus 返回: {resp.status_code}, {resp.text}")
if resp.status_code != 200:
    sys.exit(1)
print("✅ 完成")
