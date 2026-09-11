# -*- coding: utf-8 -*-
"""
Feature Engine: 1:1 Math match with MultiCharts PowerLanguage implementation
- Fractional Differentiation (d*=0.30, window=50)
- Dual Moving Averages on FracDiff (SMA 15, SMA 70)
- Z-Score normalization (60-bar lookback)
- Yang-Zhang Drift-Independent Volatility (20-bar)
- Volatility Percentile Rank (252-bar rolling)
- Macro 200 SMA
- Kaufman Efficiency Ratio (KER 20)
"""
import numpy as np
import pandas as pd
import math

class FeatureAdaptiveEngine:
    def __init__(self, d_order=0.30, fd_window=50, ma_fast=15, ma_slow=70, z_len=60,
                 yz_window=20, vol_rank_len=252, macro_len=200, ker_len=20):
        self.d_order = d_order
        self.fd_window = fd_window
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.z_len = z_len
        self.yz_window = yz_window
        self.vol_rank_len = vol_rank_len
        self.macro_len = macro_len
        self.ker_len = ker_len
        
        # Pre-compute binomial expansion weights
        self.weights = np.zeros(self.fd_window)
        self.weights[0] = 1.0
        for k in range(1, self.fd_window):
            self.weights[k] = -self.weights[k-1] * (self.d_order - k + 1.0) / float(k)
            
        # Yang-Zhang optimal k factor
        self.k_factor = 0.34 / (1.34 + (self.yz_window + 1.0) / (self.yz_window - 1.0))

    def compute_features(self, df):
        """
        Compute all stationary and adaptive features for given OHLCV DataFrame.
        """
        df = df.copy()
        n = len(df)
        close_vals = df['close'].values
        open_vals = df['open'].values
        high_vals = df['high'].values
        low_vals = df['low'].values
        
        # 1. Fractional Differentiation on Log(Close)
        log_close = np.log(np.maximum(close_vals, 1e-8))
        frac_diff = np.zeros(n)
        for i in range(self.fd_window - 1, n):
            window_closes = log_close[i - self.fd_window + 1 : i + 1][::-1]
            frac_diff[i] = np.dot(self.weights, window_closes)
            
        df['frac_diff'] = frac_diff
        df['fd_fast'] = df['frac_diff'].rolling(self.ma_fast).mean()
        df['fd_slow'] = df['frac_diff'].rolling(self.ma_slow).mean()
        df['fd_std'] = df['frac_diff'].rolling(self.z_len).std(ddof=1)
        
        # Z-Score
        df['z_score'] = (df['frac_diff'] - df['fd_slow']) / (df['fd_std'].replace(0, np.nan))
        df['z_score'] = df['z_score'].fillna(0.0)
        
        # 2. Yang-Zhang Volatility
        log_ho = np.log(high_vals / open_vals)
        log_lo = np.log(low_vals / open_vals)
        log_co = np.log(close_vals / open_vals)
        
        prev_close = np.roll(close_vals, 1)
        prev_close[0] = close_vals[0]
        log_oc = np.log(open_vals / prev_close)
        log_cc = np.log(close_vals / prev_close)
        
        rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
        rs_series = pd.Series(rs, index=df.index).rolling(self.yz_window).mean()
        var_open = pd.Series(log_oc, index=df.index).rolling(self.yz_window).var(ddof=1)
        var_close = pd.Series(log_cc, index=df.index).rolling(self.yz_window).var(ddof=1)
        
        yz_var = var_open + self.k_factor * var_close + (1.0 - self.k_factor) * rs_series
        df['yz_annual_vol'] = np.sqrt(np.maximum(yz_var, 0) * 252.0).fillna(0.15)
        
        # Volatility Percentile Rank over rolling window
        df['vol_percentile'] = df['yz_annual_vol'].rolling(self.vol_rank_len).apply(
            lambda x: (x[-1] >= x).sum() / float(len(x)), raw=True
        ).fillna(0.50)
        
        # 3. Macro 200 SMA
        df['macro_200ma'] = df['close'].rolling(self.macro_len).mean()
        df['macro_bull'] = df['close'] > df['macro_200ma']
        
        # 4. Kaufman Efficiency Ratio (KER)
        net_change = (df['close'] - df['close'].shift(self.ker_len)).abs()
        gross_path = (df['close'] - df['close'].shift(1)).abs().rolling(self.ker_len).sum()
        df['kaufman_er'] = (net_change / (gross_path + 1e-8)).fillna(0.0)
        
        return df

if __name__ == '__main__':
    from data_fetcher import fetch_and_update_data
    df = fetch_and_update_data()
    engine = FeatureAdaptiveEngine()
    features_df = engine.compute_features(df)
    print("Latest feature values:")
    latest = features_df.iloc[-1]
    print(f"Date: {latest.name.strftime('%Y-%m-%d')}")
    print(f"Close: {latest['close']:,.2f}")
    print(f"200MA: {latest['macro_200ma']:,.2f} (Macro Bull: {latest['macro_bull']})")
    print(f"FracDiff Z-Score: {latest['z_score']:+.2f}")
    print(f"FracDiff Fast vs Slow: {latest['fd_fast']:.4f} vs {latest['fd_slow']:.4f}")
    print(f"YZ Volatility: {latest['yz_annual_vol']*100:.1f}% (Rank: {latest['vol_percentile']*100:.1f}%)")
    print(f"Kaufman ER: {latest['kaufman_er']:.3f}")
