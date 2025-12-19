# Tutorial Page Content for Streamlit
# This content will be inserted into app.py

tutorial_content = """
# ===================================================================
# PAGE 0: TUTORIAL & GUIDE
# ===================================================================

if page == "📖 Tutorial & Guide":
    st.title("📖 Tutorial & User Guide")
    st.markdown("*Learn how to use IDX Hybrid Sniper effectively*")

    # Quick Start Section
    st.header("🚀 Quick Start (5 Minutes)")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1️⃣ Setup")
        st.code('''# Import watchlist
python main.py import-csv --file watchlist_template.csv

# Update data
python main.py update --full

# First scan
python main.py scan''', language="bash")

        st.subheader("2️⃣ Daily Workflow")
        st.markdown('''
        1. ✅ Morning: Run `python main.py scan`
        2. ✅ Review signals in **Market Screener** tab
        3. ✅ Analyze charts in **Chart Analysis** tab
        4. ✅ Execute trades during market hours
        5. ✅ Update **Trading Journal** after close
        ''')

    with col2:
        st.subheader("3️⃣ Strategy Overview")
        st.info('''
        **SMC Entry (Priority #1)**
        - Buy on low-volume pullback
        - Entry at FVG (Fair Value Gap) zones
        - Trend: Bullish (SuperTrend green)

        **Momentum Entry (Priority #2)**
        - Buy at HMA60 support bounce
        - Stochastic turning up (< 60)
        - Trend: Bullish continuation
        ''')

        st.success('''
        **Risk Management**
        - 2% risk per trade
        - ATR-based Stop Loss & Take Profit
        - R:R Ratio: 1:3 target
        - Exit: 50% at TP1, trail 50% with SuperTrend
        ''')

    st.markdown("---")

    # Tab-by-Tab Guide
    st.header("📚 How to Use Each Tab")

    tab1, tab2, tab3 = st.tabs(["📊 Market Screener", "📈 Chart Analysis", "📔 Trading Journal"])

    with tab1:
        st.subheader("Market Screener Usage")

        st.markdown('''
        ### Purpose
        Scan 900+ IDX stocks to find high-probability entry setups.

        ### Step-by-Step
        1. **Update Data** (if needed)
           - Click `🔄 Update All Data` in sidebar
           - Wait for confirmation

        2. **Run Scan**
           - Click `🚀 Scan Market` button
           - Wait for progress bar

        3. **Review Results**
           - **SMC Signals**: Pullback entries at FVG zones
           - **Momentum Signals**: HMA support bounces
           - Sort by RS Score or R:R ratio

        4. **Analyze Top Signals**
           - Click ticker to view in Chart Analysis
           - Check FVG zones and indicators

        ### Signal Quality Guide

        | Quality | Criteria | Action |
        |---------|----------|--------|
        | 🟢 **Best** | SMC + LOW vol + RS >+10% | Top priority |
        | 🟡 **Good** | SMC + NORMAL vol + RS >0% | Consider |
        | 🔴 **Watch** | Negative RS or HIGH vol | Be careful |
        ''')

    with tab2:
        st.subheader("Chart Analysis Usage")

        st.markdown('''
        ### Purpose
        Deep-dive technical analysis on individual stocks.

        ### Understanding the Chart

        **Main Chart (Top):**
        - 🟢 **Green Line** → HMA60 (support/resistance)
        - 🔴/🟢 **Dots** → SuperTrend (red=bearish, green=bullish)
        - 🟦 **Blue Boxes** → Bullish FVG zones (entry areas)
        - 🟪 **Purple Boxes** → Bearish FVG zones (resistance)

        **Volume Panel (Middle):**
        - 📊 **Bars** → Daily volume
        - 🔵 **Line** → Volume MA
        - Compare current vs average

        **Stochastic Panel (Bottom):**
        - 🔵 **Blue** → Stochastic K
        - 🟠 **Orange** → Stochastic D
        - 🔴 **>80** → Overbought
        - 🟢 **<20** → Oversold

        ### Entry Checklist

        **SMC Entry:**
        ```
        ✅ Price in blue box (FVG zone)
        ✅ SuperTrend = Green
        ✅ Volume = LOW
        ✅ RS Score > 0%

        → ENTER at FVG mid-level
        ```

        **Momentum Entry:**
        ```
        ✅ Price bouncing from HMA60
        ✅ SuperTrend = Green
        ✅ Stochastic K > D and < 60
        ✅ RS Score > -10%

        → ENTER immediately
        ```
        ''')

    with tab3:
        st.subheader("Trading Journal Usage")

        st.markdown('''
        ### Purpose
        Track performance and improve over time.

        ### How to Use

        **Adding Trade:**
        1. Fill form in sidebar (ticker, entry date, price, size)
        2. Select strategy type (SMC/Momentum)
        3. Click `Add Trade`

        **Closing Trade:**
        1. Select trade from Active Trades table
        2. Enter exit date and exit price
        3. Click `Close Trade`
        4. P/L calculated automatically

        ### Position Sizing Formula

        ```python
        # Risk 2% per trade
        capital = 100_000_000  # Your capital
        risk_percent = 0.02    # 2%

        entry = 1000
        stop_loss = 950

        risk_per_share = entry - stop_loss  # 50
        risk_amount = capital * risk_percent  # 2M

        position_size = risk_amount / risk_per_share
        # = 2,000,000 / 50 = 40,000 shares
        ```

        ### Best Practices

        ✅ **DO:**
        - Log EVERY trade (wins and losses)
        - Review weekly
        - Accept losses quickly
        - Follow system rules

        ❌ **DON'T:**
        - Skip losing trades
        - Edit past trades
        - Increase size after wins
        - Ignore stop loss
        ''')

    st.markdown("---")

    # Strategy Deep Dive
    st.header("🎯 Strategy Explained")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💎 Smart Money Concepts (SMC)")
        st.markdown('''
        ### Philosophy
        "Buy on Weakness, Sell on Strength"

        ### What is FVG?
        Fair Value Gap = Price inefficiency that tends to get filled.

        **Formation:**
        - 3-candle pattern
        - Candle 3 Low > Candle 1 High
        - Gap > ATR threshold

        ### Why It Works
        - Institutions leave footprints (FVG)
        - We follow their accumulation zones
        - Buy when they buy (low volume)
        - Exit when they distribute (breakout)

        ### Criteria
        | Filter | Requirement |
        |--------|-------------|
        | Trend | SuperTrend = Bullish |
        | FVG | Price in/near zone (±10%) |
        | Volume | < Average (LOW = best) |
        | RS | > -5% (not severely weak) |
        ''')

    with col2:
        st.subheader("⚡ Momentum Entry")
        st.markdown('''
        ### Philosophy
        "Ride the Monster Trend"

        ### What is HMA Support?
        Hull Moving Average = Dynamic support in uptrends.

        **Why HMA?**
        - Lag-reduced (faster response)
        - Smooth (filters noise)
        - Dynamic (adjusts to volatility)

        ### Why It Works
        - Strong trends respect HMA
        - Pullbacks to HMA = high-probability bounces
        - Stochastic confirms momentum
        - Trail with SuperTrend for exits

        ### Criteria
        | Filter | Requirement |
        |--------|-------------|
        | Trend | Price > HMA & SuperTrend green |
        | Distance | < 5% from HMA |
        | Stochastic | < 60 & K > D |
        | RS | > -10% |
        ''')

    st.markdown("---")

    # Risk Management
    st.header("🛡️ Risk Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Risk Per Trade", "2%")
        st.caption("Maximum risk per position")

        st.metric("Stop Loss", "Entry - 2×ATR")
        st.caption("Volatility-adjusted")

    with col2:
        st.metric("Take Profit", "Entry + 3×ATR")
        st.caption("R:R = 1:1.5 minimum")

        st.metric("Exit Strategy", "50% at TP1")
        st.caption("Trail 50% with SuperTrend")

    with col3:
        st.metric("Win Rate Target", "45-55%")
        st.caption("Expected with discipline")

        st.metric("Max Drawdown", "10-15%")
        st.caption("Stay within limits")

    st.markdown("---")

    # Resources
    st.header("📚 Additional Resources")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📖 Documentation")
        st.markdown('''
        - **USER_GUIDE.md** - Comprehensive guide
        - **QUICK_START.md** - 5-minute setup
        - **TICKER_MANAGEMENT.md** - Watchlist guide
        - **CSV_IMPORT_GUIDE.md** - CSV format
        ''')

        st.subheader("⌨️ CLI Commands")
        st.code('''# Show all commands
python main.py help

# Quick start guide
python main.py guide

# Debug scan
python main.py scan --debug --limit 10''', language="bash")

    with col2:
        st.subheader("💡 Pro Tips")
        st.markdown('''
        1. Start with **paper trading** (1 week)
        2. Always use **stop loss**
        3. Log **every trade**
        4. Review **weekly**
        5. Don't **chase price**
        6. **2% risk** maximum
        7. Trade the **setup**
        8. **Process** > Outcome
        9. **Consistency** wins
        10. **Discipline** is the edge
        ''')

        st.info('''
        **Expected Performance:**
        - Win Rate: 45-55%
        - Trades/month: 10-20
        - Annual Return: 30-60%

        *With discipline & risk management*
        ''')

    st.markdown("---")
    st.success("💪 Ready to trade? Start with **Market Screener** tab!")

# ===================================================================
# PAGE 1: MARKET SCREENER
# ===================================================================

elif page == "📊 Market Screener":
"""
