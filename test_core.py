"""
Quick test of core functionality
"""

import sys
import io
# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("Testing IDX Hybrid Sniper Core Modules...")
print("=" * 50)

# Test 1: Data Engine
print("\n1. Testing Data Engine...")
from src.data_engine import data_engine

tickers = data_engine.get_tickers()
print(f"   ✓ Loaded {len(tickers)} tickers from watchlist")

# Test 2: Fetch sample data
print("\n2. Testing Data Fetch (BBCA)...")
try:
    df = data_engine.get_ticker_data('BBCA')
    if df is not None and not df.empty:
        print(f"   ✓ Fetched {len(df)} bars of BBCA data")
        print(f"   ✓ Latest close: Rp {df['Close'].iloc[-1]:,.0f}")
    else:
        print("   ⚠ No data available (will fetch on first scan)")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# Test 3: Indicators
print("\n3. Testing Technical Indicators...")
from src.indicators import calculate_hma, calculate_supertrend, detect_fvg

if df is not None and not df.empty and len(df) > 100:
    try:
        hma = calculate_hma(df)
        print(f"   ✓ HMA calculated, latest: {hma.iloc[-1]:.2f}")

        st_data = calculate_supertrend(df)
        print(f"   ✓ SuperTrend calculated, direction: {'BULLISH' if st_data['supertrend_direction'].iloc[-1] == 1 else 'BEARISH'}")

        fvg_data = detect_fvg(df)
        bullish_fvg_count = fvg_data['fvg_bullish_top'].notna().sum()
        bearish_fvg_count = fvg_data['fvg_bearish_top'].notna().sum()
        print(f"   ✓ FVG detected: {bullish_fvg_count} bullish, {bearish_fvg_count} bearish")
    except Exception as e:
        print(f"   ⚠ Error: {e}")

# Test 4: Strategy
print("\n4. Testing Strategy Module...")
from src.strategy import strategy

try:
    ihsg_df = data_engine.get_ihsg_data()
    if ihsg_df is not None and not ihsg_df.empty:
        print(f"   ✓ IHSG data loaded: {len(ihsg_df)} bars")

    if df is not None and not df.empty:
        signal = strategy.analyze_ticker('BBCA', df, ihsg_df)
        print(f"   ✓ Signal generated: {signal.signal_type}")
        print(f"   ✓ Current price: Rp {signal.current_price:,.0f}")
        if signal.signal_type != 'NO_SIGNAL':
            print(f"   ✓ Entry: Rp {signal.entry_price:,.0f}, SL: Rp {signal.sl_price:,.0f}")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# Test 5: Journal
print("\n5. Testing Trading Journal...")
from src.journal_mgr import journal_mgr

try:
    stats = journal_mgr.get_statistics()
    print(f"   ✓ Journal stats loaded: {stats['total_trades']} total trades")

    lot_size = journal_mgr.calculate_lot_size(
        capital=100_000_000,  # 100 juta
        risk_pct=2.0,
        entry_price=9000,
        sl_price=8700
    )
    print(f"   ✓ Position calculator: {lot_size} lots for 100M capital")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# Test 6: Visualizer
print("\n6. Testing Chart Visualizer...")
from src.visualizer import create_candlestick_chart

try:
    if df is not None and not df.empty:
        fig = create_candlestick_chart(df, 'BBCA', ihsg_df, show_volume=True)
        print(f"   ✓ Chart created with {len(fig.data)} traces")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n" + "=" * 50)
print("✅ Core functionality test completed!")
print("\nNext steps:")
print("1. Run: streamlit run app.py")
print("2. Or use CLI: python main.py scan")
