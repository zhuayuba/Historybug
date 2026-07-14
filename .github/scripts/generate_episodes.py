"""Generate 6 new episodes via LLM API when backlog is low."""
import os, json, re, sys, textwrap
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ["LLM_API_KEY"]
API_BASE = os.environ.get("LLM_API_BASE", "https://api.deepseek.com/v1")
EPISODES_DIR = Path(__file__).resolve().parent.parent.parent / "episodes"
BACKLOG_PATH = Path(__file__).resolve().parent / "backlog.json"

# Determine quadrant rotation based on existing counts
def next_quadrants(backlog):
    counter = backlog.get("quadrant_counter", {"modern": 11, "ancient": 3, "world": 2})
    # Generate 6 new episodes following M-M-A-M-M-W pattern
    # Determine starting position based on tail of current upcoming list
    upcoming = backlog["upcoming"]
    tail_quadrants = []
    for slug in upcoming[-4:]:
        if slug in EPISODE_META:
            tail_quadrants.append(EPISODE_META[slug]["quadrant"])
        else:
            tail_quadrants.append("modern")

    # Pattern: M-M-A-M-M-W (6 per cycle)
    # Figure out where we are in the pattern based on tail
    pattern = ["modern", "modern", "ancient", "modern", "modern", "world"]
    # Try each rotation to find the best fit
    best_start = 0
    best_match = -1
    for start in range(6):
        match = 0
        for i, tq in enumerate(tail_quadrants[-3:]):
            if tq == pattern[(start + i) % 6]:
                match += 1
        if match > best_match:
            best_match = match
            best_start = start

    # Generate 6 quadrants starting from best_start+1 (next in pattern)
    new_quadrants = []
    pos = (best_start + len(tail_quadrants)) % 6
    for _ in range(6):
        new_quadrants.append(pattern[pos % 6])
        pos += 1

    # Update counter
    for q in new_quadrants:
        counter[q] = counter.get(q, 0) + 1

    return new_quadrants, counter

# Episode metadata for existing episodes (used by the script to know quadrants)
EPISODE_META = {
    "001-xian-shi-bian": {"quadrant": "modern", "type": "機械降神"},
    "002-si-du-chishui": {"quadrant": "modern", "type": "無限流玩家"},
    "003-qin-shi-huang": {"quadrant": "ancient", "type": "系統格式化"},
    "004-sun-zhongshan": {"quadrant": "modern", "type": "平行宇宙滯留者"},
    "005-hong-xiuquan": {"quadrant": "modern", "type": "降維下載失敗"},
    "006-da-vinci": {"quadrant": "world", "type": "時間旅行者"},
    "007-feng-yuxiang": {"quadrant": "modern", "type": "覺醒NPC"},
    "008-deng-xiaoping": {"quadrant": "modern", "type": "系統管理員"},
    "009-zhu-ge-liang": {"quadrant": "ancient", "type": "時間線計算者"},
    "010-zhou-enlai": {"quadrant": "modern", "type": "時間線導航員"},
    "011-cixi": {"quadrant": "modern", "type": "負優化AI"},
    "012-napoleon": {"quadrant": "world", "type": "數據溢出"},
    "013-lu-xun": {"quadrant": "modern", "type": "診斷協議執行者"},
    "014-lin-biao": {"quadrant": "modern", "type": "速通玩家"},
    "015-wu-zetian": {"quadrant": "ancient", "type": "權限漏洞利用"},
    "016-li-hongzhang": {"quadrant": "modern", "type": "守護進程"},
}

def read_example_html(slug):
    """Read an existing episode HTML as an example for the AI."""
    path = EPISODES_DIR / f"{slug}.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None

def build_prompt(quadrants, existing_slugs):
    """Build the generation prompt with context and examples."""
    # Read 2 example episodes (one modern, one ancient/world)
    example_modern = read_example_html("001-xian-shi-bian")
    example_ancient = read_example_html("003-qin-shi-huang")

    # Get last episode number
    max_num = 0
    for s in existing_slugs:
        n = int(s.split("-")[0])
        if n > max_num:
            max_num = n

    start_num = max_num + 1

    quadrant_labels = {
        "modern": "近現代中國 ▸ 核心觀測區",
        "ancient": "古代中國 ▸ 深層掃描區",
        "world": "全球史 ▸ 跨域觀測區"
    }

    quadrant_descriptions = []
    for i, q in enumerate(quadrants):
        num = start_num + i
        quadrant_descriptions.append(f"ANO-{num:03d}: 時空象限={q} ({quadrant_labels[q]})")

    prompt = f"""你是一個歷史腦洞寫作助手。請為「腦洞歷史」系列生成 6 期新的異常觀測檔案。

## 時空象限分配（嚴格遵循）
{chr(10).join(quadrant_descriptions)}

## 格式要求
每期必須是一個獨立的 HTML 段落，嚴格遵循以下結構。請參考提供的範例。
每個 episode 的 HTML 開始於 `<!-- EPISODE START: ANO-XXX -->` 結束於 `<!-- EPISODE END -->`。

## 內容結構
每期包含4個Part:
- Part 0: 信號異常（約150字，懸疑鉤子，用一個引人入勝的異常細節開場）
- Part 1: 異常觀測報告（含1.1類型判定、1.2五個關鍵異常點、1.3推演敘事約200字、1.4可信度評估百分比和一句點評）
- Part 2: 正史解碼（含2.1歷史現場約300字、2.2深層邏輯約200字、2.3史家評價約100字和參考來源）
- Part 3: 二象性觀察（含3.1腦洞為什麼成立、3.2正史為什麼可靠、3.3尾聲含finale-line和約100字結尾段落）

## 重要規則
1. Part 2 的歷史事實必須完全準確——這是硬性要求。日期、人物、事件經過不能有任何虛構。
2. Part 1 的腦洞可以天馬行空（科幻、遊戲、系統邏輯），但要和真實歷史細節掛鉤。
3. Part 3 是兩個視角的對話——不能只是重複前文，要有反思。
4. 每期的「異常類型」要新穎，避免重複已有的類型（如機械降神、無限流玩家等已使用過）。
5. 選題優先級：近現代中國 > 古代中國 > 全球史。
6. 近現代候選：梁啟超、陳獨秀、胡適、張愛玲、袁隆平、瞿秋白、汪精衛、閻錫山、杜月笙...
7. 古代候選：曹操、蘇軾、岳飛、鄭和、李白、王陽明、司馬遷、張騫...
8. 世界候選：愛因斯坦、圖靈、聖女貞德、哥倫布、梵谷、拉斯普京、特斯拉...

## 範例 HTML 格式（請嚴格複製此結構）

以下是兩個完整範例：

=== 範例 1 (近現代) ===
{example_modern[:3000]}

=== 範例 2 (古代) ===
{example_ancient[:3000]}

## 輸出格式
請直接輸出 6 個 HTML 區塊，每個區塊以 `<!-- EPISODE START: ANO-{num:03d} -->` 開始，以 `<!-- EPISODE END -->` 結束。
區塊之間不需要任何分隔符或文字說明。
請確保每個 episode 中所有 `<` `>` 符號只用於 HTML 標籤，不要在正文中出現未轉義的 `<` `>`。
Part 1.2 中的 `<strong>` 標籤必須正確配對關閉。
導航連結（prev/next）請使用 `{{PREV_FILE}}` 和 `{{NEXT_FILE}}` 佔位符，我會在後處理中替換。

現在開始生成 ANO-{start_num:03d} 到 ANO-{start_num+5:03d}：
"""
    return prompt

def call_api(prompt):
    """Call the LLM API to generate episodes."""
    data = {
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": "你是一個精通中國近現代史、中國古代史和全球史的寫作助手。你的歷史知識準確無誤，同時你擅長從科幻、遊戲、系統設計等角度對歷史進行腦洞大開的重新解讀。你輸出的 HTML 結構精確、標籤配對無誤。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.85,
        "max_tokens": 32000,
    }

    req = Request(
        f"{API_BASE}/chat/completions",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    )

    resp = urlopen(req, timeout=300)
    body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]

def parse_episodes(raw_output, start_num):
    """Parse the AI output into individual episode HTML blocks."""
    episodes = []
    for i in range(6):
        num = start_num + i
        pattern = f"<!-- EPISODE START: ANO-{num:03d} -->"
        end_pattern = "<!-- EPISODE END -->"

        start_idx = raw_output.find(pattern)
        if start_idx == -1:
            print(f"WARNING: Could not find start marker for ANO-{num:03d}")
            continue

        end_idx = raw_output.find(end_pattern, start_idx)
        if end_idx == -1:
            print(f"WARNING: Could not find end marker for ANO-{num:03d}")
            content = raw_output[start_idx + len(pattern):]
        else:
            content = raw_output[start_idx + len(pattern):end_idx]

        episodes.append(content.strip())

    return episodes

def save_episode(num, html_content, slug, metadata):
    """Save an episode HTML file with nav links filled in."""
    # Build proper nav links (will be fixed by the orchestrator)
    html_content = html_content.replace("{{PREV_FILE}}", "#")
    html_content = html_content.replace("{{NEXT_FILE}}", "#")

    path = EPISODES_DIR / f"{slug}.html"
    path.write_text(html_content, encoding="utf-8")
    print(f"  Saved: {slug}.html")
    return True

def main():
    # Load backlog
    backlog = json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))

    # Get existing slugs
    existing_slugs = [f.stem for f in EPISODES_DIR.glob("*.html")]
    existing_slugs.sort()

    # Calculate next quadrants
    quadrants, new_counter = next_quadrants(backlog)

    print(f"Generating 6 episodes with quadrants: {quadrants}")

    # Build prompt
    prompt = build_prompt(quadrants, existing_slugs)

    # Call API
    print("Calling LLM API...")
    raw_output = call_api(prompt)

    # Parse episodes
    max_num = max(int(s.split("-")[0]) for s in existing_slugs)
    start_num = max_num + 1
    episodes_html = parse_episodes(raw_output, start_num)

    if len(episodes_html) < 6:
        print(f"WARNING: Only got {len(episodes_html)}/6 episodes from API")

    # Save episodes
    new_slugs = []
    for i, html in enumerate(episodes_html):
        num = start_num + i
        slug = f"{num:03d}-auto"
        save_episode(num, html, slug, {"quadrant": quadrants[i]})
        new_slugs.append(slug)

    # Update backlog
    backlog["upcoming"].extend(new_slugs)
    backlog["quadrant_counter"] = new_counter
    backlog["last_generated"] = datetime.utcnow().isoformat()

    BACKLOG_PATH.write_text(json.dumps(backlog, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done. Added {len(new_slugs)} episodes. Backlog now has {len(backlog['upcoming'])} upcoming.")

    # Output new slugs for the orchestrator
    print("NEW_SLUGS:" + ",".join(new_slugs))

if __name__ == "__main__":
    main()
