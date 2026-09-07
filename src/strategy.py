"""
IDX Hybrid Sniper - Trading Strategy
Signal generation with SMC and Momentum entries
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    MIN_LIQUIDITY_IDR, STOCH_OVERSOLD,
    VOLUME_LOW_THRESHOLD, VOLUME_HIGH_THRESHOLD,
    RS_STRONG, RS_WEAK,
    SL_ATR_MULTIPLIER, TP1_ATR_MULTIPLIER
)
from src.indicators import (
    add_all_indicators, get_active_fvg,
    calculate_discount_zone, is_fvg_in_discount,
    detect_volume_anomaly, check_distribution_pattern,
    check_rejection_candle, find_nearest_resistance,
    check_weekly_daily_alignment  # Phase 2
)


class Signal:
    """Trading signal data class"""

    def __init__(self, ticker: str, signal_type: str, **kwargs):
        self.ticker = ticker
        self.signal_type = signal_type  # 'SMC_ENTRY', 'MOMENTUM_ENTRY', 'NO_SIGNAL'

        # Price levels
        self.current_price = kwargs.get('current_price', 0)
        self.entry_price = kwargs.get('entry_price', 0)
        self.sl_price = kwargs.get('sl_price', 0)
        self.tp1_price = kwargs.get('tp1_price', 0)

        # Signal details
        self.fvg_level = kwargs.get('fvg_level', None)
        self.volume_status = kwargs.get('volume_status', 'NORMAL')
        self.rs_score = kwargs.get('rs_score', 0)
        self.stoch_value = kwargs.get('stoch_value', 0)

        # Risk/Reward
        self.risk_amount = kwargs.get('risk_amount', 0)
        self.reward_amount = kwargs.get('reward_amount', 0)
        self.risk_reward_ratio = kwargs.get('risk_reward_ratio', 0)

        # Additional info
        self.reason = kwargs.get('reason', '')
        self.liquidity_idr = kwargs.get('liquidity_idr', 0)
        self.trend = kwargs.get('trend', 'NEUTRAL')

        # Advanced Filter Details (Phase 1)
        self.zone_type = kwargs.get('zone_type', None)  # 'SWEET_SPOT', 'DISCOUNT', 'PREMIUM'
        self.zone_position = kwargs.get('zone_position', None)  # % position in swing (0.0-1.0)
        self.volume_anomaly = kwargs.get('volume_anomaly', None)  # 'NORMAL', 'PANIC_SELLING', 'ACCUMULATION'
        self.volume_ratio = kwargs.get('volume_ratio', None)  # Volume / MA ratio
        self.rejection_quality = kwargs.get('rejection_quality', None)  # 'STRONG', 'GOOD', 'WEAK', 'NONE'
        self.rejection_details = kwargs.get('rejection_details', None)  # Dict with wick%, close% etc
        self.tp_adjustment = kwargs.get('tp_adjustment', None)  # TP adjustment reason
        self.nearest_resistance = kwargs.get('nearest_resistance', None)  # Resistance level

        # Multi-Timeframe Analysis (Phase 2)
        self.weekly_trend = kwargs.get('weekly_trend', None)  # 'BULLISH', 'BEARISH', 'ALIGNED'
        self.weekly_bars_in_trend = kwargs.get('weekly_bars_in_trend', None)  # Number of weeks in trend

    def to_dict(self) -> dict:
        """Convert signal to dictionary"""
        return {
            'ticker': self.ticker,
            'signal_type': self.signal_type,
            'current_price': self.current_price,
            'entry_price': self.entry_price,
            'sl_price': self.sl_price,
            'tp1_price': self.tp1_price,
            'fvg_level': self.fvg_level,
            'volume_status': self.volume_status,
            'rs_score': self.rs_score,
            'stoch_value': self.stoch_value,
            'risk_reward_ratio': self.risk_reward_ratio,
            'reason': self.reason,
            'liquidity_idr': self.liquidity_idr,
            'trend': self.trend,
            # Advanced filter details
            'zone_type': self.zone_type,
            'zone_position': self.zone_position,
            'volume_anomaly': self.volume_anomaly,
            'volume_ratio': self.volume_ratio,
            'rejection_quality': self.rejection_quality,
            'rejection_details': self.rejection_details,
            'tp_adjustment': self.tp_adjustment,
            'nearest_resistance': self.nearest_resistance,
            # Phase 2
            'weekly_trend': self.weekly_trend,
            'weekly_bars_in_trend': self.weekly_bars_in_trend
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Create Signal object from dictionary
        Used for loading from cache

        Args:
            data: Dictionary with signal data

        Returns:
            Signal object
        """
        return cls(
            ticker=data.get('ticker', ''),
            signal_type=data.get('signal_type', 'NO_SIGNAL'),
            current_price=data.get('current_price', 0),
            entry_price=data.get('entry_price', 0),
            sl_price=data.get('sl_price', 0),
            tp1_price=data.get('tp1_price', 0),
            fvg_level=data.get('fvg_level'),
            volume_status=data.get('volume_status', 'NORMAL'),
            rs_score=data.get('rs_score', 0),
            stoch_value=data.get('stoch_value', 0),
            risk_reward_ratio=data.get('risk_reward_ratio', 0),
            reason=data.get('reason', ''),
            liquidity_idr=data.get('liquidity_idr', 0),
            trend=data.get('trend', 'NEUTRAL'),
            # Advanced filter details (Phase 1)
            zone_type=data.get('zone_type'),
            zone_position=data.get('zone_position'),
            volume_anomaly=data.get('volume_anomaly'),
            volume_ratio=data.get('volume_ratio'),
            rejection_quality=data.get('rejection_quality'),
            rejection_details=data.get('rejection_details'),
            tp_adjustment=data.get('tp_adjustment'),
            nearest_resistance=data.get('nearest_resistance'),
            # Multi-Timeframe Analysis (Phase 2)
            weekly_trend=data.get('weekly_trend'),
            weekly_bars_in_trend=data.get('weekly_bars_in_trend')
        )


class HybridSniperStrategy:
    """Hybrid Sniper trading strategy implementation"""

    def __init__(self):
        pass

    def check_liquidity(self, df: pd.DataFrame) -> tuple:
        """
        Check if stock meets minimum liquidity requirement

        Returns:
            (meets_requirement: bool, avg_value_idr: float)
        """
        # Calculate average daily value (last 20 days)
        recent_data = df.tail(20)
        avg_volume = recent_data['Volume'].mean()
        avg_price = recent_data['Close'].mean()
        avg_value_idr = avg_volume * avg_price

        meets_requirement = avg_value_idr >= MIN_LIQUIDITY_IDR

        return meets_requirement, avg_value_idr

    def get_volume_status(self, current_volume: float, volume_ma: float) -> str:
        """
        Determine volume status relative to moving average

        Returns:
            'LOW', 'NORMAL', or 'HIGH'
        """
        if pd.isna(current_volume) or pd.isna(volume_ma) or volume_ma == 0:
            return 'NORMAL'

        ratio = current_volume / volume_ma

        if ratio < VOLUME_LOW_THRESHOLD:
            return 'LOW'
        elif ratio > VOLUME_HIGH_THRESHOLD:
            return 'HIGH'
        else:
            return 'NORMAL'

    def calculate_position_levels(self, entry_price: float, atr: float) -> dict:
        """
        Calculate SL and TP levels based on ATR

        Returns:
            Dictionary with sl_price, tp1_price, risk, reward, and ratio
        """
        sl_price = entry_price - (SL_ATR_MULTIPLIER * atr)
        tp1_price = entry_price + (TP1_ATR_MULTIPLIER * atr)

        risk = entry_price - sl_price
        reward = tp1_price - entry_price
        ratio = reward / risk if risk > 0 else 0

        return {
            'sl_price': round(sl_price, 2),
            'tp1_price': round(tp1_price, 2),
            'risk': round(risk, 2),
            'reward': round(reward, 2),
            'ratio': round(ratio, 2)
        }

    def check_smc_entry(self, df: pd.DataFrame, ticker: str, strict_mode: bool = False,
                       debug: bool = False) -> Optional[Signal]:
        """
        Check for SMC (Smart Money Concepts) Entry Signal - IMPROVED VERSION

        Phase 1: Existing Filters
        1. Price > SuperTrend (Bullish trend)
        2. Bullish FVG exists
        3. Price in/near FVG zone (10% tolerance)

        Phase 2: Premium vs Discount Zone Filter
        4. Calculate swing-based discount zones
        5. FVG must be in discount zone (<50% of swing)
           → SKIP if FVG in premium zone (>50%)

        Phase 3: Volume Anomaly Detection
        6. Detect volume spike (>3x MA = panic selling)
           → SKIP if panic selling detected
        7. Check distribution pattern (2+ red bars high volume)
           → SKIP if distribution detected

        Phase 4: Rejection Candle Confirmation
        8. Check for rejection candle at FVG
           - Green candle (buyers present)
           - Lower wick >= 40% (rejection)
           - Volume increased
           - Close in upper 60% (strong bounce)
           → SKIP if no rejection confirmation

        Phase 5: Entry Logic (CHANGED!)
        9. Entry = CURRENT price (market order after confirmation)
           NOT FVG mid (limit order)

        Phase 6: Structure-Aware TP
        10. Calculate TP with resistance awareness
            - Standard TP = Entry + 3×ATR
            - Check nearest resistance
            - If TP near resistance → adjust to 98% of resistance
            - Ensure min R:R 1:1.5

        Args:
            strict_mode: If True, price must be IN FVG. If False, within 10%
            debug: If True, print detailed filter analysis

        Returns:
            Signal object or None
        """
        if len(df) < 50:
            return None

        latest = df.iloc[-1]
        current_price = latest['Close']

        # ============================================
        # PHASE 1: Existing Filters
        # ============================================

        # 1. Check daily trend
        if latest['supertrend_direction'] != 1:
            if debug:
                print(f"  ❌ SMC: Bearish daily trend (SuperTrend)")
            return None

        # ============================================
        # PHASE 1.5: Multi-Timeframe Analysis (Phase 2)
        # ============================================

        # 1.5 Check weekly trend alignment
        is_aligned, weekly_info, alignment_msg = check_weekly_daily_alignment(df, debug=debug)
        
        # CHANGED: Don't filter out if not aligned. Just use as info.
        weekly_trend_status = 'ALIGNED' if is_aligned else 'NOT_ALIGNED'
        
        if debug:
            if is_aligned:
                print(f"  ✅ SMC: Weekly-Daily ALIGNED")
            else:
                print(f"  ⚠️ SMC: Weekly-Daily NOT aligned (Aggressive Mode)")
            print(f"      → {alignment_msg}")

        # 2. Check for active FVG
        fvg_zones = get_active_fvg(df, current_price)
        bullish_fvg = fvg_zones['bullish']

        if bullish_fvg is None:
            if debug:
                print(f"  ❌ SMC: No bullish FVG found")
            return None

        # 3. Check if current price is IN or NEAR the FVG zone
        in_fvg_zone = (current_price >= bullish_fvg['bottom'] and
                       current_price <= bullish_fvg['top'])

        # Relaxed mode: check if price is within 15% distance from FVG
        if not strict_mode and not in_fvg_zone:
            fvg_distance_pct = abs(current_price - bullish_fvg['top']) / bullish_fvg['top'] * 100

            if fvg_distance_pct > 15:
                if debug:
                    print(f"  ❌ SMC: Price {fvg_distance_pct:.1f}% away from FVG (>15%)")
                return None
        elif strict_mode and not in_fvg_zone:
            if debug:
                print(f"  ❌ SMC: Price not in FVG zone (strict mode)")
            return None

        # ============================================
        # PHASE 2: Premium vs Discount Zone Filter
        # ============================================

        # 4-5. Calculate discount zones and check FVG position
        zones = calculate_discount_zone(df, lookback=50)
        is_discount, zone_type, fvg_position = is_fvg_in_discount(bullish_fvg, zones)

        if not is_discount:
            if debug:
                print(f"  ❌ SMC: FVG in PREMIUM zone ({fvg_position*100:.1f}% of swing)")
                print(f"      → Avoid buying expensive! Wait for discount zone")
            return None

        if debug:
            print(f"  ✅ SMC: FVG in {zone_type} zone ({fvg_position*100:.1f}% of swing)")

        # ============================================
        # PHASE 3: Volume Anomaly Detection
        # ============================================

        # 6. Check for volume spike (panic selling)
        is_anomaly, anomaly_type, volume_ratio = detect_volume_anomaly(df, threshold=3.0)

        if is_anomaly and anomaly_type == "PANIC_SELLING":
            if debug:
                print(f"  ❌ SMC: PANIC SELLING detected ({volume_ratio:.2f}x volume spike)")
                print(f"      → Avoid catching falling knife!")
            return None

        if debug:
            print(f"  ✅ SMC: Volume anomaly check passed ({anomaly_type}, {volume_ratio:.2f}x)")

        # 7. Check for distribution pattern
        is_distribution, dist_msg = check_distribution_pattern(df)

        if is_distribution:
            if debug:
                print(f"  ❌ SMC: {dist_msg}")
                print(f"      → Smart money distributing, avoid entry!")
            return None

        if debug:
            print(f"  ✅ SMC: No distribution pattern")

        # ============================================
        # PHASE 4: Rejection Candle Confirmation
        # ============================================

        # 8. Check for rejection candle at FVG
        has_rejection, rejection_quality, rejection_details = check_rejection_candle(df, bullish_fvg)

        # ============================================
        # HYBRID MODE: SETUP vs CONFIRMED
        # ============================================

        # Check RS first (applies to both SETUP and CONFIRMED)
        if latest['rs_score'] < RS_WEAK:
            if debug:
                print(f"  ❌ SMC: RS Score {latest['rs_score']:.2f}% < {RS_WEAK}%")
            return None

        # Get volume status and liquidity (needed for both signal types)
        volume_status = self.get_volume_status(latest['Volume'], latest['volume_ma'])
        _, liquidity = self.check_liquidity(df)

        # CASE 1: NO REJECTION → Return SMC_SETUP (Prepare limit order)
        if not has_rejection:
            if debug:
                print(f"  📢 SMC SETUP: No rejection YET ({rejection_quality})")
                print(f"      → {rejection_details['reason']}")
                print(f"      → Prepare LIMIT ORDER at FVG mid")

            # Entry at FVG mid (limit order)
            entry_price_setup = bullish_fvg['mid']

            # Calculate position levels based on FVG mid
            atr = latest['atr']
            sl_price = entry_price_setup - (SL_ATR_MULTIPLIER * atr)
            tp_standard = entry_price_setup + (TP1_ATR_MULTIPLIER * atr)

            # Check for nearest resistance
            nearest_resistance = find_nearest_resistance(df, entry_price_setup, lookback=50)
            tp_final = tp_standard
            tp_reason = f"Standard TP ({TP1_ATR_MULTIPLIER}×ATR)"

            if nearest_resistance is not None:
                distance_to_resistance = (nearest_resistance - tp_standard) / nearest_resistance
                if distance_to_resistance < 0.05:
                    tp_adjusted = nearest_resistance * 0.98
                    risk = entry_price_setup - sl_price
                    reward_adjusted = tp_adjusted - entry_price_setup
                    rr_adjusted = reward_adjusted / risk if risk > 0 else 0

                    if rr_adjusted >= 1.5:
                        tp_final = tp_adjusted
                        tp_reason = f"Adjusted to 98% of resistance @ {nearest_resistance:.0f}"

            # Calculate final levels
            risk = entry_price_setup - sl_price
            reward = tp_final - entry_price_setup
            ratio = reward / risk if risk > 0 else 0

            if debug:
                print(f"  📋 SETUP Entry: {entry_price_setup:.0f} (FVG mid - LIMIT ORDER)")
                print(f"  💰 SL: {sl_price:.0f} | TP: {tp_final:.0f} | R:R {ratio:.2f}")
                print(f"  📢 ACTION: Pasang buy limit order, tunggu konfirmasi!")

            # Create SETUP signal
            signal = Signal(
                ticker=ticker,
                signal_type='SMC_SETUP',  # NEW: Setup signal
                current_price=round(current_price, 2),
                entry_price=round(entry_price_setup, 2),  # FVG mid for limit order
                sl_price=round(sl_price, 2),
                tp1_price=round(tp_final, 2),
                fvg_level=f"{bullish_fvg['bottom']:.0f}-{bullish_fvg['top']:.0f}",
                volume_status=volume_status,
                rs_score=round(latest['rs_score'], 2),
                risk_amount=round(risk, 2),
                reward_amount=round(reward, 2),
                risk_reward_ratio=round(ratio, 2),
                reason=f'SMC Setup: {zone_type} zone, waiting for rejection - Prepare limit order',
                liquidity_idr=liquidity,
                trend='BULLISH',
                # Advanced filter details
                zone_type=zone_type,
                zone_position=round(fvg_position, 3),
                volume_anomaly=anomaly_type,
                volume_ratio=round(volume_ratio, 2),
                rejection_quality='PENDING',  # No rejection yet
                rejection_details={'reason': 'Waiting for buyer confirmation'},
                tp_adjustment=tp_reason,
                nearest_resistance=nearest_resistance,
                # Phase 2: Weekly trend info
                weekly_trend=weekly_trend_status,
                weekly_bars_in_trend=weekly_info['bars_in_trend']
            )
            return signal

        # CASE 2: HAS REJECTION → Return SMC_ENTRY (Execute now)
        if debug:
            print(f"  ✅ SMC CONFIRMED: {rejection_quality} rejection candle!")
            print(f"      → Buyers stepping in with confirmation!")
            print(f"      → EXECUTE MARKET ORDER NOW!")

        # Entry at CURRENT price (market order after rejection)
        entry_price = current_price

        # ============================================
        # PHASE 6: Structure-Aware TP Calculation
        # ============================================

        # 10. Calculate TP with resistance awareness
        atr = latest['atr']

        # Standard SL and TP
        sl_price = entry_price - (SL_ATR_MULTIPLIER * atr)
        tp_standard = entry_price + (TP1_ATR_MULTIPLIER * atr)

        # Check for nearest resistance
        nearest_resistance = find_nearest_resistance(df, entry_price, lookback=50)

        tp_final = tp_standard
        tp_reason = f"Standard TP ({TP1_ATR_MULTIPLIER}×ATR)"

        if nearest_resistance is not None:
            # Calculate distance to resistance
            distance_to_resistance = (nearest_resistance - tp_standard) / nearest_resistance

            # If TP is too close to resistance (within 5%), adjust it
            if distance_to_resistance < 0.05:
                # Place TP at 98% of resistance (safer)
                tp_adjusted = nearest_resistance * 0.98

                # Check if adjusted TP still gives min R:R of 1.5
                risk = entry_price - sl_price
                reward_adjusted = tp_adjusted - entry_price
                rr_adjusted = reward_adjusted / risk if risk > 0 else 0

                if rr_adjusted >= 1.5:
                    tp_final = tp_adjusted
                    tp_reason = f"Adjusted to 98% of resistance @ {nearest_resistance:.0f}"
                    if debug:
                        print(f"  📊 TP adjusted: {tp_standard:.0f} → {tp_final:.0f} (before resistance)")
                else:
                    # If can't meet min R:R, keep standard TP but warn
                    tp_reason = f"Standard TP (resistance @ {nearest_resistance:.0f} too close)"
                    if debug:
                        print(f"  ⚠️ TP kept at standard (adjusted R:R {rr_adjusted:.2f} < 1.5)")
            else:
                tp_reason = f"Standard TP (resistance @ {nearest_resistance:.0f} is safe)"
                if debug:
                    print(f"  ✅ TP safe, resistance far enough @ {nearest_resistance:.0f}")

        # Calculate final levels
        risk = entry_price - sl_price
        reward = tp_final - entry_price
        ratio = reward / risk if risk > 0 else 0

        # Note: volume_status and liquidity already calculated above

        if debug:
            print(f"  💰 Entry: {entry_price:.0f} | SL: {sl_price:.0f} | TP: {tp_final:.0f} | R:R {ratio:.2f}")
            print(f"  📈 Volume: {volume_status} | RS: {latest['rs_score']:.1f}%")
            print(f"  ✅ ALL SMC FILTERS PASSED - HIGH QUALITY SETUP!")

        # Create signal with advanced filter details
        signal = Signal(
            ticker=ticker,
            signal_type='SMC_ENTRY',
            current_price=round(current_price, 2),
            entry_price=round(entry_price, 2),  # Changed: Market order at current price
            sl_price=round(sl_price, 2),
            tp1_price=round(tp_final, 2),
            fvg_level=f"{bullish_fvg['bottom']:.0f}-{bullish_fvg['top']:.0f}",
            volume_status=volume_status,
            rs_score=round(latest['rs_score'], 2),
            risk_amount=round(risk, 2),
            reward_amount=round(reward, 2),
            risk_reward_ratio=round(ratio, 2),
            reason=f'SMC Entry: {zone_type} zone, {rejection_quality} rejection, {tp_reason}',
            liquidity_idr=liquidity,
            trend='BULLISH',
            # Advanced filter details for web UI
            zone_type=zone_type,
            zone_position=round(fvg_position, 3),
            volume_anomaly=anomaly_type,
            volume_ratio=round(volume_ratio, 2),
            rejection_quality=rejection_quality,
            rejection_details=rejection_details,
            tp_adjustment=tp_reason,
            nearest_resistance=nearest_resistance,
            # Phase 2: Weekly trend info
            weekly_trend=weekly_trend_status,
            weekly_bars_in_trend=weekly_info['bars_in_trend']
        )

        return signal

    def check_momentum_entry(self, df: pd.DataFrame, ticker: str, debug: bool = False) -> Optional[Signal]:
        """
        Check for Momentum Entry Signal

        Criteria:
        1. Price > HMA60 AND Price > SuperTrend
        2. Price near HMA60 (within 5% distance) - RELAXED from 2%
        3. Stochastic < 60 (Neutral/Pullback zone) - RELAXED from 30
        4. Stochastic K > D (Momentum turning up) - SIMPLIFIED from golden cross
        5. RS Score > -10 (Not severely underperforming) - RELAXED from 0

        Returns:
            Signal object or None
        """
        if len(df) < 50:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = latest['Close']

        # 1. Trend checks
        if latest['supertrend_direction'] != 1:
            if debug:
                print(f"  ❌ Momentum: Bearish trend (SuperTrend)")
            return None

        if current_price < latest['hma']:
            if debug:
                print(f"  ❌ Momentum: Price {current_price:.0f} < HMA {latest['hma']:.0f}")
            return None

        # 2. Price near HMA (support test) - RELAXED to 8%
        distance_to_hma = abs(current_price - latest['hma']) / latest['hma']
        if distance_to_hma > 0.08:  # More than 8% away (relaxed from 2%)
            if debug:
                print(f"  ❌ Momentum: Distance to HMA {distance_to_hma*100:.1f}% > 8%")
            return None

        # 3. Stochastic pullback zone - RELAXED to 75
        if latest['stoch_k'] > 75:  # Relaxed from 40 to allow more entries
            if debug:
                print(f"  ❌ Momentum: Stoch {latest['stoch_k']:.1f} > 75 (too high)")
            return None

        # 4. Stochastic momentum up - SIMPLIFIED (just K > D)
        if latest['stoch_k'] <= latest['stoch_d']:
            if debug:
                print(f"  ❌ Momentum: Stoch K {latest['stoch_k']:.1f} <= D {latest['stoch_d']:.1f} (momentum down)")
            return None

        # 5. Relative Strength - RELAXED to -10
        if latest['rs_score'] < -10:  # Relaxed from 0
            if debug:
                print(f"  ❌ Momentum: RS {latest['rs_score']:.1f}% < -10%")
            return None

        if debug:
            print(f"  ✅ MOMENTUM ENTRY! Stoch:{latest['stoch_k']:.1f}, HMA dist:{distance_to_hma*100:.1f}%, RS:{latest['rs_score']:.1f}%")

        # CHANGED: Entry at HMA + 1% (Front-run the support) to avoid buying at top
        entry_price_limit = latest['hma'] * 1.01
        
        # Calculate position levels based on LIMIT price, not current price
        levels = self.calculate_position_levels(entry_price_limit, latest['atr'])

        # Get liquidity
        _, liquidity = self.check_liquidity(df)

        # Volume status
        volume_status = self.get_volume_status(latest['Volume'], latest['volume_ma'])

        # Create signal
        signal = Signal(
            ticker=ticker,
            signal_type='MOMENTUM_ENTRY',
            current_price=round(current_price, 2),
            entry_price=round(entry_price_limit, 2), # Limit order near HMA
            sl_price=levels['sl_price'],
            tp1_price=levels['tp1_price'],
            volume_status=volume_status,
            rs_score=round(latest['rs_score'], 2),
            stoch_value=round(latest['stoch_k'], 2),
            risk_amount=levels['risk'],
            reward_amount=levels['reward'],
            risk_reward_ratio=levels['ratio'],
            reason=f'Momentum Entry: Buy near HMA support ({latest["hma"]:.0f})',
            liquidity_idr=liquidity,
            trend='BULLISH'
        )

        return signal

    def analyze_ticker(self, ticker: str, stock_df: pd.DataFrame,
                      ihsg_df: pd.DataFrame = None, debug: bool = False) -> Signal:
        """
        Analyze a ticker and generate trading signal

        Args:
            ticker: Stock ticker symbol
            stock_df: Stock OHLCV DataFrame
            ihsg_df: IHSG DataFrame for RS calculation
            debug: If True, print detailed filter reasons

        Returns:
            Signal object
        """
        # Add indicators
        df = add_all_indicators(stock_df, ihsg_df)

        # Pre-filter: Liquidity check
        meets_liquidity, liquidity = self.check_liquidity(df)

        if not meets_liquidity:
            if debug:
                print(f"{ticker}: ❌ Liquidity {liquidity/1e9:.2f}B < 1B")
            return Signal(
                ticker=ticker,
                signal_type='NO_SIGNAL',
                reason=f'Low Liquidity: {liquidity/1e9:.2f}B IDR (Min: 1B)',
                liquidity_idr=liquidity
            )

        latest = df.iloc[-1]

        # Debug info
        if debug:
            print(f"\n{ticker} Analysis:")
            print(f"  Price: {latest['Close']:.0f}")
            print(f"  HMA60: {latest['hma']:.0f} (Distance: {abs(latest['Close'] - latest['hma']) / latest['hma'] * 100:.1f}%)")
            print(f"  Trend: {'BULLISH' if latest['supertrend_direction'] == 1 else 'BEARISH'}")
            print(f"  Stochastic: K={latest['stoch_k']:.1f}, D={latest['stoch_d']:.1f}")
            print(f"  Volume Ratio: {latest['volume_ratio']:.2f}x")
            print(f"  RS Score: {latest['rs_score']:.2f}%")

            fvg_zones = get_active_fvg(df, latest['Close'])
            if fvg_zones['bullish']:
                fvg = fvg_zones['bullish']
                print(f"  Bullish FVG: {fvg['bottom']:.0f} - {fvg['top']:.0f}")
                distance = abs(latest['Close'] - fvg['top']) / fvg['top'] * 100
                print(f"  Distance to FVG: {distance:.1f}%")
            else:
                print(f"  Bullish FVG: None")

        # Check for SMC Entry (Priority #1) - RELAXED MODE by default
        smc_signal = self.check_smc_entry(df, ticker, strict_mode=False, debug=debug)
        if smc_signal:
            if debug:
                print(f"  ✅ SMC Entry Signal!")
            return smc_signal

        # Check for Momentum Entry (Priority #2)
        momentum_signal = self.check_momentum_entry(df, ticker, debug=debug)
        if momentum_signal:
            if debug:
                print(f"  ✅ Momentum Entry Signal!")
            return momentum_signal

        # No signal - but check if "approaching" setup
        trend = 'BULLISH' if latest['supertrend_direction'] == 1 else 'BEARISH'

        # Check for "approaching" conditions (for watchlist)
        reason = 'No entry setup at current price'

        if trend == 'BEARISH':
            fvg_zones = get_active_fvg(df, latest['Close'])
            if fvg_zones['bullish']:
                fvg = fvg_zones['bullish']
                distance_pct = abs(latest['Close'] - fvg['top']) / fvg['top'] * 100

                if distance_pct <= 15:  # Within 15% of FVG
                    vol_status = self.get_volume_status(latest['Volume'], latest['volume_ma'])
                    reason = f'Bearish trend, but has FVG @ {fvg["bottom"]:.0f}-{fvg["top"]:.0f} ({distance_pct:.1f}% away) - Watch for reversal'

                    if debug:
                        print(f"  ⚠️ WATCHLIST: Has setup but bearish trend")
            else:
                reason = 'Bearish trend, no FVG zones'

        if debug and reason == 'No entry setup at current price':
            print(f"  ℹ️ No entry setup")

        return Signal(
            ticker=ticker,
            signal_type='NO_SIGNAL',
            current_price=round(latest['Close'], 2),
            reason=reason,
            liquidity_idr=liquidity,
            trend=trend,
            rs_score=round(latest['rs_score'], 2)
        )

    def scan_tickers(self, tickers: List[str], data_engine) -> List[Signal]:
        """
        Scan multiple tickers for signals

        Args:
            tickers: List of ticker symbols
            data_engine: DataEngine instance

        Returns:
            List of Signal objects
        """
        signals = []

        # Get IHSG data for RS calculation
        ihsg_df = data_engine.get_ihsg_data()

        for ticker in tickers:
            try:
                # Get stock data
                stock_df = data_engine.get_ticker_data(ticker)

                if stock_df is None or stock_df.empty:
                    continue

                # Analyze
                signal = self.analyze_ticker(ticker, stock_df, ihsg_df)
                signals.append(signal)

            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
                continue

        return signals

    def filter_signals(self, signals: List[Signal],
                      signal_types: List[str] = None,
                      min_rs: float = None) -> List[Signal]:
        """
        Filter signals based on criteria

        Args:
            signals: List of Signal objects
            signal_types: List of signal types to include (e.g., ['SMC_ENTRY'])
            min_rs: Minimum RS score

        Returns:
            Filtered list of Signal objects
        """
        filtered = signals

        if signal_types:
            filtered = [s for s in filtered if s.signal_type in signal_types]

        if min_rs is not None:
            filtered = [s for s in filtered if s.rs_score >= min_rs]

        return filtered


# Initialize global strategy
strategy = HybridSniperStrategy()
