# -*- coding: utf-8 -*-
"""
Decision Engine:
- MultiCharts Mutex State-Machine Cascade
- Analytical/Numerical Solver for Next Bar Pivot Critical Levels (轉折關鍵點位)
- Complete Historical Trade Pairing (Extract Last 5 Completed Trades)
"""
import pandas as pd
import numpy as np
from scipy.optimize import brentq

class DecisionEngine:
    def __init__(self,
                 z_panic_thresh=-1.8,
                 vol_panic_thresh=0.75,
                 z_trend_thresh=-0.6,
                 z_short_min=-1.5,
                 z_short_max=0.3,
                 z_overbought_thresh=2.2,
                 vol_exhaust_thresh=0.35,
                 er_filter_thresh=0.20):
        self.z_panic_thresh = z_panic_thresh
        self.vol_panic_thresh = vol_panic_thresh
        self.z_trend_thresh = z_trend_thresh
        self.z_short_min = z_short_min
        self.z_short_max = z_short_max
        self.z_overbought_thresh = z_overbought_thresh
        self.vol_exhaust_thresh = vol_exhaust_thresh
        self.er_filter_thresh = er_filter_thresh

    def evaluate_state_machine(self, df):
        """
        Replay state machine through the dataset to determine historical states,
        trade records, and today's fresh decision.
        """
        n = len(df)
        states = [0] * n # 1 = Long, -1 = Short, 0 = Flat
        signals = [""] * n
        reasons = [""] * n
        
        pos = 0
        
        for i in range(1, n):
            row = df.iloc[i]
            z = row['z_score']
            vp = row['vol_percentile']
            fast = row['fd_fast']
            slow = row['fd_slow']
            mb = row['macro_bull']
            
            next_pos = pos
            sig = ""
            rsn = ""
            
            # 1. Cascade: Panic Long (Highest Priority)
            if z < self.z_panic_thresh and vp > self.vol_panic_thresh:
                next_pos = 1
                sig = "Panic_LE"
                rsn = f"觸發恐慌極端抄底 (Z: {z:.2f} < {self.z_panic_thresh}, 波動率: {vp*100:.1f}% > {self.vol_panic_thresh*100:.0f}%)"
            # 2. Trend Long
            elif mb and (fast > slow) and (z > self.z_trend_thresh):
                next_pos = 1
                sig = "Trend_LE"
                rsn = f"站上年線且動量金叉順勢做多 (Close > 200MA, Fast > Slow, Z: {z:.2f} > {self.z_trend_thresh})"
            # 3. Bear Breakdown Short
            elif (not mb) and (fast < slow) and (z > self.z_short_min) and (z < self.z_short_max):
                next_pos = -1
                sig = "Breakdown_SE"
                rsn = f"跌破年線且動量死叉破位做空 (Close <= 200MA, Fast < Slow, Z: {z:.2f} 於 [{self.z_short_min}, {self.z_short_max}])"
            # 4. Exhaustion Short
            elif z > self.z_overbought_thresh and vp < self.vol_exhaust_thresh:
                next_pos = -1
                sig = "Exhaustion_SE"
                rsn = f"極度超買但流動性枯竭摸頂做空 (Z: {z:.2f} > {self.z_overbought_thresh}, 波動率: {vp*100:.1f}% < {self.vol_exhaust_thresh*100:.0f}%)"
            # 5. Long Exit
            elif pos == 1 and ((fast < slow) or (not mb and z < 0.0)):
                next_pos = 0
                sig = "Exit_LX"
                if fast < slow:
                    rsn = f"多單平倉：快線跌破慢線死叉 (Fast: {fast:.4f} < Slow: {slow:.4f})"
                else:
                    rsn = f"多單平倉：跌破年線且動量轉負 (Close <= 200MA 且 Z < 0)"
            # 6. Short Exit
            elif pos == -1 and ((z < self.z_panic_thresh) or (fast > slow) or (mb and z > 0.2)):
                next_pos = 0
                sig = "Exit_SX"
                if z < self.z_panic_thresh:
                    rsn = f"空單回補：殺入極端超跌恐慌區 (Z: {z:.2f} < {self.z_panic_thresh})"
                elif fast > slow:
                    rsn = f"空單回補：快線金叉慢線 (Fast: {fast:.4f} > Slow: {slow:.4f})"
                else:
                    rsn = f"空單回補：站回年線且動量轉正 (Close > 200MA 且 Z > 0.2)"
                    
            states[i] = next_pos
            signals[i] = sig
            reasons[i] = rsn
            pos = next_pos
            
        df['state_pos'] = states
        df['signal'] = signals
        df['reason'] = reasons
        
        return df

    def extract_trade_history(self, df):
        """
        Pair up entries and exits to extract all completed trades.
        """
        trades = []
        current_trade = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            pos = row['state_pos']
            sig = row['signal']
            rsn = row['reason']
            price = row['close']
            date_str = row.name.strftime('%Y-%m-%d')
            
            # Check exit for existing trade
            if current_trade is not None:
                prev_pos = current_trade['pos']
                if pos == 0 or (pos != prev_pos and pos != 0):
                    current_trade['exit_date'] = date_str
                    current_trade['exit_price'] = price
                    current_trade['exit_signal'] = sig if sig != '' else ('Exit_LX' if prev_pos == 1 else 'Exit_SX')
                    current_trade['exit_reason'] = rsn if rsn != '' else f'翻轉為{pos}'
                    
                    pts = (current_trade['exit_price'] - current_trade['entry_price']) if prev_pos == 1 else (current_trade['entry_price'] - current_trade['exit_price'])
                    pnl = pts * 200.0 - 200.0
                    current_trade['points'] = pts
                    current_trade['pnl'] = pnl
                    trades.append(current_trade)
                    current_trade = None
                    
            # Open new trade
            if pos != 0 and current_trade is None and ('LE' in sig or 'SE' in sig):
                current_trade = {
                    'entry_date': date_str,
                    'pos': pos,
                    'entry_signal': sig,
                    'entry_price': price,
                    'entry_reason': rsn
                }
                
        return trades, current_trade

    def calculate_pivot_levels(self, df):
        """
        Reverse-solve for critical pivot price levels on the NEXT bar:
        1. Death cross price (Fast SMA 15 == Slow SMA 70) -> Long Exit
        2. 200MA break price (Close == 200MA) -> Bearish regime
        3. Z-Score = 2.2 price -> Exhaustion Short threshold
        4. Z-Score = -1.8 price -> Panic Long threshold
        """
        w = 50
        d = 0.30
        weights = np.zeros(w)
        weights[0] = 1.0
        for k in range(1, w):
            weights[k] = -weights[k-1] * (d - k + 1.0) / float(k)

        def get_next_bar_metrics(p_next):
            closes = np.append(df['close'].values, p_next)
            window_log_closes = np.log(np.maximum(closes[-w:], 1e-8))[::-1]
            fd_last = np.dot(weights, window_log_closes)
            
            past_fds = df['frac_diff'].values
            all_fds = np.append(past_fds, fd_last)
            
            fast = np.mean(all_fds[-15:])
            slow = np.mean(all_fds[-70:])
            std = np.std(all_fds[-60:], ddof=1)
            z = (fd_last - slow) / (std if std > 1e-8 else 1.0)
            ma200 = np.mean(closes[-200:])
            return fast, slow, z, ma200

        curr_p = df['close'].iloc[-1]
        
        # 1. Death Cross
        try:
            p_death = brentq(lambda p: get_next_bar_metrics(p)[0] - get_next_bar_metrics(p)[1], 1000, 250000)
        except Exception:
            p_death = None
            
        # 2. 200MA Cross
        p_200ma = float(np.sum(df['close'].values[-199:]) / 199.0)
        
        # 3. Z = 2.2
        try:
            p_z22 = brentq(lambda p: get_next_bar_metrics(p)[2] - self.z_overbought_thresh, 10000, 350000)
        except Exception:
            p_z22 = None
            
        # 4. Z = -1.8
        try:
            p_z18 = brentq(lambda p: get_next_bar_metrics(p)[2] - self.z_panic_thresh, 1000, 250000)
        except Exception:
            p_z18 = None
            
        pivots = []
        if p_death is not None:
            gap = p_death - curr_p
            pivots.append({
                "type": "多單平倉死叉警戒線",
                "condition": "快線跌破慢線 (Fast < Slow)",
                "price": round(p_death, 1),
                "gap_pts": round(gap, 1),
                "gap_pct": round(gap / curr_p * 100.0, 2),
                "direction": "下跌" if gap < 0 else "上漲",
                "badge_class": "bg-rose-50 text-rose-700 border-rose-200",
                "accent_color": "#e11d48",
                "desc": "若次日收盤跌破此點位，分數階均線將翻為死叉，觸發多單平倉出場。"
            })
            
        gap_200 = p_200ma - curr_p
        pivots.append({
            "type": "宏觀年線轉空警戒線",
            "condition": "跌破 200MA (Close <= 200MA)",
            "price": round(p_200ma, 1),
            "gap_pts": round(gap_200, 1),
            "gap_pct": round(gap_200 / curr_p * 100.0, 2),
            "direction": "下跌" if gap_200 < 0 else "上漲",
            "badge_class": "bg-amber-50 text-amber-700 border-amber-200",
            "accent_color": "#d97706",
            "desc": "大盤長線牛熊分水嶺。跌破後宏觀體制翻為空頭，禁止順勢做多。"
        })
        
        if p_z22 is not None:
            gap_z22 = p_z22 - curr_p
            pivots.append({
                "type": "極端超買摸頂放空臨界",
                "condition": "Z-Score >= +2.20 (且波動萎縮)",
                "price": round(p_z22, 1),
                "gap_pts": round(gap_z22, 1),
                "gap_pct": round(gap_z22 / curr_p * 100.0, 2),
                "direction": "上漲" if gap_z22 > 0 else "下跌",
                "badge_class": "bg-purple-50 text-purple-700 border-purple-200",
                "accent_color": "#7c3aed",
                "desc": "動能極致透支。若達此點位且成交波動萎縮，觸發摸頂空單。"
            })
            
        if p_z18 is not None:
            gap_z18 = p_z18 - curr_p
            pivots.append({
                "type": "恐慌超跌抄底臨界線",
                "condition": "Z-Score <= -1.80 (且波動爆衝)",
                "price": round(p_z18, 1),
                "gap_pts": round(gap_z18, 1),
                "gap_pct": round(gap_z18 / curr_p * 100.0, 2),
                "direction": "下跌" if gap_z18 < 0 else "上漲",
                "badge_class": "bg-pink-50 text-pink-700 border-pink-200",
                "accent_color": "#db2777",
                "desc": "若遭遇黑天鵝暴跌至此，將觸發高勝率逆勢抄底買單。"
            })

        return pivots

    def generate_daily_diagnosis(self, df):
        """
        Generate complete daily diagnostic bundle.
        """
        df = self.evaluate_state_machine(df)
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        pos = today['state_pos']
        prev_pos = yesterday['state_pos']
        fresh_signal = today['signal']
        
        if fresh_signal != "":
            if "LE" in fresh_signal:
                action_badge = "BUY_ACTION"
                action_title = "【積極做多信號觸發】"
                action_type = "多單進場" if prev_pos != 1 else "多單續抱確認"
            elif "SE" in fresh_signal:
                action_badge = "SELL_ACTION"
                action_title = "【積極放空信號觸發】"
                action_type = "空單進場" if prev_pos != -1 else "空單續抱確認"
            else:
                action_badge = "EXIT_ACTION"
                action_title = "【平倉退場信號觸發】"
                action_type = "平倉空手觀望"
            action_desc = today['reason']
        else:
            if pos == 1:
                action_badge = "HOLD_LONG"
                action_title = "【維持多單續抱】"
                action_type = "持有多單"
                action_desc = f"當前處於多頭動量延續格局（Z-Score: {today['z_score']:+.2f}，200MA 上方），尚未觸發平倉條件。"
            elif pos == -1:
                action_badge = "HOLD_SHORT"
                action_title = "【維持空單續抱】"
                action_type = "持有空單"
                action_desc = f"當前處於空頭結構（200MA 下方），尚未觸發回補條件。"
            else:
                action_badge = "HOLD_FLAT"
                action_title = "【維持空手觀望】"
                action_type = "空手觀望"
                action_desc = f"目前市場處於整理未觸發突破區間，無有效多空邊界，保持空手耐性觀望。"
                
        # Market Regime
        if today['macro_bull']:
            if today['z_score'] > 1.5:
                regime = "強勢多頭加速段 (Strong Bullish Acceleration)"
                regime_color = "#059669"
            elif today['z_score'] > -0.6:
                regime = "穩健多頭波段震盪 (Healthy Bullish Swing)"
                regime_color = "#0284c7"
            else:
                regime = "多頭回檔深洗整理 (Bullish Pullback)"
                regime_color = "#d97706"
        else:
            if today['z_score'] < -1.8 and today['vol_percentile'] > 0.75:
                regime = "恐慌崩跌超跌極限區 (Extreme Panic Selling)"
                regime_color = "#db2777"
            elif today['z_score'] < -0.5:
                regime = "空頭波段主跌結構 (Bearish Markdown Structure)"
                regime_color = "#dc2626"
            else:
                regime = "空頭弱勢反彈整理 (Weak Bearish Rebound)"
                regime_color = "#b91c1c"

        gap_200ma_pts = today['close'] - today['macro_200ma']
        gap_200ma_pct = (gap_200ma_pts / today['macro_200ma']) * 100.0
        
        # Checklists
        checklist = [
            {
                "name": "宏觀 200MA 牛熊分界",
                "status": "多頭之上 (Bullish)" if today['macro_bull'] else "空頭之下 (Bearish)",
                "val": f"現價 {today['close']:,.0f} vs 年線 {today['macro_200ma']:,.0f} ({gap_200ma_pct:+.2f}%)",
                "pass": bool(today['macro_bull'])
            },
            {
                "name": "分數階均線排列 (Fast vs Slow)",
                "status": "動量金叉多頭 (Golden Cross)" if today['fd_fast'] > today['fd_slow'] else "動量死叉空頭 (Death Cross)",
                "val": f"Fast(15): {today['fd_fast']:.4f} | Slow(70): {today['fd_slow']:.4f}",
                "pass": bool(today['fd_fast'] > today['fd_slow'])
            },
            {
                "name": "分數階 Z-Score 偏離階",
                "status": f"{today['z_score']:+.2f} σ",
                "val": "順勢多 > -0.60 | 恐慌抄底 < -1.80 | 力竭摸頂 > +2.20",
                "pass": bool(today['z_score'] > -0.6)
            },
            {
                "name": "Yang-Zhang 極差波動率分位",
                "status": f"{today['vol_percentile']*100:.1f} %",
                "val": f"年化波動率: {today['yz_annual_vol']*100:.1f}% (恐慌臨界: > 75%)",
                "pass": bool(today['vol_percentile'] <= 0.75)
            },
            {
                "name": "Kaufman 效率比率 (KER)",
                "status": "趨勢能量充足" if today['kaufman_er'] >= self.er_filter_thresh else "隨機震盪雜訊",
                "val": f"當前 ER: {today['kaufman_er']:.3f} (門檻: > {self.er_filter_thresh})",
                "pass": bool(today['kaufman_er'] >= self.er_filter_thresh)
            }
        ]
        
        # Calculate pivot levels
        pivots = self.calculate_pivot_levels(df)
        
        # Completed trades & active trade
        completed_trades, active_trade = self.extract_trade_history(df)
        
        last_5_trades = []
        for t in completed_trades[-5:]:
            pos_label = "做多" if t['pos'] == 1 else "放空"
            pnl_val = t['pnl']
            last_5_trades.append({
                "entry_date": t['entry_date'],
                "entry_signal": t['entry_signal'],
                "entry_price": f"{t['entry_price']:,.0f}",
                "exit_date": t['exit_date'],
                "exit_signal": t['exit_signal'],
                "exit_price": f"{t['exit_price']:,.0f}",
                "pos_label": pos_label,
                "points": f"{t['points']:+,.0f}",
                "pnl": f"NT$ {pnl_val:+,.0f}",
                "is_win": pnl_val > 0,
                "exit_reason": t['exit_reason']
            })
            
        active_trade_info = None
        if active_trade is not None:
            pos_label = "做多" if active_trade['pos'] == 1 else "放空"
            pts = (today['close'] - active_trade['entry_price']) if active_trade['pos'] == 1 else (active_trade['entry_price'] - today['close'])
            pnl_val = pts * 200.0 - 200.0
            active_trade_info = {
                "entry_date": active_trade['entry_date'],
                "entry_signal": active_trade['entry_signal'],
                "entry_price": f"{active_trade['entry_price']:,.0f}",
                "pos_label": pos_label,
                "current_price": f"{today['close']:,.0f}",
                "unrealized_points": f"{pts:+,.0f}",
                "unrealized_pnl": f"NT$ {pnl_val:+,.0f}",
                "is_win": pnl_val > 0,
                "entry_reason": active_trade['entry_reason']
            }

        return {
            "date": today.name.strftime('%Y-%m-%d'),
            "close": today['close'],
            "open": today['open'],
            "high": today['high'],
            "low": today['low'],
            "volume": today['volume'],
            "pos": pos,
            "action_badge": action_badge,
            "action_title": action_title,
            "action_type": action_type,
            "action_desc": action_desc,
            "regime": regime,
            "regime_color": regime_color,
            "z_score": today['z_score'],
            "fd_fast": today['fd_fast'],
            "fd_slow": today['fd_slow'],
            "yz_vol": today['yz_annual_vol'],
            "vol_percentile": today['vol_percentile'],
            "macro_200ma": today['macro_200ma'],
            "kaufman_er": today['kaufman_er'],
            "checklist": checklist,
            "pivots": pivots,
            "last_5_trades": last_5_trades[::-1], # newest first
            "active_trade": active_trade_info
        }
