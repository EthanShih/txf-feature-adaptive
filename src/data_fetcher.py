# -*- coding: utf-8 -*-
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'twii_daily.csv')

def fetch_and_update_data(symbol='^TWII'):
    """
    Fetch latest daily OHLCV from Yahoo Finance (^TWII) and update local CSV.
    """
    print(f"[DataFetcher] Checking {symbol} daily data...")
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    existing_df = None
    if os.path.exists(DATA_FILE):
        try:
            existing_df = pd.read_csv(DATA_FILE, index_col=0, parse_dates=True)
            print(f"[DataFetcher] Loaded existing {len(existing_df)} bars (up to {existing_df.index[-1].strftime('%Y-%m-%d')}).")
        except Exception as e:
            print(f"[DataFetcher] Warning reading existing CSV: {e}")

    try:
        ticker = yf.Ticker(symbol)
        period = '5y' if existing_df is None or len(existing_df) < 200 else '1mo'
        df_new = ticker.history(period=period)
        
        if df_new.empty and existing_df is None:
            print("[DataFetcher] Warning: yfinance returned empty data, trying period='2y'")
            df_new = ticker.history(period='2y')
            
        if not df_new.empty:
            df_new = df_new[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df_new.index = pd.to_datetime(df_new.index).tz_localize(None).normalize()
            df_new.columns = [c.lower() for c in df_new.columns]
            df_new.dropna(inplace=True)
            
            if existing_df is not None:
                combined = pd.concat([existing_df, df_new])
                combined = combined[~combined.index.duplicated(keep='last')].sort_index()
            else:
                combined = df_new.sort_index()
                
            combined.to_csv(DATA_FILE)
            print(f"[DataFetcher] Successfully updated dataset: {len(combined)} total bars, latest: {combined.index[-1].strftime('%Y-%m-%d')}")
            return combined
    except Exception as e:
        print(f"[DataFetcher] Notice during yfinance fetch: {e}")
        
    if existing_df is not None and len(existing_df) > 0:
        print("[DataFetcher] Using cached dataset.")
        return existing_df
        
    # Fallback to local research file if available
    research_files = [
        r'c:\AntiGravity\research\^TWII_1d_5y.csv',
        r'c:\AntiGravity\research\txf1_1D.parquet'
    ]
    for rf in research_files:
        if os.path.exists(rf):
            print(f"[DataFetcher] Initializing from local fallback: {rf}")
            if rf.endswith('.parquet'):
                df_fb = pd.read_parquet(rf)
            else:
                df_fb = pd.read_csv(rf, index_col=0, parse_dates=True)
            df_fb.columns = [c.lower() for c in df_fb.columns]
            df_fb.to_csv(DATA_FILE)
            return df_fb
            
    raise RuntimeError("No data could be retrieved or initialized.")

if __name__ == '__main__':
    df = fetch_and_update_data()
    print("Latest 5 bars:")
    print(df.tail())
