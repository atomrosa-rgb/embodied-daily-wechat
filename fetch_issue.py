import os
import requests
import sys

repo = "luohongk/Embodied-AI-Daily"

print(f"要访问的仓库: {repo}")

url = f"https://api.github.com/repos/{repo}/issues"
print(f"请求 URL: {url}")

r = requests.get(
    url,
    params={"per_page": 1, "state": "all"},
    headers={"Accept": "application/vnd.github+json"},
    timeout=20,
)

print(f"HTTP 状态码: {r.status_code}")

if r.status_code == 404:
    print("❌ 404：仓库路径不对，或者仓库不存在/不可访问。请检查 repo 变量。")
    sys.exit(1)

r.raise_for_status()

issues = r.json()
if not issues:
    print("没有拿到 issue")
    sys.exit(1)

issue = issues[0]
title = issue["title"]
body = issue.get("body", "") or ""

if len(body) > 3500:
    body = body[:3500] + "\n...（更多见 GitHub Issue）"

content = f"## {title}\n\n{body}\n\n> 来源: {issue['html_url']}"

token = os.environ.get("PUSHPLUS_TOKEN")
if not token:
    print("❌ 没找到 PUSHPLUS_TOKEN")
    sys.exit(1)

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
