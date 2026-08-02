import os
import requests
import sys
import re

repo = "luohongk/Embodied-AI-Daily"

print(f"要访问的仓库: {repo}")
url = f"https://api.github.com/repos/{repo}/issues"

r = requests.get(
    url,
    params={"per_page": 1, "state": "all"},
    headers={"Accept": "application/vnd.github+json"},
    timeout=20,
)
print(f"GitHub API 状态码: {r.status_code}")
r.raise_for_status()

issues = r.json()
if not issues:
    print("没有拿到 issue")
    sys.exit(1)

issue = issues[0]
title = issue["title"]
body = issue.get("body", "") or ""

# --- 核心：格式清洗与美化 ---
# 1. 去掉 Markdown 表格的表头和分隔线（类似 | Title | Date | 这种）
lines = body.splitlines()
cleaned_lines = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    # 跳过表头和 ---|---|--- 这种行
    if re.match(r'^\|?\s*(Title|Date|Comment)\s*\|', line, re.I):
        continue
    if re.match(r'^\|?\s*[-:]+\s*\|', line):
        continue
    
    # 2. 如果是表格数据行（用 | 分隔），把它拆成漂亮的单条论文格式
    if line.startswith('|') and line.endswith('|'):
        parts = [p.strip() for p in line[1:-1].split('|')]
        if len(parts) >= 2:
            paper_title_md = parts[0]  # 通常包含 [标题](链接)
            date_str = parts[1] if len(parts) > 1 else ""
            comment_str = parts[2] if len(parts) > 2 else ""
            
            # 拼接成手机端友好的卡片样式
            cleaned_lines.append(f"📄 {paper_title_md}")
            if date_str:
                cleaned_lines.append(f"🗓 {date_str}")
            if comment_str:
                cleaned_lines.append(f"💬 {comment_str}")
            cleaned_lines.append("")  # 空行隔开
            cleaned_lines.append("---")  # 分割线
            cleaned_lines.append("")  # 空行
        else:
            cleaned_lines.append(line)
    else:
        cleaned_lines.append(line)

pretty_body = "\n".join(cleaned_lines)

# 3. 截断控制（防止太长）
if len(pretty_body) > 3500:
    pretty_body = pretty_body[:3500] + "\n...（更多见 GitHub Issue）"

content = f"## {title}\n\n{pretty_body}\n\n> [查看 GitHub 原文]({issue['html_url']})"

# --- 发送 PushPlus ---
token = os.environ.get("PUSHPLUS_TOKEN")
if not token:
    print("❌ 没找到 PUSHPLUS_TOKEN")
    sys.exit(1)

print("📤 正在发送到 PushPlus...")
resp = requests.post(
    "https://www.pushplus.plus/send",
    data={
        "token": token,
        "title": "具身智能论文早报",
        "content": content,
        "template": "markdown",
    },
    timeout=20,
)

print(f"PushPlus 返回: {resp.status_code}, {resp.text}")
if resp.status_code == 200:
    print("✅ 发送成功！")
else:
    print("❌ 发送失败")
    sys.exit(1)
