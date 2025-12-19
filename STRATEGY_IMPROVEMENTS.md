# 🎯 Strategy Improvements - Critical Issues & Solutions

**Analysis of Current Weaknesses & Implementation Plan**

---

## 📊 Critical Issues Identified

### 1. ❌ SMC Entry - Catching Falling Knife

**Current Logic:**
```python
# Entry di tengah FVG tanpa konfirmasi
entry_price = fvg['mid']  # Limit order blind
if volume < volume_ma:    # Low volume saja
    → ENTER
```

**Problem:**
- 🔴 Limit order di tengah FVG = **catching falling knife**
- 🔴 LOW volume ≠ ada pembeli (bisa sepi karena takut)
- 🔴 Tidak ada konfirmasi rejection/pantulan
- 🔴 Risk tinggi di second liner IDX

**Solution:**
```python
# Tambah konfirmasi REJECTION CANDLE
def check_rejection_candle(df, fvg_zone):
    latest = df.iloc[-1]

    # 1. Price harus MASUK FVG zone
    if not (latest['Low'] <= fvg_zone['top']):
        return False

    # 2. Candle harus GREEN (buyer muncul)
    if latest['Close'] <= latest['Open']:
        return False

    # 3. Lower wick minimal 40% dari total range (rejection)
    body = abs(latest['Close'] - latest['Open'])
    lower_wick = latest['Open'] - latest['Low']
    total_range = latest['High'] - latest['Low']

    if lower_wick < (total_range * 0.4):  # Wick < 40%
        return False

    # 4. Volume harus NAIK saat rejection (buyer aktif)
    if latest['Volume'] <= df['Volume'].rolling(5).mean().iloc[-1]:
        return False

    # 5. Close harus di upper 60% dari range (strong rejection)
    close_position = (latest['Close'] - latest['Low']) / total_range
    if close_position < 0.6:  # Close < 60% dari bottom
        return False

    return True  # ✅ Valid rejection candle!

# Entry HANYA setelah rejection confirmed
if price_in_fvg and check_rejection_candle(df, fvg):
    entry_price = latest['Close']  # Market order, bukan limit!
```

**Benefits:**
- ✅ Entry setelah ada bukti buyer
- ✅ Rejection wick = support confirmed
- ✅ Volume naik = institutional buying
- ✅ Avoid knife catching

---

### 2. ❌ FVG Quality - Premium vs Discount Zone

**Current Logic:**
```python
# Semua FVG dianggap sama
if bullish_fvg_exists:
    → ENTER  # Tanpa cek posisi di swing
```

**Problem:**
- 🔴 FVG di puncak rally (premium) = jebol
- 🔴 Tidak ada konsep discount zone
- 🔴 Beli di area mahal (>50% swing)

**Solution:**
```python
def calculate_discount_zone(df, lookback=50):
    """
    Hitung swing high/low untuk premium vs discount zone
    Premium: >50% dari swing range (MAHAL - avoid!)
    Discount: <50% dari swing range (MURAH - buy!)
    """
    recent = df.tail(lookback)

    swing_high = recent['High'].max()
    swing_low = recent['Low'].min()
    swing_range = swing_high - swing_low

    # Equilibrium = 50% level
    equilibrium = swing_low + (swing_range * 0.5)

    # Premium zone = 50% - 100% (atas)
    premium_threshold = swing_low + (swing_range * 0.5)

    # Discount zone = 0% - 50% (bawah)
    discount_threshold = swing_low + (swing_range * 0.5)

    return {
        'swing_high': swing_high,
        'swing_low': swing_low,
        'equilibrium': equilibrium,
        'premium_start': premium_threshold,
        'discount_end': discount_threshold
    }

def is_fvg_in_discount(fvg, zones):
    """
    FVG harus berada di DISCOUNT zone (<50% swing)
    """
    fvg_mid = (fvg['top'] + fvg['bottom']) / 2

    # FVG mid harus di bawah equilibrium
    if fvg_mid > zones['equilibrium']:
        return False  # Premium zone - SKIP!

    # Ideal: FVG di 20%-40% zone (sweet spot)
    fvg_position = (fvg_mid - zones['swing_low']) / (zones['swing_high'] - zones['swing_low'])

    if 0.2 <= fvg_position <= 0.4:
        return True, "SWEET_SPOT"  # ✅ Perfect discount
    elif fvg_position < 0.5:
        return True, "DISCOUNT"     # ✅ OK discount
    else:
        return False, "PREMIUM"     # ❌ Too expensive

# Usage dalam SMC entry
zones = calculate_discount_zone(df)
is_discount, zone_type = is_fvg_in_discount(fvg, zones)

if not is_discount:
    return None  # SKIP FVG di premium zone!
```

**Benefits:**
- ✅ Beli di area MURAH (discount)
- ✅ Avoid FVG di puncak rally
- ✅ Align dengan SMC principle
- ✅ Better risk/reward

---

### 3. ❌ Multi-Timeframe Analysis

**Current Logic:**
```python
# Hanya pakai daily data
df_daily = get_ticker_data(ticker)
# Tidak cek weekly
```

**Problem:**
- 🔴 Daily bullish tapi weekly bearish = trap!
- 🔴 Missing bigger picture
- 🔴 Tren harian sering noise

**Solution:**
```python
def get_weekly_data(ticker):
    """
    Fetch weekly data untuk bigger picture
    """
    daily_df = data_engine.get_ticker_data(ticker)

    # Resample ke weekly
    weekly_df = daily_df.resample('W-FRI', on='Date').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })

    # Add indicators to weekly
    weekly_df = add_all_indicators(weekly_df, ihsg_weekly)

    return weekly_df

def check_weekly_trend_alignment(daily_df, weekly_df):
    """
    Daily trend HARUS aligned dengan weekly trend
    """
    latest_daily = daily_df.iloc[-1]
    latest_weekly = weekly_df.iloc[-1]

    # 1. Weekly harus bullish (SuperTrend green)
    if latest_weekly['supertrend_direction'] != 1:
        return False, "Weekly bearish"

    # 2. Weekly HMA harus naik (slope positif)
    weekly_hma_slope = latest_weekly['hma'] - weekly_df['hma'].iloc[-2]
    if weekly_hma_slope < 0:
        return False, "Weekly HMA declining"

    # 3. Daily price harus di atas weekly HMA
    if latest_daily['Close'] < latest_weekly['hma']:
        return False, "Price below weekly HMA"

    # 4. Cek weekly resistance
    weekly_swing_high = weekly_df['High'].tail(20).max()
    distance_to_resistance = (weekly_swing_high - latest_daily['Close']) / latest_daily['Close']

    if distance_to_resistance < 0.05:  # < 5% dari resistance
        return False, "Too close to weekly resistance"

    return True, "Weekly aligned"

# Usage
weekly_df = get_weekly_data(ticker)
is_aligned, reason = check_weekly_trend_alignment(df, weekly_df)

if not is_aligned:
    return None  # SKIP jika weekly tidak support!
```

**Benefits:**
- ✅ Confirm daily trend dengan weekly
- ✅ Avoid false breakout
- ✅ Better probability
- ✅ See bigger picture

---

### 4. ❌ Liquidity Threshold

**Current Logic:**
```python
MIN_LIQUIDITY_IDR = 1_000_000_000  # 1 Miliar
```

**Problem:**
- 🔴 1B terlalu kecil untuk IDX
- 🔴 Spread lebar (lompat-lompat)
- 🔴 Bandar manipulation risk

**Solution:**
```python
# Update settings.py
MIN_LIQUIDITY_IDR = 5_000_000_000  # 5 Miliar (safer!)

def calculate_spread_percentage(df):
    """
    Hitung average spread percentage
    Spread = (Ask - Bid) / Mid

    Untuk IDX, estimate dari High-Low intraday
    """
    recent = df.tail(20)

    # Estimate spread dari intraday range
    intraday_range = recent['High'] - recent['Low']
    mid_price = (recent['High'] + recent['Low']) / 2

    spread_pct = (intraday_range / mid_price * 100).mean()

    return spread_pct

def check_spread_quality(df):
    """
    Spread harus < 2% untuk safe execution
    """
    spread = calculate_spread_percentage(df)

    if spread > 2.0:
        return False, f"Spread too wide: {spread:.2f}%"
    elif spread > 1.0:
        return True, f"Spread acceptable: {spread:.2f}%"
    else:
        return True, f"Spread tight: {spread:.2f}%"

# Usage
is_ok, msg = check_spread_quality(df)
if not is_ok:
    return None  # SKIP jika spread terlalu lebar
```

**Benefits:**
- ✅ Safer liquidity level
- ✅ Tighter spread
- ✅ Better execution
- ✅ Less manipulation risk

---

### 5. ❌ Price Fraction & Volatility

**Current Logic:**
```python
# ATR multiplier sama untuk semua harga
SL_ATR_MULTIPLIER = 2.0  # Fix untuk semua saham
```

**Problem:**
- 🔴 Saham 50-200 (gocap) vs >2000 beda karakter
- 🔴 Fraksi 1 punya volatility brutal
- 🔴 Risk/reward tidak adil

**Solution:**
```python
def get_price_tier(price):
    """
    Kategorikan saham berdasarkan harga & fraksi
    """
    if price < 200:
        return "GOCAP"      # Fraksi 1 - sangat volatile
    elif price < 500:
        return "LOW_PRICE"  # Fraksi 2 - volatile
    elif price < 2000:
        return "MID_PRICE"  # Fraksi 5 - moderate
    elif price < 5000:
        return "HIGH_PRICE" # Fraksi 25 - stable
    else:
        return "BLUE_CHIP"  # Fraksi 50 - very stable

def get_adaptive_atr_multipliers(price):
    """
    ATR multiplier disesuaikan dengan tier harga
    """
    tier = get_price_tier(price)

    multipliers = {
        "GOCAP": {
            "sl": 3.0,   # Wider SL (volatility tinggi)
            "tp1": 4.5,  # Wider TP
            "min_rr": 1.5
        },
        "LOW_PRICE": {
            "sl": 2.5,
            "tp1": 4.0,
            "min_rr": 1.6
        },
        "MID_PRICE": {
            "sl": 2.0,
            "tp1": 3.5,
            "min_rr": 1.75
        },
        "HIGH_PRICE": {
            "sl": 1.5,
            "tp1": 3.0,
            "min_rr": 2.0
        },
        "BLUE_CHIP": {
            "sl": 1.5,
            "tp1": 2.5,
            "min_rr": 1.67
        }
    }

    return multipliers[tier]

# Usage
multipliers = get_adaptive_atr_multipliers(current_price)
sl_price = entry_price - (multipliers['sl'] * atr)
tp1_price = entry_price + (multipliers['tp1'] * atr)
```

**Benefits:**
- ✅ Adaptive risk management
- ✅ Fair untuk semua tier harga
- ✅ Better suited untuk IDX
- ✅ Reduce whipsaw di gocap

---

### 6. ❌ Volume Spike Detection

**Current Logic:**
```python
# Hanya cek volume < MA
if volume < volume_ma:
    # LOW volume = good
```

**Problem:**
- 🔴 Tidak detect volume anomaly
- 🔴 Volume spike 3x = distribusi!
- 🔴 Miss panic selling signal

**Solution:**
```python
def detect_volume_anomaly(df, threshold=3.0):
    """
    Detect volume spike during pullback
    Spike > 3x average = DANGER (distribusi/panic)
    """
    latest = df.iloc[-1]
    volume_ma = df['Volume'].rolling(20).mean().iloc[-1]

    volume_ratio = latest['Volume'] / volume_ma

    # 1. Volume spike > 3x = RED FLAG
    if volume_ratio > threshold:
        # Cek apakah candle merah (selling pressure)
        if latest['Close'] < latest['Open']:
            return True, "PANIC_SELLING", volume_ratio
        else:
            # Green candle dengan volume spike = accumulation (OK!)
            return False, "ACCUMULATION", volume_ratio

    # 2. Volume normal
    return False, "NORMAL", volume_ratio

def check_distribution_pattern(df):
    """
    Detect distribution pattern (volume tinggi, harga turun)
    """
    recent = df.tail(5)

    # Cek apakah ada 2+ candle merah dengan volume tinggi
    red_candles = recent[recent['Close'] < recent['Open']]

    if len(red_candles) >= 2:
        avg_red_volume = red_candles['Volume'].mean()
        avg_total_volume = recent['Volume'].mean()

        if avg_red_volume > (avg_total_volume * 1.5):
            return True, "Distribution detected"

    return False, "No distribution"

# Usage
is_anomaly, anomaly_type, ratio = detect_volume_anomaly(df)

if is_anomaly and anomaly_type == "PANIC_SELLING":
    return None  # ❌ SKIP! Distribusi detected!

is_distribution, msg = check_distribution_pattern(df)
if is_distribution:
    return None  # ❌ SKIP! Distribution pattern!
```

**Benefits:**
- ✅ Avoid panic selling
- ✅ Detect distribusi
- ✅ Differentiate accumulation vs distribution
- ✅ Better entry quality

---

### 7. ❌ TP Placement - Market Structure Aware

**Current Logic:**
```python
# Fixed ATR multiplier
tp1_price = entry + (3.0 * atr)  # Tanpa cek resistance
```

**Problem:**
- 🔴 TP bisa tepat di resistance
- 🔴 Price reversal sebelum kena TP
- 🔴 Ignore market structure

**Solution:**
```python
def find_nearest_resistance(df, entry_price, lookback=50):
    """
    Cari swing high terdekat sebagai resistance
    """
    recent = df.tail(lookback)

    # Cari semua swing highs
    swing_highs = []
    for i in range(2, len(recent)-2):
        if (recent['High'].iloc[i] > recent['High'].iloc[i-1] and
            recent['High'].iloc[i] > recent['High'].iloc[i-2] and
            recent['High'].iloc[i] > recent['High'].iloc[i+1] and
            recent['High'].iloc[i] > recent['High'].iloc[i+2]):

            swing_highs.append({
                'price': recent['High'].iloc[i],
                'date': recent.index[i]
            })

    # Filter swing highs di atas entry
    resistances = [s['price'] for s in swing_highs if s['price'] > entry_price]

    if resistances:
        return min(resistances)  # Nearest resistance
    else:
        return None

def calculate_structure_aware_tp(entry, atr, df):
    """
    TP placement dengan pertimbangan market structure
    """
    # Standard ATR-based TP
    standard_tp = entry + (3.0 * atr)

    # Cari resistance terdekat
    nearest_resistance = find_nearest_resistance(df, entry)

    if nearest_resistance:
        # Jarak ke resistance
        distance_to_resistance = nearest_resistance - entry
        distance_to_standard_tp = standard_tp - entry

        # Jika standard TP terlalu dekat resistance (<5%), adjust
        if standard_tp > (nearest_resistance * 0.95):  # Within 5% of resistance
            # Set TP 2% sebelum resistance (safety margin)
            adjusted_tp = nearest_resistance * 0.98

            # Pastikan masih ada R:R minimal 1:2
            risk = atr * 2.0  # Assuming SL at 2*ATR
            reward = adjusted_tp - entry

            if reward / risk >= 1.5:  # Min R:R 1:1.5
                return adjusted_tp, "ADJUSTED_FOR_RESISTANCE"
            else:
                return None, "INSUFFICIENT_RR_AT_RESISTANCE"
        else:
            return standard_tp, "STANDARD_TP"
    else:
        return standard_tp, "NO_RESISTANCE_FOUND"

# Usage
tp_price, tp_reason = calculate_structure_aware_tp(entry_price, atr, df)

if tp_price is None:
    return None  # Skip jika R:R tidak cukup
```

**Benefits:**
- ✅ Avoid TP di resistance
- ✅ Structure-aware exits
- ✅ Better fill rate
- ✅ Respect market structure

---

## 📊 Implementation Priority

### Phase 1: Critical (Immediate)
1. ✅ **Rejection Candle Confirmation** - Avoid knife catching
2. ✅ **Premium vs Discount Zone** - Buy cheap only
3. ✅ **Volume Spike Detection** - Avoid panic/distribution

### Phase 2: Important (This Week)
4. ✅ **Multi-Timeframe Analysis** - Weekly confirmation
5. ✅ **Liquidity & Spread Filter** - Safer execution
6. ✅ **Market Structure TP** - Better exits

### Phase 3: Enhancement (Next Week)
7. ✅ **Adaptive ATR by Price Tier** - Fair risk management

---

## 🎯 Expected Improvements

### Before:
- Hit Rate: 20% (banyak false signals)
- Win Rate: 45-55% (avg)
- R:R: 1:1.5 (suboptimal)
- Knife catching: HIGH risk
- Execution: Spread issues

### After:
- Hit Rate: 10-15% (lebih selektif, lebih quality)
- Win Rate: 55-65% (better quality)
- R:R: 1:2 to 1:3 (optimal)
- Knife catching: MINIMAL risk
- Execution: Better fills

---

## ✅ Testing Plan

```bash
# Test dengan improvements
python main.py scan --debug --limit 50

# Verify:
# 1. Rejection candle detected
# 2. FVG in discount zone only
# 3. Volume spike avoided
# 4. Weekly alignment checked
# 5. TP adjusted for resistance
```

---

**Next:** Implement improvements satu per satu dengan testing di setiap step.
