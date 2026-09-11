# -*- coding: utf-8 -*-
"""
Decision Engine: Implements the exact MultiCharts Mutex State-Machine Cascade
Generates comprehensive market diagnosis, signal states, and human-readable reasoning.
"""
import pandas as pd
import numpy as np

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
        Replay state machine through the dataset to determine historical trades
        and the current active state & today's fresh decision.
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
            er = row['kaufman_er']
            
            next_pos = pos
            sig = ""
            rsn = ""
            
            # 1. Cascade logic: Panic Long (Highest Priority)
            if z < self.z_panic_thresh and vp > self.vol_panic_thresh:
                next_pos = 1
                sig = "Panic_LE"
                rsn = f"觸發恐慌極端抄底 (Z-Score: {z:.2f} < {self.z_panic_thresh}, 波動率分位: {vp*100:.1f}% > {self.vol_panic_thresh*100:.0f}%)"
            # 2. Trend Long
            elif mb and (fast > slow) and (z > self.z_trend_thresh):
                next_pos = 1
                sig = "Trend_LE"
                rsn = f"站上年線且動量金叉順勢做多 (Close > 200MA, Fast > Slow, Z-Score: {z:.2f} > {self.z_trend_thresh})"
            # 3. Bear Breakdown Short
            elif (not mb) and (fast < slow) and (z > self.z_short_min) and (z < self.z_short_max):
                next_pos = -1
                sig = "Breakdown_SE"
                rsn = f"跌破年線且動量死叉破位做空 (Close <= 200MA, Fast < Slow, Z-Score: {z:.2f} 於 [{self.z_short_min}, {self.z_short_max}])"
            # 4. Exhaustion Short
            elif z > self.z_overbought_thresh and vp < self.vol_exhaust_thresh:
                next_pos = -1
                sig = "Exhaustion_SE"
                rsn = f"極度超買但流動性枯竭摸頂做空 (Z-Score: {z:.2f} > {self.z_overbought_thresh}, 波動率分位: {vp*100:.1f}% < {self.vol_exhaust_thresh*100:.0f}%)"
            # 5. Long Exit
            elif pos == 1 and ((fast < slow) or (not mb and z < 0.0)):
                next_pos = 0
                sig = "Exit_LX"
                if fast < slow:
                    rsn = f"多單平倉出場：分數階快線跌破慢線死叉 (Fast: {fast:.4f} < Slow: {slow:.4f})"
                else:
                    rsn = f"多單平倉出場：跌破年線且動量轉負 (Close <= 200MA 且 Z-Score: {z:.2f} < 0)"
            # 6. Short Exit
            elif pos == -1 and ((z < self.z_panic_thresh) or (fast > slow) or (mb and z > 0.2)):
                next_pos = 0
                sig = "Exit_SX"
                if z < self.z_panic_thresh:
                    rsn = f"空單回補出場：殺入極端超跌恐慌區 (Z-Score: {z:.2f} < {self.z_panic_thresh})"
                elif fast > slow:
                    rsn = f"空單回補出場：分數階快線金叉慢線 (Fast: {fast:.4f} > Slow: {slow:.4f})"
                else:
                    rsn = f"空單回補出場：站回年線且動量轉正 (Close > 200MA 且 Z-Score: {z:.2f} > 0.2)"
                    
            states[i] = next_pos
            signals[i] = sig
            reasons[i] = rsn
            pos = next_pos
            
        df['state_pos'] = states
        df['signal'] = signals
        df['reason'] = reasons
        
        return df

    def generate_daily_diagnosis(self, df):
        """
        Generate comprehensive diagnosis report for today's market close.
        """
        df = self.evaluate_state_machine(df)
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        pos = today['state_pos']
        prev_pos = yesterday['state_pos']
        fresh_signal = today['signal']
        
        # Position Action Determination
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
                regime_color = "#10B981"
            elif today['z_score'] > -0.6:
                regime = "穩健多頭波段震盪 (Healthy Bullish Swing)"
                regime_color = "#059669"
            else:
                regime = "多頭回檔深洗整理 (Bullish Pullback)"
                regime_color = "#F59E0B"
        else:
            if today['z_score'] < -1.8 and today['vol_percentile'] > 0.75:
                regime = "恐慌崩跌超跌極限區 (Extreme Panic Selling Exhaustion)"
                regime_color = "#EC4899"
            elif today['z_score'] < -0.5:
                regime = "空頭波段主跌結構 (Bearish Markdown Structure)"
                regime_color = "#EF4444"
            else:
                regime = "空頭弱勢反彈整理 (Weak Bearish Rebound)"
                regime_color = "#DC2626"

        # Diagnostic Details
        gap_200ma_pts = today['close'] - today['macro_200ma']
        gap_200ma_pct = (gap_200ma_pts / today['macro_200ma']) * 100.0
        
        # Checklists
        checklist = [
            {
                "name": "宏觀 200MA 牛熊分界",
                "status": "多頭格局 (Bullish)" if today['macro_bull'] else "空頭格局 (Bearish)",
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
                "val": "做多門檻 > -0.60 | 恐慌抄底 < -1.80 | 力竭做空 > +2.20",
                "pass": bool(today['z_score'] > -0.6)
            },
            {
                "name": "Yang-Zhang 極差波動率分位",
                "status": f"{today['vol_percentile']*100:.1f} %",
                "val": f"年化波動率: {today['yz_annual_vol']*100:.1f}% (恐慌臨界點: > 75%)",
                "pass": bool(today['vol_percentile'] <= 0.75)
            },
            {
                "name": "Kaufman 效率比率 (KER)",
                "status": "趨勢能量有效" if today['kaufman_er'] >= self.er_filter_thresh else "隨機震盪雜訊",
                "val": f"當前 ER: {today['kaufman_er']:.3f} (門檻: > {self.er_filter_thresh})",
                "pass": bool(today['kaufman_er'] >= self.er_filter_thresh)
            }
        ]
        
        # Recent trades log
        recent_trades = []
        sig_indices = df[df['signal'] != ""].index
        for idx in sig_indices[-8:]:
            r = df.loc[idx]
            recent_trades.append({
                "date": idx.strftime('%Y-%m-%d'),
                "signal": r['signal'],
                "close": f"{r['close']:,.0f}",
                "z_score": f"{r['z_score']:+.2f}",
                "reason": r['reason']
            })

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
            "recent_trades": recent_trades[::-1]
        }
