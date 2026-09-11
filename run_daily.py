# -*- coding: utf-8 -*-
"""
Main Entry Point: Daily pipeline
1. Fetch latest data
2. Compute features
3. Run decision engine
4. Generate docs/index.html
"""
import os
import sys

# Ensure src is in python path
SRC_DIR = os.path.join(os.path.dirname(__file__), 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from data_fetcher import fetch_and_update_data
from feature_engine import FeatureAdaptiveEngine
from decision_engine import DecisionEngine
from dashboard_builder import build_dashboard_html

def main():
    print("=" * 60)
    print("Feature Adaptive Daily Monitor Pipeline Starting...")
    print("=" * 60)
    
    # 1. Ingest Data
    df = fetch_and_update_data('^TWII')
    
    # 2. Compute Features
    print("[Pipeline] Computing stationary & adaptive features...")
    engine = FeatureAdaptiveEngine()
    features_df = engine.compute_features(df)
    
    # 3. Decision Diagnosis
    print("[Pipeline] Running mutex state machine decision engine...")
    decider = DecisionEngine()
    diag = decider.generate_daily_diagnosis(features_df)
    
    print("-" * 60)
    print(f"Date: {diag['date']} | Close: {diag['close']:,.2f}")
    print(f"Action: {diag['action_title']} ({diag['action_type']})")
    print(f"Regime: {diag['regime']}")
    print(f"Reason: {diag['action_desc']}")
    print(f"Z-Score: {diag['z_score']:+.2f} | YZ Vol Rank: {diag['vol_percentile']*100:.1f}% | 200MA: {diag['macro_200ma']:,.0f}")
    print("-" * 60)
    
    # 4. Build Dashboard HTML for GitHub Pages
    docs_html = os.path.join(os.path.dirname(__file__), 'docs', 'index.html')
    build_dashboard_html(features_df, diag, docs_html)
    
    print("=" * 60)
    print("Pipeline Execution Completed Successfully.")
    print("=" * 60)

if __name__ == '__main__':
    main()
