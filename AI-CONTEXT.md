# 腦洞歷史 — AI 開發上下文

## 專案概述

這是一個靜態網站系列，以「異常觀測檔案」的暗黑科幻風格，從穿越者、無限流玩家、覺醒NPC、系統管理員等腦洞角度重新解讀歷史人物與事件，每期分 Part 0-3 雙重視角（腦洞+正史）呈現。

- **網址**: https://zhuayuba.github.io/Historybug/
- **Repo**: zhuayuba/Historybug
- **本地路徑**: `/Users/linxiao/Desktop/project/灵感漫游日志/腦洞歷史/`

## 時空象限

| 象限 | CSS class | 主色 | 卡片徽章 | Dossier 值 |
|------|-----------|------|----------|------------|
| 近現代中國 | `modern` | 青 `#00e5ff` | `近現代` | `近現代中國 ▸ 核心觀測區` |
| 古代中國 | `ancient` | 金 `#e8b860` | `古代` | `古代中國 ▸ 深層掃描區` |
| 全球史 | `world` | 紫 `#b388ff` | `世界` | `全球史 ▸ 跨域觀測區` |

**穿插規則**: M-M-A-M-M-W（2近現代 → 1古代 → 2近現代 → 1世界 → 循環）

## 檔案結構

```
腦洞歷史/
├── index.html                     # 首頁：卡片網格 + 象限/類型雙層篩選器
├── css/style.css                  # 全域樣式（暗黑科幻風，CSS變數在 :root）
├── episodes/
│   ├── 001-xian-shi-bian.html    # 近現代
│   ├── 002-si-du-chishui.html    # 近現代
│   ├── 003-qin-shi-huang.html    # 古代 ★
│   ├── 004-sun-zhongshan.html    # 近現代
│   ├── 005-hong-xiuquan.html     # 近現代
│   ├── 006-da-vinci.html         # 世界 ★
│   ├── 007-feng-yuxiang.html     # 近現代
│   ├── 008-deng-xiaoping.html    # 近現代
│   ├── 009-zhu-ge-liang.html     # 古代 ★
│   ├── 010-zhou-enlai.html       # 近現代
│   ├── 011-cixi.html             # 近現代
│   ├── 012-napoleon.html         # 世界 ★
│   ├── 013-lu-xun.html           # 近現代
│   ├── 014-lin-biao.html         # 近現代
│   ├── 015-wu-zetian.html        # 古代 ★
│   └── 016-li-hongzhang.html     # 近現代
├── .github/
│   ├── workflows/lark-reminder.yml    # GitHub Action：被 cron-job.org 觸發
│   └── scripts/
│       ├── backlog.json               # 存貨隊列（upcoming + featured）
│       ├── send_lark.py               # 主流程：取號→發 Lark→檢查存貨→觸發生產
│       └── generate_episodes.py       # 調用 LLM API 生成 6 期 HTML
└── AI-CONTEXT.md                 # 本檔案
```

## 每期結構（必須嚴格遵循）

每期 HTML 從 `<header class="dossier-header">` 開始，含以下欄位：觀測對象、異常類型、時間定位、異常等級、時空象限、關聯個體、檔案狀態、tags。

四個 Part：

```
Part 0: 信號異常        — 懸疑鉤子，~150字，一個異常細節開場
Part 1: 異常觀測報告     — 1.1 類型判定 → 1.2 五個關鍵異常點 → 1.3 推演敘事(~200字) → 1.4 可信度評估
Part 2: 正史解碼        — 2.1 歷史現場(~300字) → 2.2 深層邏輯(~200字) → 2.3 史家評價+參考來源
Part 3: 二象性觀察      — 3.1 腦洞為什麼成立 → 3.2 正史為什麼可靠 → 3.3 尾聲(finale-line + ~100字結尾)
```

**硬性規則**:
- Part 2 史實必須完全準確（日期、人物、事件經過不能虛構）
- Part 1 腦洞可以天馬行空但要掛鉤真實歷史細節
- 每期結尾有 `<nav class="episode-nav">` 前後導航

## 新增一期 Checklist

1. 確定時空象限（遵循 M-M-A-M-M-W 穿插）
2. 確定 ANO 編號（當前最大 +1）
3. 建立 `episodes/NNN-slug.html`（用既有期數作模板）
4. 更新前一期和後一期的 `<nav class="episode-nav">`
5. 在 `index.html` 的 `</main>` 前（placeholder-card 前）新增卡片
6. 更新 `index.html` 統計欄（已歸檔異常數量）
7. 更新 `.github/scripts/backlog.json` 的 `upcoming` 陣列
8. 如果推送後才被 Lark 發送，要加入 backlog.json

## 部署與自動化

### 部署
- `git push main` → GitHub Pages 自動建置（~1-2分鐘）
- 網址: `https://zhuayuba.github.io/Historybug/`

### Lark 通知
- **排程**: cron-job.org → 每週二、四、六 9:03 → POST 到 GitHub workflow dispatch API
- **workflow**: `.github/workflows/lark-reminder.yml` → 執行 `send_lark.py`
- **卡片格式**: 互動卡片，含本期標題+異常類型+存貨倒數+兩個按鈕（本期檔案、全部檔案）

### 自動補貨系統
- `send_lark.py` 從 `backlog.json` 的 `upcoming` 取下一期 → 移到 `featured`
- 發送 Lark 通知（本期為 featured episode）
- 如果 `upcoming` 剩餘 ≤ 2 → 調用 `generate_episodes.py`
- `generate_episodes.py` 用 LLM API 生成 6 期，遵循 M-M-A-M-M-W 象限穿插
- 生成後 commit + push 所有新檔案 + 更新後的 backlog.json + index.html
- GitHub Pages 自動重建

### GitHub Secrets
- `LARK_WEBHOOK_URL`: 飛書機器人 webhook
- `LLM_API_KEY`: DeepSeek API key（用於自動生成內容）

### cron-job.org 設定
- URL: `https://api.github.com/repos/zhuayuba/Historybug/actions/workflows/lark-reminder.yml/dispatches`
- Method: POST
- Headers: `Authorization: Bearer <github_token>`, `Accept: application/vnd.github+json`, `Content-Type: application/json`
- Body: `{"ref": "main"}`

## 設計系統

### 顏色變數（見 `css/style.css` `:root`）
- 背景: `#08080f` (deep) / `#0f0f18` (surface) / `#12121f` (card)
- 主色: `--cyan: #00e5ff` / `--cyan-dim: #008899`
- 金色: `--gold: #e8b860` / `--gold-dim: #a07828`
- 紫色: `--world: #b388ff` / `--world-dim: #7c4dff`
- 紅色: `--red: #ff5577` / 綠色: `--green: #44cc88` / 橘色: `--text-warn: #ff8866`

### 字體
- 等寬: `SF Mono, Fira Code, Cascadia Code, JetBrains Mono, monospace`
- 中文: `Noto Sans TC, Noto Sans SC, PingFang TC, PingFang SC, Microsoft YaHei, sans-serif`
- 基礎字號: `17px`，行高 `1.8`

### 排版要點
- 卡片網格: `grid-template-columns: repeat(auto-fill, minmax(360px, 1fr))`
- 內頁最大寬度: `840px`
- 掃描線覆蓋層: `.scanlines`（fixed, z-index: 9999）
- 篩選器支援象限+類型雙層聯動

## 內容寫作規範

1. 史實引用以中國官方史書和權威學術研究為主
2. 參考來源格式: `<div class="source-note">作者《書名》；……</div>`
3. 異常等級用 `█` 字元表示，如 `████████░░ 8.6/10`
4. 腦洞可信度: low(18%)/medium(42%)/high(72%)，附一句自嘲式點評
5. 尾聲 finale-blank 用一句話收束，風格為「歷史沒有如果，但有______」
6. 時空象限值在 dossier-header 中的 class: `quadrant-modern` / `quadrant-ancient` / `quadrant-world`

## 已知的異常類型（避免重複）

機械降神、無限流玩家、平行宇宙滯留者、降維下載失敗、覺醒NPC、系統管理員、時間線導航員、負優化AI、診斷協議執行者、速通玩家、守護進程、系統格式化、時間旅行者、時間線計算者、數據溢出、權限漏洞利用
