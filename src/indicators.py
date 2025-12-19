"""
IDX Hybrid Sniper - Technical Indicators
HMA, SuperTrend, SMC FVG, Stochastic, Relative Strength
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    HMA_PERIOD, SUPERTREND_ATR_PERIOD, SUPERTREND_MULTIPLIER,
    STOCH_K_PERIOD, STOCH_D_PERIOD, STOCH_SMOOTH,
    VOLUME_MA_PERIOD, RS_LOOKBACK_PERIOD, FVG_MIN_ATR_RATIO
)


def calculate_hma(df: pd.DataFrame, period: int = HMA_PERIOD) -> pd.Series:
    """
    Calculate Hull Moving Average (HMA)

    HMA = WMA(2 * WMA(n/2) - WMA(n)), sqrt(n))
    where WMA = Weighted Moving Average

    Args:
        df: DataFrame with 'Close' column
        period: HMA period

    Returns:
        Series with HMA values
    """
    def wma(series, length):
        """Weighted Moving Average"""
        weights = np.arange(1, length + 1)
        return series.rolling(length).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    half_length = int(period / 2)
    sqrt_length = int(np.sqrt(period))

    wma_half = wma(df['Close'], half_length)
    wma_full = wma(df['Close'], period)

    raw_hma = 2 * wma_half - wma_full
    hma = wma(raw_hma, sqrt_length)

    return hma


def calculate_supertrend(df: pd.DataFrame,
                        atr_period: int = SUPERTREND_ATR_PERIOD,
                        multiplier: float = SUPERTREND_MULTIPLIER) -> pd.DataFrame:
    """
    Calculate SuperTrend indicator

    Args:
        df: DataFrame with OHLC data
        atr_period: ATR calculation period
        multiplier: ATR multiplier for bands

    Returns:
        DataFrame with columns: supertrend, supertrend_direction
        direction: 1 = bullish (green), -1 = bearish (red)
    """
    df = df.copy()

    # Calculate ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(atr_period).mean()

    # Calculate basic bands
    hl2 = (df['High'] + df['Low']) / 2
    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)

    # Calculate final bands
    final_upper = basic_upper.copy()
    final_lower = basic_lower.copy()

    for i in range(atr_period, len(df)):
        # Upper band
        if basic_upper.iloc[i] < final_upper.iloc[i-1] or df['Close'].iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = basic_upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]

        # Lower band
        if basic_lower.iloc[i] > final_lower.iloc[i-1] or df['Close'].iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = basic_lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]

    # Determine trend
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    for i in range(atr_period, len(df)):
        if i == atr_period:
            # Initialize
            if df['Close'].iloc[i] <= final_upper.iloc[i]:
                supertrend.iloc[i] = final_upper.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = final_lower.iloc[i]
                direction.iloc[i] = 1
        else:
            # Continue trend
            if direction.iloc[i-1] == 1:
                if df['Close'].iloc[i] <= final_lower.iloc[i]:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1
                else:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
            else:
                if df['Close'].iloc[i] >= final_upper.iloc[i]:
                    supertrend.iloc[i] = final_lower.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = final_upper.iloc[i]
                    direction.iloc[i] = -1

    result = pd.DataFrame({
        'supertrend': supertrend,
        'supertrend_direction': direction,
        'atr': atr
    }, index=df.index)

    return result


def calculate_stochastic(df: pd.DataFrame,
                         k_period: int = STOCH_K_PERIOD,
                         d_period: int = STOCH_D_PERIOD,
                         smooth: int = STOCH_SMOOTH) -> pd.DataFrame:
    """
    Calculate Stochastic Oscillator

    Args:
        df: DataFrame with OHLC data
        k_period: %K period
        d_period: %D period (smoothing)
        smooth: Smoothing period

    Returns:
        DataFrame with columns: stoch_k, stoch_d
    """
    df = df.copy()

    # Calculate %K
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()

    stoch_k = 100 * (df['Close'] - low_min) / (high_max - low_min)

    # Smooth %K
    stoch_k = stoch_k.rolling(window=smooth).mean()

    # Calculate %D (SMA of %K)
    stoch_d = stoch_k.rolling(window=d_period).mean()

    result = pd.DataFrame({
        'stoch_k': stoch_k,
        'stoch_d': stoch_d
    }, index=df.index)

    return result


def detect_fvg(df: pd.DataFrame, min_atr_ratio: float = FVG_MIN_ATR_RATIO) -> pd.DataFrame:
    """
    Detect Fair Value Gaps (FVG) - Smart Money Concepts

    Bullish FVG: candle[i].Low > candle[i-2].High
    Bearish FVG: candle[i].High < candle[i-2].Low

    Args:
        df: DataFrame with OHLC data and ATR
        min_atr_ratio: Minimum FVG size relative to ATR

    Returns:
        DataFrame with columns: fvg_bullish_top, fvg_bullish_bottom,
                                fvg_bearish_top, fvg_bearish_bottom
    """
    df = df.copy()

    # Initialize columns
    df['fvg_bullish_top'] = np.nan
    df['fvg_bullish_bottom'] = np.nan
    df['fvg_bearish_top'] = np.nan
    df['fvg_bearish_bottom'] = np.nan

    # Need ATR for filtering
    if 'atr' not in df.columns:
        st_data = calculate_supertrend(df)
        df['atr'] = st_data['atr']

    # Detect FVG (starting from index 2)
    for i in range(2, len(df)):
        atr_threshold = df['atr'].iloc[i] * min_atr_ratio

        # Bullish FVG: current low > previous 2 bar high
        if df['Low'].iloc[i] > df['High'].iloc[i-2]:
            gap_size = df['Low'].iloc[i] - df['High'].iloc[i-2]

            if gap_size >= atr_threshold:
                df.loc[df.index[i], 'fvg_bullish_top'] = df['Low'].iloc[i]
                df.loc[df.index[i], 'fvg_bullish_bottom'] = df['High'].iloc[i-2]

        # Bearish FVG: current high < previous 2 bar low
        if df['High'].iloc[i] < df['Low'].iloc[i-2]:
            gap_size = df['Low'].iloc[i-2] - df['High'].iloc[i]

            if gap_size >= atr_threshold:
                df.loc[df.index[i], 'fvg_bearish_top'] = df['Low'].iloc[i-2]
                df.loc[df.index[i], 'fvg_bearish_bottom'] = df['High'].iloc[i]

    return df[['fvg_bullish_top', 'fvg_bullish_bottom',
               'fvg_bearish_top', 'fvg_bearish_bottom']]


def get_active_fvg(df: pd.DataFrame, current_price: float) -> dict:
    """
    Get currently active (unfilled) FVG zones

    Args:
        df: DataFrame with FVG columns
        current_price: Current market price

    Returns:
        Dictionary with active bullish and bearish FVG zones
    """
    bullish_fvg = None
    bearish_fvg = None

    # Find most recent unfilled bullish FVG
    for i in range(len(df) - 1, -1, -1):
        if pd.notna(df['fvg_bullish_top'].iloc[i]):
            top = df['fvg_bullish_top'].iloc[i]
            bottom = df['fvg_bullish_bottom'].iloc[i]

            # Check if price is above FVG (not filled yet)
            if current_price > top:
                bullish_fvg = {
                    'top': top,
                    'bottom': bottom,
                    'mid': (top + bottom) / 2,
                    'date': df.index[i]
                }
                break

    # Find most recent unfilled bearish FVG
    for i in range(len(df) - 1, -1, -1):
        if pd.notna(df['fvg_bearish_top'].iloc[i]):
            top = df['fvg_bearish_top'].iloc[i]
            bottom = df['fvg_bearish_bottom'].iloc[i]

            # Check if price is below FVG (not filled yet)
            if current_price < bottom:
                bearish_fvg = {
                    'top': top,
                    'bottom': bottom,
                    'mid': (top + bottom) / 2,
                    'date': df.index[i]
                }
                break

    return {
        'bullish': bullish_fvg,
        'bearish': bearish_fvg
    }


def calculate_relative_strength(stock_df: pd.DataFrame,
                                 index_df: pd.DataFrame,
                                 lookback: int = RS_LOOKBACK_PERIOD) -> float:
    """
    Calculate Relative Strength vs IHSG

    RS Score = (Stock % Change - IHSG % Change) over lookback period

    Args:
        stock_df: Stock OHLCV DataFrame
        index_df: IHSG OHLCV DataFrame
        lookback: Period for calculation

    Returns:
        RS Score (positive = outperforming, negative = underperforming)
    """
    if len(stock_df) < lookback or len(index_df) < lookback:
        return 0.0

    # Get percentage change over lookback period
    stock_change = ((stock_df['Close'].iloc[-1] / stock_df['Close'].iloc[-lookback]) - 1) * 100
    index_change = ((index_df['Close'].iloc[-1] / index_df['Close'].iloc[-lookback]) - 1) * 100

    rs_score = stock_change - index_change

    return rs_score


def calculate_volume_metrics(df: pd.DataFrame,
                             ma_period: int = VOLUME_MA_PERIOD) -> pd.DataFrame:
    """
    Calculate volume-related metrics

    Args:
        df: DataFrame with Volume column
        ma_period: Moving average period for volume

    Returns:
        DataFrame with volume_ma and volume_ratio
    """
    df = df.copy()

    # Volume moving average
    df['volume_ma'] = df['Volume'].rolling(window=ma_period).mean()

    # Current volume relative to average
    df['volume_ratio'] = df['Volume'] / df['volume_ma']

    return df[['volume_ma', 'volume_ratio']]


def add_all_indicators(df: pd.DataFrame,
                       ihsg_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Add all technical indicators to a DataFrame

    Args:
        df: Stock OHLCV DataFrame
        ihsg_df: Optional IHSG DataFrame for RS calculation

    Returns:
        DataFrame with all indicators added
    """
    df = df.copy()

    # Trend indicators
    df['hma'] = calculate_hma(df)
    st_data = calculate_supertrend(df)
    df['supertrend'] = st_data['supertrend']
    df['supertrend_direction'] = st_data['supertrend_direction']
    df['atr'] = st_data['atr']

    # Momentum
    stoch_data = calculate_stochastic(df)
    df['stoch_k'] = stoch_data['stoch_k']
    df['stoch_d'] = stoch_data['stoch_d']

    # Volume
    vol_data = calculate_volume_metrics(df)
    df['volume_ma'] = vol_data['volume_ma']
    df['volume_ratio'] = vol_data['volume_ratio']

    # Fair Value Gaps
    fvg_data = detect_fvg(df)
    df['fvg_bullish_top'] = fvg_data['fvg_bullish_top']
    df['fvg_bullish_bottom'] = fvg_data['fvg_bullish_bottom']
    df['fvg_bearish_top'] = fvg_data['fvg_bearish_top']
    df['fvg_bearish_bottom'] = fvg_data['fvg_bearish_bottom']

    # Relative Strength (if IHSG data provided)
    if ihsg_df is not None and not ihsg_df.empty:
        df['rs_score'] = calculate_relative_strength(df, ihsg_df)
    else:
        df['rs_score'] = 0.0

    return df


# ===================================================================
# NEW: ADVANCED SMC FILTERS
# ===================================================================

def calculate_discount_zone(df: pd.DataFrame, lookback: int = 50):
    """
    Calculate swing-based premium vs discount zones

    Premium zone: >50% of swing range (EXPENSIVE - avoid!)
    Discount zone: <50% of swing range (CHEAP - buy!)

    Args:
        df: DataFrame with OHLC data
        lookback: Period untuk swing calculation

    Returns:
        Dictionary with zone levels
    """
    recent = df.tail(lookback)

    swing_high = recent['High'].max()
    swing_low = recent['Low'].min()
    swing_range = swing_high - swing_low

    # Equilibrium = 50% level
    equilibrium = swing_low + (swing_range * 0.5)

    # Premium zone starts at 50%
    premium_start = equilibrium

    # Discount zone ends at 50%
    discount_end = equilibrium

    # Sweet spot: 20-40% of swing (ideal buy zone)
    sweet_spot_low = swing_low + (swing_range * 0.2)
    sweet_spot_high = swing_low + (swing_range * 0.4)

    return {
        'swing_high': swing_high,
        'swing_low': swing_low,
        'equilibrium': equilibrium,
        'premium_start': premium_start,
        'discount_end': discount_end,
        'sweet_spot_low': sweet_spot_low,
        'sweet_spot_high': sweet_spot_high,
        'swing_range': swing_range
    }


def is_fvg_in_discount(fvg: dict, zones: dict):
    """
    Check if FVG is in discount zone (< 50% of swing)

    Args:
        fvg: FVG dictionary with 'top' and 'bottom'
        zones: Zones from calculate_discount_zone()

    Returns:
        Tuple (is_discount: bool, zone_type: str)
    """
    fvg_mid = (fvg['top'] + fvg['bottom']) / 2

    # Calculate FVG position in swing range (0 = low, 1 = high)
    fvg_position = (fvg_mid - zones['swing_low']) / zones['swing_range']

    # Sweet spot: 20-40% (ideal!)
    if zones['sweet_spot_low'] <= fvg_mid <= zones['sweet_spot_high']:
        return True, "SWEET_SPOT", fvg_position

    # Discount zone: < 50%
    elif fvg_mid < zones['equilibrium']:
        return True, "DISCOUNT", fvg_position

    # Premium zone: > 50% (AVOID!)
    else:
        return False, "PREMIUM", fvg_position


def detect_volume_anomaly(df: pd.DataFrame, threshold: float = 3.0):
    """
    Detect volume spike during pullback

    Volume spike > 3x average = DANGER (panic selling/distribution)

    Args:
        df: DataFrame with Volume data
        threshold: Multiplier for anomaly (default 3x)

    Returns:
        Tuple (is_anomaly: bool, anomaly_type: str, ratio: float)
    """
    latest = df.iloc[-1]
    volume_ma = df['Volume'].rolling(20).mean().iloc[-1]

    if pd.isna(volume_ma) or volume_ma == 0:
        return False, "INSUFFICIENT_DATA", 0.0

    volume_ratio = latest['Volume'] / volume_ma

    # Check if volume spike
    if volume_ratio > threshold:
        # Red candle with spike = PANIC SELLING
        if latest['Close'] < latest['Open']:
            return True, "PANIC_SELLING", volume_ratio
        # Green candle with spike = ACCUMULATION (OK!)
        else:
            return False, "ACCUMULATION", volume_ratio

    # Normal volume
    return False, "NORMAL", volume_ratio


def check_distribution_pattern(df: pd.DataFrame):
    """
    Detect distribution pattern (high volume selling)

    Pattern: 2+ red candles with volume > 1.5x average in last 5 bars

    Args:
        df: DataFrame with OHLC and Volume

    Returns:
        Tuple (is_distribution: bool, message: str)
    """
    recent = df.tail(5)

    # Find red candles (down days)
    red_candles = recent[recent['Close'] < recent['Open']]

    if len(red_candles) >= 2:
        avg_red_volume = red_candles['Volume'].mean()
        avg_total_volume = recent['Volume'].mean()

        # Red candles have 1.5x higher volume = Distribution
        if avg_red_volume > (avg_total_volume * 1.5):
            return True, f"Distribution: {len(red_candles)} red bars with high volume"

    return False, "No distribution pattern"


def check_rejection_candle(df: pd.DataFrame, fvg_zone: dict):
    """
    Check if latest candle shows rejection/bounce from FVG

    Criteria for valid rejection:
    1. Price touched FVG zone (low <= FVG top)
    2. Candle is GREEN (buyers stepped in)
    3. Lower wick >= 40% of total range (rejection)
    4. Volume increased (buyers active)
    5. Close in upper 60% of range (strong bounce)

    Args:
        df: DataFrame with OHLC and Volume
        fvg_zone: FVG dictionary with 'top' and 'bottom'

    Returns:
        Tuple (is_rejection: bool, quality: str, details: dict)
    """
    if len(df) < 2:
        return False, "INSUFFICIENT_DATA", {}

    latest = df.iloc[-1]
    prev_volume = df['Volume'].rolling(5).mean().iloc[-1]

    details = {}

    # 1. Price must touch FVG zone
    if latest['Low'] > fvg_zone['top']:
        return False, "NO_TOUCH", {'reason': 'Price did not touch FVG'}

    # 2. Candle must be GREEN (buyers present)
    is_green = latest['Close'] > latest['Open']
    if not is_green:
        return False, "RED_CANDLE", {'reason': 'Candle is red (no buyers)'}

    # 3. Calculate candle metrics
    total_range = latest['High'] - latest['Low']
    if total_range == 0:
        return False, "DOJI", {'reason': 'No range (doji)'}

    body = abs(latest['Close'] - latest['Open'])
    lower_wick = latest['Open'] - latest['Low']
    upper_wick = latest['High'] - latest['Close']

    wick_ratio = lower_wick / total_range
    close_position = (latest['Close'] - latest['Low']) / total_range

    details = {
        'total_range': total_range,
        'lower_wick_ratio': wick_ratio,
        'close_position': close_position,
        'volume_ratio': latest['Volume'] / prev_volume if prev_volume > 0 else 0
    }

    # 4. Lower wick must be >= 40% (shows rejection)
    if wick_ratio < 0.4:
        return False, "WEAK_REJECTION", {**details, 'reason': f'Wick only {wick_ratio*100:.1f}% (need 40%)'}

    # 5. Volume must increase (buyers stepping in)
    if latest['Volume'] <= prev_volume:
        return False, "LOW_VOLUME", {**details, 'reason': 'Volume not increasing'}

    # 6. Close in upper 60% of range (strong buyers)
    if close_position < 0.6:
        return False, "WEAK_CLOSE", {**details, 'reason': f'Close at {close_position*100:.1f}% (need >60%)'}

    # All criteria met!
    quality = "STRONG" if (wick_ratio > 0.5 and close_position > 0.75) else "GOOD"

    return True, quality, {**details, 'reason': 'Valid rejection candle'}


def find_nearest_resistance(df: pd.DataFrame, entry_price: float, lookback: int = 50):
    """
    Find nearest swing high resistance above entry price

    Swing high = local peak (higher than 2 bars before and after)

    Args:
        df: DataFrame with OHLC data
        entry_price: Proposed entry price
        lookback: Period to search for swing highs

    Returns:
        Float (nearest resistance price) or None
    """
    if len(df) < lookback:
        return None

    recent = df.tail(lookback)
    swing_highs = []

    # Find swing highs (local peaks)
    for i in range(2, len(recent) - 2):
        if (recent['High'].iloc[i] > recent['High'].iloc[i-1] and
            recent['High'].iloc[i] > recent['High'].iloc[i-2] and
            recent['High'].iloc[i] > recent['High'].iloc[i+1] and
            recent['High'].iloc[i] > recent['High'].iloc[i+2]):

            swing_highs.append(recent['High'].iloc[i])

    # Filter resistances above entry
    resistances = [r for r in swing_highs if r > entry_price]

    if resistances:
        return min(resistances)  # Nearest resistance
    else:
        return None


# ============================================
# PHASE 2: MULTI-TIMEFRAME ANALYSIS
# ============================================

def resample_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily data to weekly timeframe

    Args:
        df: Daily OHLCV DataFrame with DatetimeIndex

    Returns:
        Weekly OHLCV DataFrame
    """
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    # Resample to weekly (W-FRI = week ending Friday)
    weekly = df.resample('W-FRI').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # Drop rows with NaN (incomplete weeks)
    weekly = weekly.dropna()

    return weekly


def get_weekly_trend(df: pd.DataFrame, atr_period: int = 10, atr_multiplier: float = 3.0) -> dict:
    """
    Analyze weekly timeframe trend using SuperTrend

    Args:
        df: Daily OHLCV DataFrame
        atr_period: ATR period for SuperTrend calculation
        atr_multiplier: ATR multiplier for SuperTrend

    Returns:
        Dictionary with weekly trend info:
        - is_bullish: bool (weekly trend is bullish)
        - weekly_supertrend: float (weekly SuperTrend level)
        - weekly_close: float (latest weekly close)
        - bars_in_trend: int (how many weeks in current trend)
    """
    # Convert to weekly
    weekly_df = resample_to_weekly(df)

    if len(weekly_df) < 20:
        return {
            'is_bullish': False,
            'weekly_supertrend': None,
            'weekly_close': None,
            'bars_in_trend': 0,
            'error': 'Insufficient weekly data'
        }

    # Calculate ATR on weekly
    weekly_df['tr'] = np.maximum(
        weekly_df['High'] - weekly_df['Low'],
        np.maximum(
            abs(weekly_df['High'] - weekly_df['Close'].shift(1)),
            abs(weekly_df['Low'] - weekly_df['Close'].shift(1))
        )
    )
    weekly_df['atr'] = weekly_df['tr'].rolling(window=atr_period).mean()

    # Calculate SuperTrend on weekly
    weekly_df['hl_avg'] = (weekly_df['High'] + weekly_df['Low']) / 2
    weekly_df['upper_band'] = weekly_df['hl_avg'] + (atr_multiplier * weekly_df['atr'])
    weekly_df['lower_band'] = weekly_df['hl_avg'] - (atr_multiplier * weekly_df['atr'])

    # Initialize SuperTrend
    weekly_df['supertrend'] = 0.0
    weekly_df['supertrend_direction'] = 1  # 1 = bullish, -1 = bearish

    for i in range(atr_period, len(weekly_df)):
        # Current values
        close = weekly_df['Close'].iloc[i]
        upper = weekly_df['upper_band'].iloc[i]
        lower = weekly_df['lower_band'].iloc[i]
        prev_st = weekly_df['supertrend'].iloc[i-1]
        prev_dir = weekly_df['supertrend_direction'].iloc[i-1]

        # Calculate SuperTrend
        if prev_dir == 1:  # Was bullish
            if close <= prev_st:
                # Trend reversal to bearish
                weekly_df.loc[weekly_df.index[i], 'supertrend'] = upper
                weekly_df.loc[weekly_df.index[i], 'supertrend_direction'] = -1
            else:
                # Stay bullish
                weekly_df.loc[weekly_df.index[i], 'supertrend'] = max(lower, prev_st)
                weekly_df.loc[weekly_df.index[i], 'supertrend_direction'] = 1
        else:  # Was bearish
            if close >= prev_st:
                # Trend reversal to bullish
                weekly_df.loc[weekly_df.index[i], 'supertrend'] = lower
                weekly_df.loc[weekly_df.index[i], 'supertrend_direction'] = 1
            else:
                # Stay bearish
                weekly_df.loc[weekly_df.index[i], 'supertrend'] = min(upper, prev_st)
                weekly_df.loc[weekly_df.index[i], 'supertrend_direction'] = -1

    # Get latest weekly bar
    latest_weekly = weekly_df.iloc[-1]
    is_bullish = latest_weekly['supertrend_direction'] == 1

    # Count bars in current trend
    bars_in_trend = 1
    for i in range(len(weekly_df)-2, -1, -1):
        if weekly_df['supertrend_direction'].iloc[i] == latest_weekly['supertrend_direction']:
            bars_in_trend += 1
        else:
            break

    return {
        'is_bullish': is_bullish,
        'weekly_supertrend': round(latest_weekly['supertrend'], 2),
        'weekly_close': round(latest_weekly['Close'], 2),
        'bars_in_trend': bars_in_trend,
        'weekly_df': weekly_df  # Return full weekly DataFrame for debugging
    }


def check_weekly_daily_alignment(df: pd.DataFrame, debug: bool = False) -> tuple:
    """
    Check if daily and weekly trends are aligned (both bullish)

    Args:
        df: Daily DataFrame with indicators already calculated
        debug: Print debug information

    Returns:
        (is_aligned: bool, weekly_info: dict, message: str)
    """
    # Get weekly trend
    weekly_info = get_weekly_trend(df)

    if 'error' in weekly_info:
        return False, weekly_info, weekly_info['error']

    # Get daily trend (from existing indicators)
    if 'supertrend_direction' not in df.columns:
        return False, weekly_info, "Daily indicators not calculated"

    latest_daily = df.iloc[-1]
    daily_is_bullish = latest_daily['supertrend_direction'] == 1

    # Check alignment
    is_aligned = daily_is_bullish and weekly_info['is_bullish']

    if debug:
        print(f"  📅 Weekly Trend: {'BULLISH' if weekly_info['is_bullish'] else 'BEARISH'} ({weekly_info['bars_in_trend']} weeks)")
        print(f"  📊 Daily Trend: {'BULLISH' if daily_is_bullish else 'BEARISH'}")
        print(f"  🎯 Alignment: {'✅ ALIGNED' if is_aligned else '❌ NOT ALIGNED'}")

    # Create message
    if is_aligned:
        message = f"Weekly + Daily aligned (W:{weekly_info['bars_in_trend']} weeks bullish)"
    elif weekly_info['is_bullish'] and not daily_is_bullish:
        message = f"Weekly bullish but daily bearish (counter-trend)"
    elif not weekly_info['is_bullish'] and daily_is_bullish:
        message = f"Daily bullish but weekly bearish (weak trend)"
    else:
        message = f"Both weekly and daily bearish"

    return is_aligned, weekly_info, message
