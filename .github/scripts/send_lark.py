"""Main orchestrator: pick next episode, send Lark, check backlog, generate if needed."""
import os, json, sys, subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKLOG_PATH = SCRIPTS_DIR / "backlog.json"
EPISODES_DIR = SCRIPTS_DIR.parent.parent / "episodes"
INDEX_PATH = SCRIPTS_DIR.parent.parent / "index.html"
WEBHOOK_URL = os.environ["LARK_WEBHOOK_URL"]
SITE_URL = os.environ.get("SITE_URL", "https://zhuayuba.github.io/Historybug/")

QUADRANT_EMOJI = {"modern": "🔷", "ancient": "🟡", "world": "🟣"}
QUADRANT_LABEL = {"modern": "近現代中國", "ancient": "古代中國", "world": "全球史"}

EPISODE_META = {
    "001-xian-shi-bian": {"title": "西安事變", "subject": "張學良 · 1936.12.12", "quadrant": "modern", "type": "機械降神", "timeline": "1936"},
    "002-si-du-chishui": {"title": "四渡赤水", "subject": "毛澤東 · 1935", "quadrant": "modern", "type": "無限流玩家", "timeline": "1935"},
    "003-qin-shi-huang": {"title": "秦始皇", "subject": "System Format Admin · 前259–前210", "quadrant": "ancient", "type": "系統格式化", "timeline": "前259–前210"},
    "004-sun-zhongshan": {"title": "孫中山", "subject": "二周目迷茫玩家 · 1866–1925", "quadrant": "modern", "type": "平行宇宙滯留者", "timeline": "1866–1925"},
    "005-hong-xiuquan": {"title": "洪秀全與太平天國", "subject": "文化軟體安裝中斷 · 1851–1864", "quadrant": "modern", "type": "降維下載失敗", "timeline": "1851–1864"},
    "006-da-vinci": {"title": "達文西", "subject": "Stranded Futurist · 1452–1519", "quadrant": "world", "type": "時間旅行者", "timeline": "1452–1519"},
    "007-feng-yuxiang": {"title": "馮玉祥", "subject": "全圖流倖存者 · 1882–1948", "quadrant": "modern", "type": "覺醒NPC", "timeline": "1882–1948"},
    "008-deng-xiaoping": {"title": "鄧小平", "subject": "Root Access User · 1904–1997", "quadrant": "modern", "type": "系統管理員", "timeline": "1904–1997"},
    "009-zhu-ge-liang": {"title": "諸葛亮", "subject": "Timeline Calculator · 181–234", "quadrant": "ancient", "type": "時間線計算者", "timeline": "181–234"},
    "010-zhou-enlai": {"title": "周恩來", "subject": "Timeline Navigator · 1898–1976", "quadrant": "modern", "type": "時間線導航員", "timeline": "1898–1976"},
    "011-cixi": {"title": "慈禧太后", "subject": "Negative Optimization AI · 1835–1908", "quadrant": "modern", "type": "負優化AI", "timeline": "1835–1908"},
    "012-napoleon": {"title": "拿破崙", "subject": "Stat Overflow · 1769–1821", "quadrant": "world", "type": "數據溢出", "timeline": "1769–1821"},
    "013-lu-xun": {"title": "魯迅", "subject": "Diagnostic Protocol Agent · 1881–1936", "quadrant": "modern", "type": "診斷協議執行者", "timeline": "1881–1936"},
    "014-lin-biao": {"title": "林彪", "subject": "Speedrunner · 1907–1971", "quadrant": "modern", "type": "速通玩家", "timeline": "1907–1971"},
    "015-wu-zetian": {"title": "武則天", "subject": "Privilege Escalation · 624–705", "quadrant": "ancient", "type": "權限漏洞利用", "timeline": "624–705"},
    "016-li-hongzhang": {"title": "李鴻章", "subject": "System Guardian · 1823–1901", "quadrant": "modern", "type": "守護進程", "timeline": "1823–1901"},
}

def send_lark(slug, meta, total, remaining):
    """Send Lark notification featuring this episode."""
    quad = meta.get("quadrant", "modern")
    emoji = QUADRANT_EMOJI.get(quad, "🔷")
    label = QUADRANT_LABEL.get(quad, "")

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"腦洞歷史 · {emoji} {meta['title']}"},
                "template": "wathet"
            },
            "elements": [
                {"tag": "markdown", "content": f"**{meta['type']}** · {label}\n{meta['subject']}\n\n{meta.get('excerpt', '點擊下方按鈕查看完整檔案。')}"},
                {"tag": "hr"},
                {"tag": "markdown", "content": f"📊 本期為第 **{total - remaining + 1}** 期推送 · 存貨剩餘 **{remaining}** 期"},
                {"tag": "action", "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "🔍 查看本期檔案"}, "url": f"{SITE_URL}episodes/{slug}.html", "type": "primary"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "📂 瀏覽全部檔案"}, "url": SITE_URL, "type": "default"}
                ]}
            ]
        }
    }

    req = Request(
        WEBHOOK_URL,
        data=json.dumps(card).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urlopen(req, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        print(f"Lark sent: {result.get('StatusMessage', result)}")
    except Exception as e:
        print(f"Lark webhook failed (non-fatal): {e}")

def update_index_html(slugs, meta_map):
    """Minimally update index.html — just ensure all slugs are present.
    For auto-generated episodes, we add a card entry if missing."""
    # This is a simplified approach; for robustness we parse and update
    content = INDEX_PATH.read_text(encoding="utf-8")
    for slug in slugs:
        if slug not in content:
            # Auto-generated episode not yet in index — add a basic card
            # We insert before the last </main> tag
            meta = meta_map.get(slug, {"title": slug, "subject": "", "type": "未知", "quadrant": "modern", "timeline": ""})
            quad_class = "quadrant-ancient" if meta["quadrant"] == "ancient" else ("quadrant-world" if meta["quadrant"] == "world" else "")
            card = f'''
    <a href="episodes/{slug}.html" class="episode-card {quad_class}" data-type="{meta.get('type', '未知')}" data-quadrant="{meta.get('quadrant', 'modern')}">
      <div class="card-header">
        <div class="card-header-left"><span class="card-number">ANO-{slug[:3]}</span><span class="quadrant-badge {meta.get('quadrant', 'modern')}">{QUADRANT_LABEL.get(meta['quadrant'], '')[:2]}</span></div>
        <span class="card-anomaly-type">{meta.get('type', '')}</span>
      </div>
      <div class="card-body">
        <h3>{meta.get('title', slug)}</h3>
        <p class="card-subject">{meta.get('subject', '')}</p>
        <p class="card-excerpt">點擊查看完整異常觀測檔案。</p>
      </div>
      <div class="card-footer"><span class="timeline">{meta.get('timeline', '')}</span><span class="arrow">▶ 檢視檔案</span></div>
    </a>'''
            # Insert before </main>
            content = content.replace("</main>", card + "\n  </main>")

    INDEX_PATH.write_text(content, encoding="utf-8")
    print("index.html updated")

def git_commit_push():
    """Commit and push changes."""
    cmds = [
        ["git", "config", "user.name", "Historybug Bot"],
        ["git", "config", "user.email", "bot@historybug.local"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"Auto: push episode + update backlog [{datetime.utcnow().strftime('%Y-%m-%d')}]"],
        ["git", "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            stderr = result.stderr or ""
            if "nothing to commit" in stderr:
                print("Nothing to commit, skipping push.")
                break
            else:
                print(f"Git error ({' '.join(cmd)}): {stderr}")

def main():
    # Load backlog
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
    upcoming = backlog["upcoming"]
    featured = backlog.get("featured", [])

    if not upcoming:
        print("ERROR: No upcoming episodes in backlog!")
        sys.exit(1)

    # Pick next episode
    slug = upcoming.pop(0)
    featured.append(slug)

    # Get metadata
    meta = EPISODE_META.get(slug, {})
    if not meta:
        # Try to read from the episode HTML
        ep_path = EPISODES_DIR / f"{slug}.html"
        if ep_path.exists():
            import re
            html = ep_path.read_text(encoding="utf-8")
            title_m = re.search(r"<h2 class=\"part-title\">信號異常</h2>\s*<p>(.*?)</p>", html, re.DOTALL)
            title_tag = re.search(r"<title>(.*?)</title>", html)
            meta = {
                "title": title_tag.group(1).split("：")[-1].split("—")[0].strip() if title_tag else slug,
                "subject": "",
                "type": "未知",
                "quadrant": "modern",
                "timeline": "",
            }

    total_before = len(upcoming) + len(featured)
    remaining = len(upcoming)

    # Send Lark notification
    print(f"Featuring: {slug} ({meta.get('title')}) — {remaining} remaining")
    send_lark(slug, meta, total_before, remaining)

    # Save intermediate backlog state
    backlog["upcoming"] = upcoming
    backlog["featured"] = featured

    # Check if we need to generate
    generated_slugs = []
    if remaining <= 2:
        print(f"⚠️  Backlog low ({remaining} remaining). Generating 6 new episodes...")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate_episodes.py")],
            capture_output=True, text=True, timeout=600,
            env={**os.environ, "LLM_API_KEY": os.environ["LLM_API_KEY"]}
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"Generation error: {result.stderr}")

        # Reload backlog (generate_episodes updated it)
        backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))
        # Find newly added slugs
        for s in backlog["upcoming"]:
            if s not in featured:
                generated_slugs.append(s)
        print(f"Generated {len(generated_slugs)} new episodes: {generated_slugs}")

    else:
        BACKLOG_PATH.write_text(json.dumps(backlog, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build meta map for index update
    all_slugs = backlog["upcoming"] + backlog["featured"]
    meta_map = dict(EPISODE_META)
    for s in generated_slugs:
        if s not in meta_map:
            meta_map[s] = {"title": s, "subject": "", "type": "未知", "quadrant": "modern", "timeline": ""}

    # Update index.html with any new episodes
    update_index_html(all_slugs, meta_map)

    # Commit and push
    git_commit_push()

    print(f"Done. Featured: {slug}, Backlog: {len(backlog['upcoming'])} upcoming, {len(backlog['featured'])} featured")

if __name__ == "__main__":
    main()
