# Feature Adaptive 原始日線 (1D) 即時監控儀表盤

[![Daily Monitor & GitHub Pages](https://github.com/ethanshih/txf-feature-adaptive/actions/workflows/daily_monitor.yml/badge.svg)](https://github.com/ethanshih/txf-feature-adaptive/actions/workflows/daily_monitor.yml)

一套專為台灣加權指數（^TWII）與台指期（TXF）設計的**特徵自適應（Feature Adaptive）量化監控系統**。

每日收盤後（14:30 台灣時間）透過 GitHub Actions 自動串接盤後開高低收數據，計算微積分平穩長記憶特徵、Yang-Zhang 極差波動率百分位階與宏觀年線，自動比對各級決策閾值，發布大盤體制判斷與做多/做空/平倉/觀望診斷至 GitHub Pages。

---

## 核心特徵與演算法架構

1. **分數階微分（Fractional Differentiation, $d^*=0.30, w=50$）**：
   - 保留 88% 的歷史趨勢長記憶，同時通過 ADF 統計平穩性檢定。
2. **多尺度動態均線（Fast 15 vs Slow 70）**：
   - 捕捉平穩空間中的金叉與死叉。
3. **Z-Score 動態標準化偏離得分（60-bar lookback）**：
   - 趨勢做多門檻：$Z > -0.60$
   - 恐慌抄底門檻：$Z < -1.80$
   - 破位做空門檻：$-1.50 < Z < 0.30$
   - 力竭摸頂門檻：$Z > +2.20$
4. **Yang-Zhang 極差無偏波動率（20-bar window）**：
   - 隔夜跳空無偏估計 + 盤中漂移修正，計算 252 交易日滾動歷史百分位階（$	ext{Vol Rank} > 75\%$ 判定為極端恐慌抛售）。
5. **宏觀 200MA 牛熊均線**：長線體制過濾。
6. **Kaufman 效率比率（KER > 0.20）**：非線性碎形噪訊門閥。

---

## 快速啟動與 GitHub 部署方式

### 步驟一：推送至您的 GitHub 倉庫
```bash
git init
git add .
git commit -m "Initial commit of feature-adaptive-monitor"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### 步驟二：開啟 GitHub Pages
1. 進入該 GitHub 倉庫的 **Settings** -> **Pages**；
2. 在 **Build and deployment** 下方的 **Source** 選擇 **GitHub Actions**；
3. 完成！每個交易日 14:30 系統將自動更新並即時發佈。您也可至 Actions 頁籤點選 **Run workflow** 隨時手動觸發。

---

## 本地開發與手動執行

```bash
pip install -r requirements.txt
python run_daily.py
```
執行完畢後直接開啟 `docs/index.html` 即可檢視最新儀表盤。
