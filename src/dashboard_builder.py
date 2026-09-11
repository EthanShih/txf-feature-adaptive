# -*- coding: utf-8 -*-
"""
Dashboard Builder (Light Theme / White Background):
- High-contrast, clean modern institutional aesthetic
- Dynamic font scaling controls (A-, A+, Reset) with localStorage
- Next-bar Critical Pivot Levels Alert (轉折關鍵點位計算卡片)
- Last 5 Completed Trade Signals Table (前五次交易歷史歷程)
- Interactive Chart.js charts configured for crisp light-mode readability
"""
import os
import json
import numpy as np
import math

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feature Adaptive 原始日線 (1D) 監控中心 | 台指大盤量化系統</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brandBlue: '#1e40af',
                        brandCyan: '#0284c7',
                        successGreen: '#059669',
                        dangerRed: '#dc2626',
                        warningAmber: '#d97706'
                    }
                }
            }
        }
    </script>
    <style>
        :root {
            font-size: 100%;
        }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; 
            background-color: #f8fafc; 
            color: #1e293b; 
            transition: font-size 0.15s ease-in-out;
        }
        .white-card { 
            background-color: #ffffff; 
            border: 1px solid #e2e8f0; 
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05); 
        }
        .pulse-badge { 
            animation: pulse 2.2s cubic-bezier(0.4, 0, 0.6, 1) infinite; 
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .75; } }
    </style>
</head>
<body class="min-h-screen pb-16">

    <!-- Top Navigation Header -->
    <header class="border-b border-slate-200 bg-white/90 sticky top-0 z-50 backdrop-blur-md shadow-xs">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-blue-500/20">
                    FA
                </div>
                <div>
                    <h1 class="text-base sm:text-lg font-bold tracking-tight text-slate-900 flex items-center gap-2">
                        Feature Adaptive 原始日線 (1D) 監控中心
                        <span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">Live Production</span>
                    </h1>
                    <p class="text-xs text-slate-500">大盤微積分平穩長記憶・Yang-Zhang 無偏波動・狀態機即時決策</p>
                </div>
            </div>
            
            <div class="flex items-center space-x-3 sm:space-x-4">
                <!-- Font Zoom Toolbar -->
                <div class="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
                    <button onclick="changeFontSize(-5)" title="縮小字體" class="px-2 py-0.5 text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-white rounded transition">
                        A-
                    </button>
                    <button onclick="resetFontSize()" title="重置字體" class="px-1.5 py-0.5 text-xs font-medium text-slate-400 hover:text-slate-800 rounded transition">
                        100%
                    </button>
                    <button onclick="changeFontSize(5)" title="放大字體" class="px-2 py-0.5 text-xs font-bold text-slate-600 hover:text-slate-900 hover:bg-white rounded transition">
                        A+
                    </button>
                </div>

                <div class="text-right border-l border-slate-200 pl-3 sm:pl-4">
                    <div class="text-xs text-slate-400">結算更新</div>
                    <div class="text-xs sm:text-sm font-semibold text-blue-600" id="update-date">{{ date }} 收盤</div>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">

        <!-- Action Banner (Decision State) -->
        <div class="white-card rounded-2xl p-6 relative overflow-hidden border-l-8" style="border-left-color: {{ banner_color }};">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div class="flex items-center gap-3">
                        <span class="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider pulse-badge" style="background-color: {{ banner_bg }}; color: {{ banner_color }}; border: 1px solid {{ banner_color }};">
                            {{ action_type }}
                        </span>
                        <span class="text-xs text-slate-500">今日狀態機裁決</span>
                    </div>
                    <h2 class="text-2xl sm:text-3xl font-extrabold mt-2 tracking-tight" style="color: {{ banner_color }};">
                        {{ action_title }}
                    </h2>
                    <p class="text-slate-700 mt-2 text-sm sm:text-base leading-relaxed max-w-3xl">
                        {{ action_desc }}
                    </p>
                </div>
                <div class="flex flex-row md:flex-col items-start md:items-end justify-between border-t md:border-t-0 pt-4 md:pt-0 border-slate-100">
                    <div class="text-xs text-slate-400">當前市場體制</div>
                    <div class="text-sm font-semibold mt-1 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200" style="color: {{ regime_color }};">
                        {{ regime }}
                    </div>
                    <div class="text-xs text-slate-400 mt-3">大盤最新收盤價</div>
                    <div class="text-3xl font-black text-slate-900 font-mono tracking-tight">{{ close_fmt }}</div>
                </div>
            </div>
        </div>

        <!-- NEW SECTION: Next Bar Critical Pivot Levels (轉折關鍵點位計算卡片) -->
        <div class="white-card rounded-2xl p-6 shadow-sm border border-slate-200">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
                <div>
                    <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-blue-600"></span>
                        次一交易日轉折關鍵點位預警（Pivot Key Levels Alert）
                    </h3>
                    <p class="text-xs text-slate-500 mt-0.5">基於分數階代數方程與狀態機條件反向求根，精確計算明日行情生變之臨界點位與安全護城河</p>
                </div>
                <span class="text-xs px-2.5 py-1 rounded bg-slate-100 text-slate-600 font-mono font-medium">嚴格零未來函數</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
                {{ pivots_html }}
            </div>
        </div>

        <!-- 4 Primary Metric Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- 1. Z-Score -->
            <div class="white-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-500">分數階 Z-Score</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono font-medium">d*=0.30</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono {{ z_color }}">{{ z_score_fmt }}</span>
                    <span class="text-xs text-slate-400">標準差偏離</span>
                </div>
                <div class="mt-3 text-xs text-slate-500 space-y-1">
                    <div class="flex justify-between"><span>順勢多門檻: > -0.60</span><span class="text-blue-600 font-medium">順勢多</span></div>
                    <div class="flex justify-between"><span>恐慌底門檻: < -1.80</span><span class="text-rose-600 font-medium">抄底區</span></div>
                </div>
            </div>

            <!-- 2. Volatility Rank -->
            <div class="white-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-500">YZ 波動率百分位</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-mono font-medium">252D Rank</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono text-cyan-600">{{ vol_rank_fmt }}</span>
                    <span class="text-xs text-slate-400">歷史水位</span>
                </div>
                <div class="mt-3 text-xs text-slate-500 space-y-1">
                    <div class="flex justify-between"><span>年化極差波動度:</span><span class="text-slate-800 font-mono font-medium">{{ yz_vol_fmt }}</span></div>
                    <div class="flex justify-between"><span>恐慌洗盤警戒:</span><span class="text-rose-600 font-medium">> 75.0%</span></div>
                </div>
            </div>

            <!-- 3. Macro 200MA -->
            <div class="white-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-500">宏觀年線 (200MA)</span>
                    <span class="text-xs px-2 py-0.5 rounded {{ macro_badge_class }}">{{ macro_status_text }}</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-2xl font-black font-mono text-slate-900">{{ macro_200ma_fmt }}</span>
                </div>
                <div class="mt-3 text-xs text-slate-500 space-y-1">
                    <div class="flex justify-between"><span>與年線點數距離:</span><span class="font-mono font-medium {{ gap_color }}">{{ gap_pts_fmt }}</span></div>
                    <div class="flex justify-between"><span>年線乖離率:</span><span class="font-mono font-medium {{ gap_color }}">{{ gap_pct_fmt }}</span></div>
                </div>
            </div>

            <!-- 4. Kaufman ER -->
            <div class="white-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-500">Kaufman 效率比率 (KER)</span>
                    <span class="text-xs px-2 py-0.5 rounded {{ ker_badge_class }}">{{ ker_status_text }}</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono text-emerald-600">{{ kaufman_er_fmt }}</span>
                    <span class="text-xs text-slate-400">訊噪比</span>
                </div>
                <div class="mt-3 text-xs text-slate-500 space-y-1">
                    <div class="flex justify-between"><span>噪訊過濾門檻:</span><span class="text-blue-600 font-medium">> 0.200</span></div>
                    <div class="flex justify-between"><span>市場碎形維度:</span><span class="text-slate-800 font-medium">{{ ker_fractal_text }}</span></div>
                </div>
            </div>
        </div>

        <!-- Charts Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main Chart: Price & 200MA (Span 2) -->
            <div class="white-card rounded-2xl p-5 lg:col-span-2 shadow-xs">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-base text-slate-900 flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                        大盤日線走勢與宏觀 200MA 年線
                    </h3>
                    <span class="text-xs text-slate-500">近 250 交易日真實軌跡</span>
                </div>
                <div class="h-72 sm:h-80">
                    <canvas id="priceChart"></canvas>
                </div>
            </div>

            <!-- Side Chart: Z-Score Thresholds -->
            <div class="white-card rounded-2xl p-5 shadow-xs">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-base text-slate-900 flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-purple-600"></span>
                        分數階 Z-Score 偏離通道
                    </h3>
                    <span class="text-xs text-slate-500">動態閾值界線</span>
                </div>
                <div class="h-72 sm:h-80">
                    <canvas id="zChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Sub Chart: Momentum Fast / Slow -->
        <div class="white-card rounded-2xl p-5 shadow-xs">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-base text-slate-900 flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span>
                    分數階微分均線動態（Fast 15 vs Slow 70）
                </h3>
                <span class="text-xs text-slate-500">平穩特徵多空交叉判定</span>
            </div>
            <div class="h-56">
                <canvas id="momentumChart"></canvas>
            </div>
        </div>

        <!-- NEW SECTION: Last 5 Trade Signals History (前五次交易訊號歷史紀錄) -->
        <div class="white-card rounded-2xl p-6 shadow-sm">
            <div class="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                    <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full bg-rose-600"></span>
                        前五次交易訊號發出與平倉歷程（Last 5 Completed Signals）
                    </h3>
                    <p class="text-xs text-slate-500 mt-0.5">狀態機精確交易配對清單，詳實記錄進出場時間、點位、盈虧與出場歸因</p>
                </div>
                <span class="text-xs px-2.5 py-1 rounded bg-slate-100 text-slate-600 font-mono font-medium">大台 200元/點計</span>
            </div>

            <!-- Current Active Position Banner if present -->
            {{ active_position_banner }}

            <div class="overflow-x-auto mt-4">
                <table class="w-full text-xs sm:text-sm text-left text-slate-700">
                    <thead class="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200 font-semibold">
                        <tr>
                            <th class="py-3 px-3">序號</th>
                            <th class="py-3 px-3">部位</th>
                            <th class="py-3 px-3">進場日期</th>
                            <th class="py-3 px-3">進場信號</th>
                            <th class="py-3 px-3">進場價</th>
                            <th class="py-3 px-3">出場日期</th>
                            <th class="py-3 px-3">出場原因</th>
                            <th class="py-3 px-3">出場價</th>
                            <th class="py-3 px-3 text-right">點數損益</th>
                            <th class="py-3 px-3 text-right">淨損益 (TWD)</th>
                            <th class="py-3 px-3 text-center">結果</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        {{ last_5_trades_html }}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Checklist Section -->
        <div class="white-card rounded-2xl p-6 shadow-sm">
            <h3 class="font-bold text-base text-slate-900 mb-3 flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                語法核心閾值即時檢驗清單 (Live Checklist)
            </h3>
            <div class="divide-y divide-slate-100">
                {{ checklist_html }}
            </div>
        </div>

    </main>

    <footer class="mt-12 text-center text-xs text-slate-400 border-t border-slate-200 pt-6">
        <p>Feature Adaptive Quantitative Research System &copy; 2026. Powered by GitHub Actions & GitHub Pages.</p>
        <p class="mt-1 text-slate-400">本系統僅供量化計量學術研究與客觀指標監控，不構成任何個人投資買賣要約。</p>
    </footer>

    <!-- Font Scaling & Chart Scripts -->
    <script>
        // 1. Font Zoom Scaling Controller
        let currentZoom = 100;
        function applyZoom() {
            document.documentElement.style.fontSize = currentZoom + '%';
        }
        function changeFontSize(delta) {
            currentZoom = Math.min(Math.max(currentZoom + delta, 80), 140);
            applyZoom();
            localStorage.setItem('fa_font_zoom', currentZoom);
        }
        function resetFontSize() {
            currentZoom = 100;
            applyZoom();
            localStorage.removeItem('fa_font_zoom');
        }
        // Load saved zoom preference
        const savedZoom = localStorage.getItem('fa_font_zoom');
        if (savedZoom) {
            currentZoom = parseInt(savedZoom, 10);
            applyZoom();
        }

        // 2. Interactive Charts
        const chartData = {{ chart_data_json }};

        // Price Chart
        new Chart(document.getElementById('priceChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: '大盤收盤價',
                        data: chartData.closes,
                        borderColor: '#0284c7',
                        backgroundColor: 'rgba(2, 132, 199, 0.06)',
                        borderWidth: 2,
                        tension: 0.1,
                        fill: true,
                        pointRadius: 0
                    },
                    {
                        label: '宏觀 200MA',
                        data: chartData.macro_200ma,
                        borderColor: '#d97706',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#475569', font: { size: 11, weight: 'bold' } } } },
                scales: {
                    x: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
                    y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
                }
            }
        });

        // Z-Score Chart
        new Chart(document.getElementById('zChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: 'Z-Score',
                        data: chartData.z_scores,
                        borderColor: '#7c3aed',
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: '做多門檻 (-0.6)',
                        data: Array(chartData.dates.length).fill(-0.6),
                        borderColor: '#0284c7',
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0
                    },
                    {
                        label: '恐慌抄底 (-1.8)',
                        data: Array(chartData.dates.length).fill(-1.8),
                        borderColor: '#e11d48',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        pointRadius: 0
                    },
                    {
                        label: '力竭超買 (+2.2)',
                        data: Array(chartData.dates.length).fill(2.2),
                        borderColor: '#d97706',
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#475569', font: { size: 10, weight: 'bold' } } } },
                scales: {
                    x: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b', maxTicksLimit: 5 } },
                    y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
                }
            }
        });

        // Momentum Fast vs Slow Chart
        new Chart(document.getElementById('momentumChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: 'FracDiff Fast MA (15)',
                        data: chartData.fd_fast,
                        borderColor: '#059669',
                        borderWidth: 1.5,
                        pointRadius: 0
                    },
                    {
                        label: 'FracDiff Slow MA (70)',
                        data: chartData.fd_slow,
                        borderColor: '#dc2626',
                        borderWidth: 1.5,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#475569', font: { size: 11, weight: 'bold' } } } },
                scales: {
                    x: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
                    y: { grid: { color: '#f1f5f9' }, ticks: { color: '#64748b' } }
                }
            }
        });
    </script>
</body>
</html>
"""

def build_dashboard_html(df, diag, output_path):
    """
    Build static index.html with light theme, font +/- controls, pivot levels, and last 5 trades history.
    """
    plot_df = df.iloc[-250:].copy()
    dates = [d.strftime('%Y-%m-%d') for d in plot_df.index]
    closes = [round(float(c), 1) for c in plot_df['close']]
    macro_200 = [round(float(m), 1) if not np.isnan(m) else None for m in plot_df['macro_200ma']]
    z_scores = [round(float(z), 2) for z in plot_df['z_score']]
    fd_fast = [round(float(f), 4) for f in plot_df['fd_fast']]
    fd_slow = [round(float(s), 4) for s in plot_df['fd_slow']]
    
    chart_data = {
        "dates": dates,
        "closes": closes,
        "macro_200ma": macro_200,
        "z_scores": z_scores,
        "fd_fast": fd_fast,
        "fd_slow": fd_slow
    }
    
    # Theme colors for Action Banner
    if diag['action_badge'] in ['BUY_ACTION', 'HOLD_LONG']:
        banner_color = '#059669' # green
        banner_bg = '#ecfdf5'
    elif diag['action_badge'] in ['SELL_ACTION', 'HOLD_SHORT']:
        banner_color = '#dc2626' # red
        banner_bg = '#fef2f2'
    else:
        banner_color = '#d97706' # amber
        banner_bg = '#fffbeb'
        
    z_val = diag['z_score']
    z_color = 'text-emerald-600' if z_val > -0.6 else ('text-rose-600' if z_val < -1.5 else 'text-amber-600')
    
    gap_pts = diag['close'] - diag['macro_200ma']
    gap_pct = (gap_pts / diag['macro_200ma']) * 100.0
    gap_color = 'text-emerald-600' if gap_pts > 0 else 'text-rose-600'
    macro_badge_class = 'bg-emerald-50 text-emerald-700 border border-emerald-200' if gap_pts > 0 else 'bg-rose-50 text-rose-700 border border-rose-200'
    macro_status_text = '多頭之上 (Bull)' if gap_pts > 0 else '空頭之下 (Bear)'
    
    er_val = diag['kaufman_er']
    ker_badge_class = 'bg-emerald-50 text-emerald-700 border border-emerald-200' if er_val >= 0.20 else 'bg-amber-50 text-amber-700 border border-amber-200'
    ker_status_text = '趨勢有效' if er_val >= 0.20 else '盤整雜訊'
    ker_fractal_text = '低碎形維度 (高訊噪比)' if er_val >= 0.20 else '高碎形維度 (隨機漫步)'
    
    # 1. Pivots HTML Cards
    pivots_cards = []
    for p in diag['pivots']:
        gap_class = "text-rose-600 font-bold" if p['gap_pts'] < 0 else "text-emerald-600 font-bold"
        pivots_cards.append(f"""
        <div class="rounded-xl p-4 bg-slate-50 border border-slate-200 relative overflow-hidden">
            <div class="text-xs font-semibold px-2 py-0.5 rounded inline-block border {p['badge_class']}">{p['type']}</div>
            <div class="text-2xl font-black text-slate-900 font-mono mt-2">{p['price']:,.0f} 點</div>
            <div class="text-xs text-slate-500 mt-1 flex items-center justify-between">
                <span>需{p['direction']}:</span>
                <span class="{gap_class} font-mono">{p['gap_pts']:+,.0f} 點 ({p['gap_pct']:+.2f}%)</span>
            </div>
            <div class="text-xs text-slate-400 mt-2 border-t border-slate-200 pt-2">{p['desc']}</div>
        </div>
        """)
    pivots_html = "".join(pivots_cards)

    # 2. Last 5 Trades Table HTML
    trade_rows = []
    for i, t in enumerate(diag['last_5_trades']):
        pos_badge = "bg-emerald-50 text-emerald-700 border-emerald-200" if t['pos_label'] == "做多" else "bg-rose-50 text-rose-700 border-rose-200"
        res_badge = "bg-emerald-100 text-emerald-800 font-bold" if t['is_win'] else "bg-rose-100 text-rose-800 font-bold"
        res_text = "獲利 WIN" if t['is_win'] else "虧損 LOSS"
        pnl_color = "text-emerald-600 font-bold" if t['is_win'] else "text-rose-600 font-bold"
        
        trade_rows.append(f"""
        <tr class="hover:bg-slate-50/80 transition">
            <td class="py-3 px-3 font-mono text-slate-400">#{len(diag['last_5_trades']) - i}</td>
            <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-xs border {pos_badge} font-bold">{t['pos_label']}</span></td>
            <td class="py-3 px-3 font-mono">{t['entry_date']}</td>
            <td class="py-3 px-3 font-semibold text-slate-800">{t['entry_signal']}</td>
            <td class="py-3 px-3 font-mono font-medium">{t['entry_price']}</td>
            <td class="py-3 px-3 font-mono">{t['exit_date']}</td>
            <td class="py-3 px-3 text-slate-600 text-xs">{t['exit_reason']}</td>
            <td class="py-3 px-3 font-mono font-medium">{t['exit_price']}</td>
            <td class="py-3 px-3 font-mono text-right {pnl_color}">{t['points']} 點</td>
            <td class="py-3 px-3 font-mono text-right {pnl_color}">{t['pnl']}</td>
            <td class="py-3 px-3 text-center"><span class="px-2 py-0.5 rounded text-xs {res_badge}">{res_text}</span></td>
        </tr>
        """)
    last_5_trades_html = "".join(trade_rows)
    
    # Active position banner if currently holding
    active_position_banner = ""
    if diag.get('active_trade') is not None:
        at = diag['active_trade']
        pnl_color = "text-emerald-600" if at['is_win'] else "text-rose-600"
        active_position_banner = f"""
        <div class="mt-4 p-4 rounded-xl bg-blue-50/80 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex items-center gap-3">
                <span class="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs uppercase pulse-badge">進行中部位 (Active)</span>
                <span class="text-sm font-bold text-slate-800">{at['entry_date']} 發出 {at['pos_label']} ({at['entry_signal']}) 於 {at['entry_price']} 點</span>
            </div>
            <div class="flex items-center gap-4 text-xs sm:text-sm">
                <span class="text-slate-500">現價: <strong class="font-mono text-slate-900">{at['current_price']}</strong></span>
                <span class="text-slate-500">未實現損益: <strong class="font-mono {pnl_color} text-base">{at['unrealized_points']} 點 ({at['unrealized_pnl']})</strong></span>
            </div>
        </div>
        """

    # 3. Checklist HTML
    checklist_rows = []
    for item in diag['checklist']:
        status_color = 'text-emerald-600 font-bold' if item['pass'] else 'text-slate-400 font-medium'
        icon = '✓' if item['pass'] else '○'
        checklist_rows.append(f"""
        <div class="py-3 flex items-center justify-between">
            <div>
                <div class="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <span class="{status_color}">{icon}</span>
                    {item['name']}
                </div>
                <div class="text-xs text-slate-500 mt-0.5">{item['val']}</div>
            </div>
            <div class="text-xs font-mono {status_color}">
                {item['status']}
            </div>
        </div>
        """)
    checklist_html = "".join(checklist_rows)

    # Render final HTML
    html = HTML_TEMPLATE
    replacements = {
        "{{ date }}": diag['date'],
        "{{ banner_color }}": banner_color,
        "{{ banner_bg }}": banner_bg,
        "{{ action_type }}": diag['action_type'],
        "{{ action_title }}": diag['action_title'],
        "{{ action_desc }}": diag['action_desc'],
        "{{ regime }}": diag['regime'],
        "{{ regime_color }}": diag['regime_color'],
        "{{ close_fmt }}": f"{diag['close']:,.0f}",
        "{{ z_score_fmt }}": f"{diag['z_score']:+.2f}",
        "{{ z_color }}": z_color,
        "{{ vol_rank_fmt }}": f"{diag['vol_percentile']*100:.1f}%",
        "{{ yz_vol_fmt }}": f"{diag['yz_vol']*100:.1f}%",
        "{{ macro_200ma_fmt }}": f"{diag['macro_200ma']:,.0f}",
        "{{ macro_badge_class }}": macro_badge_class,
        "{{ macro_status_text }}": macro_status_text,
        "{{ gap_pts_fmt }}": f"{gap_pts:+,.0f} 點",
        "{{ gap_pct_fmt }}": f"{gap_pct:+.2f}%",
        "{{ gap_color }}": gap_color,
        "{{ kaufman_er_fmt }}": f"{diag['kaufman_er']:.3f}",
        "{{ ker_badge_class }}": ker_badge_class,
        "{{ ker_status_text }}": ker_status_text,
        "{{ ker_fractal_text }}": ker_fractal_text,
        "{{ pivots_html }}": pivots_html,
        "{{ active_position_banner }}": active_position_banner,
        "{{ last_5_trades_html }}": last_5_trades_html,
        "{{ checklist_html }}": checklist_html,
        "{{ chart_data_json }}": json.dumps(chart_data)
    }
    
    for k, v in replacements.items():
        html = html.replace(k, str(v))
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"[DashboardBuilder] HTML dashboard successfully written to: {output_path}")
