import os, requests

repo = os.environ.get("SRC_REPO", "luohongk/Embodied-AI-Daily")
token = os.environ["PUSHPLUS_TOKEN"]

# 取最新一条 issue（state=all 或 open 都行，看作者习惯用 open 汇总）
r = requests.get(
    f"https://api.github.com/repos/{repo}/issues",
    params={"per_page": 1, "state": "all"},
    headers={"Accept": "application/vnd.github+json"},
    timeout=20,
)
r.raise_for_status()
issue = r.json()[0]
title = issue["title"]
body = issue.get("body", "") or ""
# 太长截断，PushPlus 微信侧别太�胖
if len(body) > 3500:
    body = body[:3500] + "\n...（更多见 GitHub Issue）"

content = f"## {title}\n\n{body}\n\n> 来源: {issue['html_url']}"
requests.post("https://www.pushplus.plus/send", data={
    "token": token,
    "title": "具身智能论文早报",
    "content": content,
    "template": "markdown",
})
