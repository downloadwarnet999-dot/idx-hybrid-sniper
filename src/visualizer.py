"""
IDX Hybrid Sniper - Chart Visualizer
Interactive Plotly charts for web dashboard
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    CHART_HEIGHT, CHART_TEMPLATE,
    COLOR_BULLISH, COLOR_BEARISH, COLOR_NEUTRAL
)
from src.indicators import add_all_indicators, get_active_fvg


def create_candlestick_chart(df: pd.DataFrame, ticker: str,
                             ihsg_df: pd.DataFrame = None,
                             show_volume: bool = True) -> go.Figure:
    """
    Create interactive candlestick chart with all indicators

    Args:
        df: Stock OHLCV DataFrame
        ticker: Stock ticker symbol
        ihsg_df: IHSG DataFrame for RS calculation
        show_volume: Whether to show volume subplot

    Returns:
        Plotly Figure object
    """
    # Add indicators
    df_plot = add_all_indicators(df.copy(), ihsg_df)

    # Create figure with subplots
    if show_volume:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=(f'{ticker} - Hybrid Sniper Analysis', 'Volume', 'Stochastic')
        )
    else:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} - Hybrid Sniper Analysis', 'Stochastic')
        )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df_plot.index,
            open=df_plot['Open'],
            high=df_plot['High'],
            low=df_plot['Low'],
            close=df_plot['Close'],
            name='Price',
            increasing_line_color=COLOR_BULLISH,
            decreasing_line_color=COLOR_BEARISH
        ),
        row=1, col=1
    )

    # HMA
    fig.add_trace(
        go.Scatter(
            x=df_plot.index,
            y=df_plot['hma'],
            name='HMA 60',
            line=dict(color='#2962FF', width=2)
        ),
        row=1, col=1
    )

    # SuperTrend
    # Split into bullish and bearish segments
    bullish_mask = df_plot['supertrend_direction'] == 1
    bearish_mask = df_plot['supertrend_direction'] == -1

    # Bullish SuperTrend
    fig.add_trace(
        go.Scatter(
            x=df_plot[bullish_mask].index,
            y=df_plot[bullish_mask]['supertrend'],
            name='SuperTrend (Bull)',
            line=dict(color=COLOR_BULLISH, width=2),
            mode='lines'
        ),
        row=1, col=1
    )

    # Bearish SuperTrend
    fig.add_trace(
        go.Scatter(
            x=df_plot[bearish_mask].index,
            y=df_plot[bearish_mask]['supertrend'],
            name='SuperTrend (Bear)',
            line=dict(color=COLOR_BEARISH, width=2),
            mode='lines'
        ),
        row=1, col=1
    )

    # Fair Value Gaps (FVG)
    # Get active FVG zones
    current_price = df_plot['Close'].iloc[-1]
    fvg_zones = get_active_fvg(df_plot, current_price)

    if fvg_zones['bullish']:
        fvg = fvg_zones['bullish']
        fig.add_shape(
            type="rect",
            x0=fvg['date'],
            x1=df_plot.index[-1],
            y0=fvg['bottom'],
            y1=fvg['top'],
            fillcolor=COLOR_BULLISH,
            opacity=0.2,
            line=dict(width=1, dash='dash', color=COLOR_BULLISH),
            row=1, col=1
        )
        fig.add_annotation(
            x=df_plot.index[-1],
            y=fvg['mid'],
            text="Bullish FVG",
            showarrow=False,
            font=dict(size=10, color=COLOR_BULLISH),
            row=1, col=1
        )

    if fvg_zones['bearish']:
        fvg = fvg_zones['bearish']
        fig.add_shape(
            type="rect",
            x0=fvg['date'],
            x1=df_plot.index[-1],
            y0=fvg['bottom'],
            y1=fvg['top'],
            fillcolor=COLOR_BEARISH,
            opacity=0.2,
            line=dict(width=1, dash='dash', color=COLOR_BEARISH),
            row=1, col=1
        )
        fig.add_annotation(
            x=df_plot.index[-1],
            y=fvg['mid'],
            text="Bearish FVG",
            showarrow=False,
            font=dict(size=10, color=COLOR_BEARISH),
            row=1, col=1
        )

    # Volume
    if show_volume:
        colors = [COLOR_BULLISH if row['Close'] >= row['Open'] else COLOR_BEARISH
                 for _, row in df_plot.iterrows()]

        fig.add_trace(
            go.Bar(
                x=df_plot.index,
                y=df_plot['Volume'],
                name='Volume',
                marker=dict(color=colors)
            ),
            row=2, col=1
        )

        # Volume MA
        fig.add_trace(
            go.Scatter(
                x=df_plot.index,
                y=df_plot['volume_ma'],
                name='Vol MA',
                line=dict(color='orange', width=1)
            ),
            row=2, col=1
        )

    # Stochastic
    stoch_row = 3 if show_volume else 2

    fig.add_trace(
        go.Scatter(
            x=df_plot.index,
            y=df_plot['stoch_k'],
            name='Stoch %K',
            line=dict(color='#2962FF', width=1.5)
        ),
        row=stoch_row, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot.index,
            y=df_plot['stoch_d'],
            name='Stoch %D',
            line=dict(color='#FF6D00', width=1.5, dash='dash')
        ),
        row=stoch_row, col=1
    )

    # Stochastic oversold/overbought lines
    fig.add_hline(y=30, line_dash="dot", line_color=COLOR_BULLISH,
                 row=stoch_row, col=1, opacity=0.5)
    fig.add_hline(y=70, line_dash="dot", line_color=COLOR_BEARISH,
                 row=stoch_row, col=1, opacity=0.5)

    # Update layout
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=CHART_HEIGHT,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # Update y-axis titles
    fig.update_yaxes(title_text="Price (IDR)", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Stoch", row=3, col=1)
    else:
        fig.update_yaxes(title_text="Stoch", row=2, col=1)

    return fig


def create_signal_summary_chart(signals: list) -> go.Figure:
    """
    Create summary chart showing signal distribution

    Args:
        signals: List of Signal objects

    Returns:
        Plotly Figure with pie chart
    """
    # Count signal types
    signal_counts = {}
    for signal in signals:
        signal_type = signal.signal_type
        signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1

    labels = list(signal_counts.keys())
    values = list(signal_counts.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=['#00ff68', '#2962FF', '#878b94'])
    )])

    fig.update_layout(
        title='Signal Distribution',
        template=CHART_TEMPLATE,
        height=400
    )

    return fig


def create_performance_chart(journal_df: pd.DataFrame) -> go.Figure:
    """
    Create performance chart from trading journal

    Args:
        journal_df: DataFrame with closed trades

    Returns:
        Plotly Figure with cumulative P/L
    """
    if journal_df.empty:
        return go.Figure()

    # Sort by exit date
    journal_df = journal_df.sort_values('exit_date')

    # Calculate cumulative P/L
    journal_df['cumulative_pnl'] = journal_df['pnl_amount'].cumsum()

    fig = go.Figure()

    # Cumulative P/L line
    fig.add_trace(
        go.Scatter(
            x=journal_df['exit_date'],
            y=journal_df['cumulative_pnl'],
            name='Cumulative P/L',
            line=dict(color=COLOR_BULLISH, width=2),
            fill='tozeroy'
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color=COLOR_NEUTRAL, opacity=0.5)

    fig.update_layout(
        title='Cumulative P/L Performance',
        xaxis_title='Date',
        yaxis_title='P/L (IDR)',
        template=CHART_TEMPLATE,
        height=400,
        hovermode='x'
    )

    return fig


def create_win_rate_chart(stats: dict) -> go.Figure:
    """
    Create win rate visualization

    Args:
        stats: Statistics dictionary from JournalDatabase

    Returns:
        Plotly Figure with win/loss bar chart
    """
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=['Winning', 'Losing'],
            y=[stats['winning_trades'], stats['losing_trades']],
            marker=dict(color=[COLOR_BULLISH, COLOR_BEARISH]),
            text=[stats['winning_trades'], stats['losing_trades']],
            textposition='auto'
        )
    )

    fig.update_layout(
        title=f"Win Rate: {stats['win_rate']:.1f}%",
        yaxis_title='Number of Trades',
        template=CHART_TEMPLATE,
        height=300,
        showlegend=False
    )

    return fig
