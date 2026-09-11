# -*- coding: utf-8 -*-
"""
Dashboard Builder: Renders high-end, futuristic responsive HTML interface for GitHub Pages.
Features:
- Live Action Banner (Long / Short / Flat / Panic)
- Real-time gauge metrics (Z-Score, Vol Percentile, 200MA gap, Kaufman ER)
- Interactive Chart.js charts:
  1. Price + 200MA + Signals
  2. FracDiff Fast/Slow Momentum
  3. Stationary Z-Score with Threshold Bands
- Checklist Matrix & Reasoning Details
- Recent Signals Audit Table
"""
import os
import json
import numpy as np
import math

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feature Adaptive 原始日線 (1D) 監控儀表盤 | 台指大盤量化系統</title>
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
                        darkBg: '#0b0f19',
                        darkCard: '#111827',
                        cardBorder: '#1f2937',
                        cyanAccent: '#06b6d4',
                        emeraldAccent: '#10b981',
                        roseAccent: '#f43f5e',
                        amberAccent: '#f59e0b'
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #0b0f19; color: #e5e7eb; }
        .glass-card { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .pulse-badge { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .6; } }
    </style>
</head>
<body class="min-h-screen pb-16">

    <!-- Top Navigation -->
    <header class="border-b border-gray-800 bg-gray-900/60 sticky top-0 z-50 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
                    FA
                </div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                        Feature Adaptive 原始日線 (1D) 監控中心
                        <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">Production</span>
                    </h1>
                    <p class="text-xs text-gray-400">大盤微積分平穩長記憶・Yang-Zhang 無偏波動・狀態機即時決策</p>
                </div>
            </div>
            <div class="text-right">
                <div class="text-xs text-gray-400">最後運算更新</div>
                <div class="text-sm font-semibold text-cyan-400" id="update-date">{{ date }} 收盤</div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">

        <!-- Action Banner (Decision State) -->
        <div class="glass-card rounded-2xl p-6 relative overflow-hidden shadow-2xl">
            <div class="absolute -right-16 -top-16 w-64 h-64 rounded-full blur-3xl pointer-events-none opacity-20" style="background-color: {{ banner_color }};"></div>
            
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div class="flex items-center gap-3">
                        <span class="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider pulse-badge" style="background-color: {{ banner_bg }}; color: {{ banner_color }}; border: 1px solid {{ banner_color }};">
                            {{ action_type }}
                        </span>
                        <span class="text-xs text-gray-400">今日狀態機裁決</span>
                    </div>
                    <h2 class="text-2xl sm:text-3xl font-extrabold mt-2 tracking-tight" style="color: {{ banner_color }};">
                        {{ action_title }}
                    </h2>
                    <p class="text-gray-300 mt-2 text-sm sm:text-base leading-relaxed max-w-3xl">
                        {{ action_desc }}
                    </p>
                </div>
                <div class="flex flex-row md:flex-col items-start md:items-end justify-between border-t md:border-t-0 pt-4 md:pt-0 border-gray-800">
                    <div class="text-xs text-gray-400">當前市場體制</div>
                    <div class="text-sm font-semibold mt-1 px-3 py-1 rounded-lg bg-gray-800/80 border border-gray-700" style="color: {{ regime_color }};">
                        {{ regime }}
                    </div>
                    <div class="text-xs text-gray-400 mt-3">大盤收盤價</div>
                    <div class="text-2xl font-black text-white font-mono">{{ close_fmt }}</div>
                </div>
            </div>
        </div>

        <!-- 4 Primary Metric Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- 1. Z-Score -->
            <div class="glass-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-gray-400">分數階 Z-Score</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">d*=0.30</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono {{ z_color }}">{{ z_score_fmt }}</span>
                    <span class="text-xs text-gray-400">標準差偏離</span>
                </div>
                <div class="mt-3 text-xs text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>趨勢門檻: > -0.60</span><span class="text-cyan-400">突破多</span></div>
                    <div class="flex justify-between"><span>恐慌極值: < -1.80</span><span class="text-rose-400">超跌底</span></div>
                </div>
            </div>

            <!-- 2. Volatility Rank -->
            <div class="glass-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-gray-400">YZ 波動率百分位</span>
                    <span class="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">252D Rank</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono text-cyan-400">{{ vol_rank_fmt }}</span>
                    <span class="text-xs text-gray-400">歷史水位</span>
                </div>
                <div class="mt-3 text-xs text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>年化極差波動度:</span><span class="text-white font-mono">{{ yz_vol_fmt }}</span></div>
                    <div class="flex justify-between"><span>恐慌洗盤臨界:</span><span class="text-rose-400">> 75.0%</span></div>
                </div>
            </div>

            <!-- 3. Macro 200MA -->
            <div class="glass-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-gray-400">宏觀年線 (200MA)</span>
                    <span class="text-xs px-2 py-0.5 rounded {{ macro_badge_class }}">{{ macro_status_text }}</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-2xl font-black font-mono text-white">{{ macro_200ma_fmt }}</span>
                </div>
                <div class="mt-3 text-xs text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>與年線點數距離:</span><span class="font-mono {{ gap_color }}">{{ gap_pts_fmt }}</span></div>
                    <div class="flex justify-between"><span>年線乖離率:</span><span class="font-mono {{ gap_color }}">{{ gap_pct_fmt }}</span></div>
                </div>
            </div>

            <!-- 4. Kaufman ER -->
            <div class="glass-card rounded-xl p-5">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-gray-400">Kaufman 效率比率 (KER)</span>
                    <span class="text-xs px-2 py-0.5 rounded {{ ker_badge_class }}">{{ ker_status_text }}</span>
                </div>
                <div class="mt-3 flex items-baseline gap-2">
                    <span class="text-3xl font-black font-mono text-emerald-400">{{ kaufman_er_fmt }}</span>
                    <span class="text-xs text-gray-400">訊噪比</span>
                </div>
                <div class="mt-3 text-xs text-gray-400 space-y-1">
                    <div class="flex justify-between"><span>噪訊過濾門檻:</span><span class="text-cyan-400">> 0.200</span></div>
                    <div class="flex justify-between"><span>市場碎形狀態:</span><span class="text-white">{{ ker_fractal_text }}</span></div>
                </div>
            </div>
        </div>

        <!-- Charts Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main Chart: Price & 200MA (Span 2) -->
            <div class="glass-card rounded-2xl p-5 lg:col-span-2">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-base text-white flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                        大盤日線走勢與宏觀 200MA 均線
                    </h3>
                    <span class="text-xs text-gray-400">近 250 交易日軌跡</span>
                </div>
                <div class="h-72 sm:h-80">
                    <canvas id="priceChart"></canvas>
                </div>
            </div>

            <!-- Side Chart: Z-Score Thresholds -->
            <div class="glass-card rounded-2xl p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-bold text-base text-white flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
                        分數階 Z-Score 偏離通道
                    </h3>
                    <span class="text-xs text-gray-400">動態閾值界線</span>
                </div>
                <div class="h-72 sm:h-80">
                    <canvas id="zChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Sub Chart: Momentum Fast / Slow -->
        <div class="glass-card rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-base text-white flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    分數階微分均線動態（Fast 15 vs Slow 70）
                </h3>
                <span class="text-xs text-gray-400">平穩特徵多空交叉判定</span>
            </div>
            <div class="h-56">
                <canvas id="momentumChart"></canvas>
            </div>
        </div>

        <!-- Checklist & Diagnosis Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Signal Rule Checklist -->
            <div class="glass-card rounded-2xl p-5">
                <h3 class="font-bold text-base text-white mb-4 flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                    語法核心閾值即時檢驗清單 (Checklist)
                </h3>
                <div class="divide-y divide-gray-800">
                    {{ checklist_html }}
                </div>
            </div>

            <!-- Recent Signals Log -->
            <div class="glass-card rounded-2xl p-5">
                <h3 class="font-bold text-base text-white mb-4 flex items-center gap-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                    最近歷史狀態機信號觸發紀錄 (Audit Log)
                </h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-xs text-left text-gray-300">
                        <thead class="text-gray-400 uppercase bg-gray-800/40">
                            <tr>
                                <th class="py-2.5 px-3">日期</th>
                                <th class="py-2.5 px-3">觸發信號</th>
                                <th class="py-2.5 px-3">收盤價</th>
                                <th class="py-2.5 px-3">Z-Score</th>
                                <th class="py-2.5 px-3">判定依據</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-800">
                            {{ recent_trades_html }}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </main>

    <footer class="mt-12 text-center text-xs text-gray-500 border-t border-gray-900 pt-6">
        <p>Feature Adaptive Quantitative Research System &copy; 2026. Powered by GitHub Actions & GitHub Pages.</p>
        <p class="mt-1 text-gray-600">本系統僅供量化學術研究與客觀計量指標監控，不構成個人投資推薦與要約。</p>
    </footer>

    <!-- Chart Configuration Scripts -->
    <script>
        const chartData = {{ chart_data_json }};

        // 1. Price Chart
        new Chart(document.getElementById('priceChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: '大盤收盤價',
                        data: chartData.closes,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.05)',
                        borderWidth: 2,
                        tension: 0.1,
                        fill: true,
                        pointRadius: 0
                    },
                    {
                        label: '宏觀 200MA',
                        data: chartData.macro_200ma,
                        borderColor: '#f59e0b',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#9ca3af', font: { size: 11 } } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280', maxTicksLimit: 8 } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280' } }
                }
            }
        });

        // 2. Z-Score Chart with Thresholds
        new Chart(document.getElementById('zChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: 'Z-Score',
                        data: chartData.z_scores,
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: '做多門檻 (-0.6)',
                        data: Array(chartData.dates.length).fill(-0.6),
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0
                    },
                    {
                        label: '恐慌抄底 (-1.8)',
                        data: Array(chartData.dates.length).fill(-1.8),
                        borderColor: '#f43f5e',
                        borderWidth: 1.5,
                        borderDash: [4, 4],
                        pointRadius: 0
                    },
                    {
                        label: '力竭超買 (+2.2)',
                        data: Array(chartData.dates.length).fill(2.2),
                        borderColor: '#eab308',
                        borderWidth: 1,
                        borderDash: [3, 3],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#9ca3af', font: { size: 10 } } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280', maxTicksLimit: 5 } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280' } }
                }
            }
        });

        // 3. Momentum Fast vs Slow Chart
        new Chart(document.getElementById('momentumChart'), {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: 'FracDiff Fast MA (15)',
                        data: chartData.fd_fast,
                        borderColor: '#10b981',
                        borderWidth: 1.5,
                        pointRadius: 0
                    },
                    {
                        label: 'FracDiff Slow MA (70)',
                        data: chartData.fd_slow,
                        borderColor: '#ef4444',
                        borderWidth: 1.5,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#9ca3af', font: { size: 11 } } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280', maxTicksLimit: 8 } },
                    y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#6b7280' } }
                }
            }
        });
    </script>
</body>
</html>
"""

def build_dashboard_html(df, diag, output_path):
    """
    Build static index.html with live calculations.
    """
    # Prepare last 250 bars for charts
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
    
    # Colors according to action_badge
    if diag['action_badge'] in ['BUY_ACTION', 'HOLD_LONG']:
        banner_color = '#10b981' # emerald
        banner_bg = 'rgba(16, 185, 129, 0.15)'
    elif diag['action_badge'] in ['SELL_ACTION', 'HOLD_SHORT']:
        banner_color = '#f43f5e' # rose
        banner_bg = 'rgba(244, 63, 94, 0.15)'
    else:
        banner_color = '#f59e0b' # amber
        banner_bg = 'rgba(245, 158, 11, 0.15)'
        
    # Metrics
    z_val = diag['z_score']
    z_color = 'text-emerald-400' if z_val > -0.6 else ('text-rose-400' if z_val < -1.5 else 'text-amber-400')
    
    gap_pts = diag['close'] - diag['macro_200ma']
    gap_pct = (gap_pts / diag['macro_200ma']) * 100.0
    gap_color = 'text-emerald-400' if gap_pts > 0 else 'text-rose-400'
    macro_badge_class = 'bg-emerald-950 text-emerald-400 border border-emerald-800' if gap_pts > 0 else 'bg-rose-950 text-rose-400 border border-rose-800'
    macro_status_text = '多頭之上 (Bull)' if gap_pts > 0 else '空頭之下 (Bear)'
    
    er_val = diag['kaufman_er']
    ker_badge_class = 'bg-emerald-950 text-emerald-400 border border-emerald-800' if er_val >= 0.20 else 'bg-amber-950 text-amber-400 border border-amber-800'
    ker_status_text = '趨勢有效' if er_val >= 0.20 else '盤整雜訊'
    ker_fractal_text = '低碎形維度 (高訊噪比)' if er_val >= 0.20 else '高碎形維度 (隨機漫步)'
    
    # Checklist HTML
    checklist_rows = []
    for item in diag['checklist']:
        status_color = 'text-emerald-400' if item['pass'] else 'text-gray-400'
        icon = '✓' if item['pass'] else '○'
        checklist_rows.append(f"""
        <div class="py-3 flex items-center justify-between">
            <div>
                <div class="text-sm font-semibold text-white flex items-center gap-2">
                    <span class="{status_color} font-bold">{icon}</span>
                    {item['name']}
                </div>
                <div class="text-xs text-gray-400 mt-0.5">{item['val']}</div>
            </div>
            <div class="text-xs font-mono font-bold {status_color}">
                {item['status']}
            </div>
        </div>
        """)
    checklist_html = "".join(checklist_rows)
    
    # Recent trades HTML
    trade_rows = []
    for t in diag['recent_trades']:
        sig_color = 'text-emerald-400' if 'LE' in t['signal'] else ('text-rose-400' if 'SE' in t['signal'] else 'text-amber-400')
        trade_rows.append(f"""
        <tr class="hover:bg-gray-800/30">
            <td class="py-2.5 px-3 font-mono">{t['date']}</td>
            <td class="py-2.5 px-3 font-bold {sig_color}">{t['signal']}</td>
            <td class="py-2.5 px-3 font-mono">{t['close']}</td>
            <td class="py-2.5 px-3 font-mono">{t['z_score']}</td>
            <td class="py-2.5 px-3 text-gray-400">{t['reason']}</td>
        </tr>
        """)
    recent_trades_html = "".join(trade_rows)
    
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
        "{{ checklist_html }}": checklist_html,
        "{{ recent_trades_html }}": recent_trades_html,
        "{{ chart_data_json }}": json.dumps(chart_data)
    }
    
    for k, v in replacements.items():
        html = html.replace(k, str(v))
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"[DashboardBuilder] HTML dashboard successfully written to: {output_path}")
