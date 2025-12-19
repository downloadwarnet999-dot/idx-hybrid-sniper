"""
IDX Hybrid Sniper - CLI Orchestrator
Command-line interface for automated scanning and notifications
"""

import sys
import io
# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import box

from src.data_engine import data_engine
from src.strategy import strategy
from src.notifier import notifier
from src.journal_mgr import journal_mgr
from src.config_mgr import config_mgr  # Import config manager
from config.settings import SCAN_TIME


console = Console()


def manage_config(key: str = None, value: str = None, reset: bool = False):
    """Manage configuration settings"""
    
    if reset:
        config_mgr.reset_to_defaults()
        console.print("[green]✅ Configuration reset to defaults![/green]")
        return

    if key and value is not None:
        # Update setting
        current_val = config_mgr.get(key)
        if current_val is None:
            console.print(f"[red]❌ Unknown configuration key: {key}[/red]")
            return
            
        # Try to cast value to correct type
        try:
            if isinstance(current_val, bool):
                new_val = value.lower() == 'true'
            elif isinstance(current_val, int):
                new_val = int(value)
            elif isinstance(current_val, float):
                new_val = float(value)
            else:
                new_val = value
                
            config_mgr.set(key, new_val)
            console.print(f"[green]✅ Updated {key} to {new_val}[/green]")
        except ValueError:
            console.print(f"[red]❌ Invalid value format for {key}. Expected {type(current_val).__name__}.[/red]")
    else:
        # List settings
        console.print("\n[bold cyan]⚙️ Current Configuration[/bold cyan]\n")
        table = Table(box=box.ROUNDED)
        table.add_column("Key", style="yellow")
        table.add_column("Value", style="white")
        
        configs = config_mgr.get_all()
        for k, v in configs.items():
            table.add_row(str(k), str(v))
            
        console.print(table)
        console.print("\n[dim]To change a value: python main.py config --key KEY --value VALUE[/dim]")


def print_banner():
    """Print application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           🎯 IDX HYBRID SNIPER v2.0                      ║
    ║                                                           ║
    ║     Buy on Weakness, Sell on Strength,                   ║
    ║          Ride the Monster Trend                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def update_data(full_update: bool = False):
    """
    Update market data for all tickers

    Args:
        full_update: If True, fetch full history. If False, incremental update.
    """
    console.print("\n[yellow]📊 Updating Market Data...[/yellow]")

    tickers = data_engine.get_tickers()

    if not tickers:
        console.print("[red]❌ No tickers in watchlist![/red]")
        return

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Updating...",
            total=len(tickers)
        )

        results = {}
        for ticker in tickers:
            success, message = data_engine.update_ticker_data(ticker, force_full=full_update)
            results[ticker] = (success, message)
            progress.update(task, advance=1)

    # Update IHSG
    console.print("\n[yellow]📈 Updating IHSG Index...[/yellow]")
    data_engine.get_ihsg_data()

    # Display results
    table = Table(title="Update Results", box=box.ROUNDED)
    table.add_column("Ticker", style="cyan")
    table.add_column("Status", style="white")

    for ticker, (success, message) in results.items():
        status_icon = "✅" if success else "❌"
        table.add_row(ticker, f"{status_icon} {message}")

    console.print("\n")
    console.print(table)


def scan_market(notify: bool = True, debug: bool = False, limit: int = None):
    """
    Scan market for trading signals

    Args:
        notify: If True, send Telegram notifications
        debug: If True, show detailed analysis for each ticker
        limit: If set, only scan first N tickers (for testing)
    """
    console.print("\n[yellow]🔍 Scanning Market...[/yellow]")

    tickers = data_engine.get_tickers()

    if not tickers:
        console.print("[red]❌ No tickers in watchlist![/red]")
        return

    # Limit tickers if specified
    if limit:
        tickers = tickers[:limit]
        console.print(f"[yellow]Debug mode: Scanning first {limit} tickers only[/yellow]")

    # Scan
    if not debug:
        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Analyzing...",
                total=len(tickers)
            )

            signals = []
            for ticker in tickers:
                try:
                    stock_df = data_engine.get_ticker_data(ticker)
                    ihsg_df = data_engine.get_ihsg_data()

                    if stock_df is not None and not stock_df.empty:
                        signal = strategy.analyze_ticker(ticker, stock_df, ihsg_df, debug=False)
                        signals.append(signal)

                except Exception as e:
                    console.print(f"[red]Error analyzing {ticker}: {e}[/red]")

                progress.update(task, advance=1)
    else:
        # Debug mode - no progress bar, show details
        signals = []
        for ticker in tickers:
            try:
                stock_df = data_engine.get_ticker_data(ticker)
                ihsg_df = data_engine.get_ihsg_data()

                if stock_df is not None and not stock_df.empty:
                    signal = strategy.analyze_ticker(ticker, stock_df, ihsg_df, debug=True)
                    signals.append(signal)

            except Exception as e:
                console.print(f"[red]Error analyzing {ticker}: {e}[/red]")

    # Filter valid signals (HYBRID MODE)
    entry_signals = [s for s in signals if s.signal_type in ['SMC_SETUP', 'SMC_ENTRY', 'MOMENTUM_ENTRY']]
    smc_setup_signals = [s for s in entry_signals if s.signal_type == 'SMC_SETUP']
    smc_confirmed_signals = [s for s in entry_signals if s.signal_type == 'SMC_ENTRY']
    momentum_signals = [s for s in entry_signals if s.signal_type == 'MOMENTUM_ENTRY']

    # Display results
    console.print(f"\n[green]✅ Scan Complete![/green]")
    console.print(f"Total Scanned: {len(signals)}")
    console.print(f"📢 SMC Setups (Prepare): {len(smc_setup_signals)}")
    console.print(f"✅ SMC Confirmed (Execute): {len(smc_confirmed_signals)}")
    console.print(f"⚡ Momentum Entries: {len(momentum_signals)}")

    # SMC SETUP Signals Table (Prepare limit order)
    if smc_setup_signals:
        console.print("\n[bold yellow]📢 SMC SETUP SIGNALS (Prepare Limit Order)[/bold yellow]")

        table = Table(box=box.ROUNDED)
        table.add_column("Ticker", style="yellow", no_wrap=True)
        table.add_column("Current", justify="right")
        table.add_column("Entry", justify="right", style="cyan")
        table.add_column("SL", justify="right")
        table.add_column("TP1", justify="right")
        table.add_column("Zone", justify="center")
        table.add_column("Vol", justify="center")
        table.add_column("RS", justify="right")
        table.add_column("R:R", justify="right")

        for signal in smc_setup_signals:
            vol_color = "green" if signal.volume_status == 'LOW' else "yellow" if signal.volume_status == 'NORMAL' else "red"
            zone_color = "green" if signal.zone_type == 'SWEET_SPOT' else "yellow"

            table.add_row(
                signal.ticker,
                f"{signal.current_price:,.0f}",
                f"{signal.entry_price:,.0f}",  # FVG mid for limit order
                f"{signal.sl_price:,.0f}",
                f"{signal.tp1_price:,.0f}",
                f"[{zone_color}]{signal.zone_type}[/{zone_color}]",
                f"[{vol_color}]{signal.volume_status}[/{vol_color}]",
                f"{signal.rs_score:+.1f}%",
                f"1:{signal.risk_reward_ratio:.2f}"
            )

        console.print(table)
        console.print("[yellow]📋 ACTION: Pasang BUY LIMIT order di kolom 'Entry', tunggu konfirmasi rejection![/yellow]")

        # Send Telegram notifications
        if notify:
            console.print("\n[yellow]📱 Sending Telegram Notifications...[/yellow]")
            for signal in smc_setup_signals[:5]:  # Limit to top 5
                notifier.send_smc_entry_signal(signal)

    # SMC CONFIRMED Signals Table (Execute now)
    if smc_confirmed_signals:
        console.print("\n[bold green]✅ SMC CONFIRMED SIGNALS (Execute Market Order NOW!)[/bold green]")

        table = Table(box=box.ROUNDED)
        table.add_column("Ticker", style="green", no_wrap=True)
        table.add_column("Price", justify="right", style="bold green")
        table.add_column("SL", justify="right")
        table.add_column("TP1", justify="right")
        table.add_column("Zone", justify="center")
        table.add_column("Rejection", justify="center")
        table.add_column("Vol", justify="center")
        table.add_column("RS", justify="right")
        table.add_column("R:R", justify="right")

        for signal in smc_confirmed_signals:
            vol_color = "green" if signal.volume_status == 'LOW' else "yellow" if signal.volume_status == 'NORMAL' else "red"
            zone_color = "green" if signal.zone_type == 'SWEET_SPOT' else "yellow"
            rej_color = "green" if signal.rejection_quality == 'STRONG' else "yellow"

            table.add_row(
                signal.ticker,
                f"{signal.current_price:,.0f}",  # Current price = entry price
                f"{signal.sl_price:,.0f}",
                f"{signal.tp1_price:,.0f}",
                f"[{zone_color}]{signal.zone_type}[/{zone_color}]",
                f"[{rej_color}]{signal.rejection_quality}[/{rej_color}]",
                f"[{vol_color}]{signal.volume_status}[/{vol_color}]",
                f"{signal.rs_score:+.1f}%",
                f"1:{signal.risk_reward_ratio:.2f}"
            )

        console.print(table)
        console.print("[bold green]🚀 ACTION: BUY MARKET ORDER SEKARANG! Rejection sudah terkonfirmasi![/bold green]")

        # Send Telegram notifications
        if notify:
            for signal in smc_confirmed_signals[:5]:
                notifier.send_smc_entry_signal(signal)

    # Momentum Signals Table
    if momentum_signals:
        console.print("\n[bold magenta]⚡ MOMENTUM ENTRY SIGNALS[/bold magenta]")

        table = Table(box=box.ROUNDED)
        table.add_column("Ticker", style="magenta", no_wrap=True)
        table.add_column("Price", justify="right")
        table.add_column("SL", justify="right")
        table.add_column("TP1", justify="right")
        table.add_column("Stoch", justify="right")
        table.add_column("RS", justify="right")
        table.add_column("R:R", justify="right")

        for signal in momentum_signals:
            table.add_row(
                signal.ticker,
                f"{signal.current_price:,.0f}",
                f"{signal.sl_price:,.0f}",
                f"{signal.tp1_price:,.0f}",
                f"{signal.stoch_value:.1f}",
                f"{signal.rs_score:+.1f}%",
                f"1:{signal.risk_reward_ratio:.2f}"
            )

        console.print(table)

        # Send Telegram notifications
        if notify:
            for signal in momentum_signals[:5]:
                notifier.send_momentum_entry_signal(signal)

    # Send watchlist summary
    if notify:
        notifier.send_watchlist_summary(entry_signals, len(signals))

    if not entry_signals:
        console.print("\n[yellow]😴 No entry signals found. Market in consolidation.[/yellow]")


def show_watchlist():
    """Display current watchlist"""
    tickers = data_engine.get_tickers()

    table = Table(title="📋 Watchlist", box=box.ROUNDED)
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Ticker", style="yellow")

    for i, ticker in enumerate(tickers, 1):
        table.add_row(str(i), ticker)

    console.print("\n")
    console.print(table)
    console.print(f"\n[cyan]Total: {len(tickers)} stocks[/cyan]")


def add_ticker(ticker: str):
    """Add ticker to watchlist"""
    ticker = ticker.upper()

    console.print(f"\n[yellow]Validating {ticker}...[/yellow]")

    if data_engine.validate_ticker(ticker):
        if data_engine.add_ticker(ticker):
            console.print(f"[green]✅ {ticker} added to watchlist![/green]")

            # Fetch initial data
            console.print(f"[yellow]Fetching data for {ticker}...[/yellow]")
            success, message = data_engine.update_ticker_data(ticker, force_full=True)

            if success:
                console.print(f"[green]✅ {message}[/green]")
            else:
                console.print(f"[red]❌ {message}[/red]")
        else:
            console.print(f"[yellow]ℹ️ {ticker} already in watchlist[/yellow]")
    else:
        console.print(f"[red]❌ {ticker} not found on Yahoo Finance[/red]")


def remove_ticker(ticker: str):
    """Remove ticker from watchlist"""
    ticker = ticker.upper()

    if data_engine.remove_ticker(ticker):
        console.print(f"[green]✅ {ticker} removed from watchlist[/green]")
    else:
        console.print(f"[yellow]ℹ️ {ticker} not in watchlist[/yellow]")


def show_journal_summary():
    """Display trading journal summary"""
    stats = journal_mgr.get_statistics()

    console.print("\n[bold cyan]📔 TRADING JOURNAL SUMMARY[/bold cyan]\n")

    table = Table(box=box.ROUNDED, show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow", justify="right")

    table.add_row("Total Trades", str(stats['total_trades']))
    table.add_row("Winning Trades", str(stats['winning_trades']))
    table.add_row("Losing Trades", str(stats['losing_trades']))
    table.add_row("Win Rate", f"{stats['win_rate']:.2f}%")
    table.add_row("Average P/L", f"{stats['avg_pnl_percent']:+.2f}%")
    table.add_row("Total P/L", f"Rp {stats['total_pnl_idr']:,.0f}")
    table.add_row("Best Trade", f"+{stats['best_trade_percent']:.2f}%")
    table.add_row("Worst Trade", f"{stats['worst_trade_percent']:.2f}%")

    console.print(table)


def import_csv(csv_file: str, replace: bool = False):
    """Import tickers from CSV file"""
    console.print(f"\n[yellow]📂 Importing tickers from {csv_file}...[/yellow]")

    count, tickers = data_engine.import_from_csv(csv_file, replace=replace)

    if count > 0:
        console.print(f"[green]✅ Imported {count} tickers![/green]")

        # Show imported tickers
        table = Table(title="Imported Tickers", box=box.ROUNDED)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Ticker", style="yellow")

        for i, ticker in enumerate(tickers[:20], 1):  # Show first 20
            table.add_row(str(i), ticker)

        if len(tickers) > 20:
            table.add_row("...", f"+ {len(tickers) - 20} more")

        console.print("\n")
        console.print(table)

        mode = "Replaced" if replace else "Added to"
        console.print(f"\n[green]{mode} watchlist successfully![/green]")
    else:
        console.print("[red]❌ No tickers imported. Check CSV file format.[/red]")
        console.print("\n[yellow]Expected CSV format:[/yellow]")
        console.print("ticker")
        console.print("BBCA")
        console.print("BBRI")
        console.print("TLKM")


def export_csv(csv_file: str):
    """Export current watchlist to CSV"""
    console.print(f"\n[yellow]💾 Exporting watchlist to {csv_file}...[/yellow]")

    if data_engine.export_to_csv(csv_file):
        tickers = data_engine.get_tickers()
        console.print(f"[green]✅ Exported {len(tickers)} tickers to {csv_file}[/green]")
    else:
        console.print("[red]❌ Export failed. Watchlist may be empty.[/red]")


def show_help():
    """Display comprehensive help menu"""
    console.print("\n[bold cyan]📚 IDX HYBRID SNIPER - COMMAND REFERENCE[/bold cyan]\n")

    help_table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    help_table.add_column("Command", style="cyan", no_wrap=True)
    help_table.add_column("Description", style="white")
    help_table.add_column("Example", style="yellow")

    help_table.add_row(
        "scan",
        "Scan market for entry signals (SMC + Momentum)",
        "python main.py scan"
    )
    help_table.add_row(
        "",
        "  --no-notify: Disable Telegram notifications",
        "python main.py scan --no-notify"
    )
    help_table.add_row(
        "",
        "  --debug: Show detailed filter analysis",
        "python main.py scan --debug --limit 20"
    )
    help_table.add_row(
        "",
        "  --limit N: Only scan first N tickers",
        ""
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "update",
        "Update market data for all tickers",
        "python main.py update"
    )
    help_table.add_row(
        "",
        "  --full: Force full update (all history)",
        "python main.py update --full"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "watchlist",
        "Display current watchlist",
        "python main.py watchlist"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "add",
        "Add ticker to watchlist",
        "python main.py add --ticker BBCA"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "remove",
        "Remove ticker from watchlist",
        "python main.py remove --ticker BBCA"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "import-csv",
        "Import tickers from CSV file",
        "python main.py import-csv --file tickers.csv"
    )
    help_table.add_row(
        "",
        "  --replace: Replace entire watchlist",
        "python main.py import-csv --file tickers.csv --replace"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "export-csv",
        "Export watchlist to CSV file",
        "python main.py export-csv --file backup.csv"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "journal",
        "Display trading journal statistics",
        "python main.py journal"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "help",
        "Show this help menu",
        "python main.py help"
    )

    help_table.add_row("", "", "")

    help_table.add_row(
        "guide",
        "Show quick start guide",
        "python main.py guide"
    )

    console.print(help_table)

    console.print("\n[bold yellow]📖 For detailed documentation:[/bold yellow]")
    console.print("  • Quick Start: [cyan]QUICK_START.md[/cyan]")
    console.print("  • Full Guide: [cyan]USER_GUIDE.md[/cyan]")
    console.print("  • CSV Import: [cyan]CSV_IMPORT_GUIDE.md[/cyan]")
    console.print("  • Ticker Management: [cyan]TICKER_MANAGEMENT.md[/cyan]")

    console.print("\n[bold green]🌐 Web Dashboard:[/bold green]")
    console.print("  [cyan]streamlit run app.py[/cyan]")


def show_guide():
    """Display quick start guide"""
    console.print("\n[bold cyan]🚀 IDX HYBRID SNIPER - QUICK START GUIDE[/bold cyan]\n")

    console.print("[bold yellow]1️⃣  First Time Setup[/bold yellow]")
    console.print("   [cyan]python main.py import-csv --file watchlist_template.csv[/cyan]")
    console.print("   [dim]Import default watchlist (20 blue chip stocks)[/dim]\n")

    console.print("[bold yellow]2️⃣  Update Market Data[/bold yellow]")
    console.print("   [cyan]python main.py update --full[/cyan]")
    console.print("   [dim]Download historical data for all stocks[/dim]\n")

    console.print("[bold yellow]3️⃣  Run Market Scan[/bold yellow]")
    console.print("   [cyan]python main.py scan[/cyan]")
    console.print("   [dim]Scan for SMC and Momentum entry signals[/dim]\n")

    console.print("[bold yellow]4️⃣  Launch Web Dashboard[/bold yellow]")
    console.print("   [cyan]streamlit run app.py[/cyan]")
    console.print("   [dim]Open http://localhost:8501 in browser[/dim]\n")

    console.print("[bold green]📊 Daily Routine:[/bold green]")
    console.print("   1. [cyan]python main.py scan[/cyan] - Morning scan for signals")
    console.print("   2. Review signals in Web Dashboard")
    console.print("   3. Analyze charts for top signals")
    console.print("   4. Execute trades during market hours")
    console.print("   5. Update journal after close\n")

    console.print("[bold green]🎯 Strategy Summary:[/bold green]")
    console.print("   • [yellow]SMC Entry[/yellow]: Buy on low-volume pullback at FVG zones")
    console.print("   • [magenta]Momentum Entry[/magenta]: Buy at HMA60 support bounce")
    console.print("   • [cyan]Risk Management[/cyan]: 2% risk per trade, ATR-based SL/TP")
    console.print("   • [green]Exit Strategy[/green]: 50% at TP1, trail 50% with SuperTrend\n")

    console.print("[bold yellow]📖 Available Commands:[/bold yellow]")
    console.print("   [cyan]python main.py help[/cyan] - Show all commands")
    console.print("   [cyan]python main.py guide[/cyan] - Show this guide")
    console.print("   [cyan]python main.py scan --debug --limit 10[/cyan] - Debug mode\n")

    console.print("[bold cyan]📚 Read Full Documentation:[/bold cyan]")
    console.print("   • [yellow]USER_GUIDE.md[/yellow] - Comprehensive guide (30 min read)")
    console.print("   • [yellow]TICKER_MANAGEMENT.md[/yellow] - Watchlist management")
    console.print("   • [yellow]CSV_IMPORT_GUIDE.md[/yellow] - CSV import details\n")

    console.print("[bold green]💡 Pro Tips:[/bold green]")
    console.print("   ✅ Start with paper trading for 1 week")
    console.print("   ✅ Always use stop loss (no exceptions!)")
    console.print("   ✅ Log every trade in journal")
    console.print("   ✅ Review statistics weekly")
    console.print("   ✅ Don't chase - wait for setup")
    console.print("   ✅ 2% risk per trade maximum\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="IDX Hybrid Sniper - CLI Trading Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'command',
        choices=['scan', 'update', 'watchlist', 'add', 'remove', 'journal', 'import-csv', 'export-csv', 'config', 'help', 'guide'],
        help='Command to execute'
    )

    parser.add_argument(
        '--ticker',
        type=str,
        help='Ticker symbol (for add/remove commands)'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='CSV file path (for import-csv/export-csv commands)'
    )
    
    parser.add_argument(
        '--key',
        type=str,
        help='Configuration key (for config command)'
    )
    
    parser.add_argument(
        '--value',
        type=str,
        help='Configuration value (for config command)'
    )

    parser.add_argument(
        '--replace',
        action='store_true',
        help='Replace existing watchlist (for import-csv command)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset configuration to defaults (for config command)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Force full update (for update command)'
    )

    parser.add_argument(
        '--no-notify',
        action='store_true',
        help='Disable Telegram notifications (for scan command)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show detailed analysis for each ticker (for scan command)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of tickers to scan (for testing)'
    )

    args = parser.parse_args()

    print_banner()

    # Execute command
    if args.command == 'scan':
        if not args.debug:
            update_data(full_update=False)  # Quick update before scan
        scan_market(notify=not args.no_notify, debug=args.debug, limit=args.limit)

    elif args.command == 'update':
        update_data(full_update=args.full)

    elif args.command == 'watchlist':
        show_watchlist()

    elif args.command == 'add':
        if args.ticker:
            add_ticker(args.ticker)
        else:
            console.print("[red]❌ Please specify --ticker[/red]")

    elif args.command == 'remove':
        if args.ticker:
            remove_ticker(args.ticker)
        else:
            console.print("[red]❌ Please specify --ticker[/red]")

    elif args.command == 'journal':
        show_journal_summary()
        
    elif args.command == 'config':
        manage_config(key=args.key, value=args.value, reset=args.reset)

    elif args.command == 'import-csv':
        if args.file:
            import_csv(args.file, replace=args.replace)
        else:
            console.print("[red]❌ Please specify --file path/to/tickers.csv[/red]")

    elif args.command == 'export-csv':
        if args.file:
            export_csv(args.file)
        else:
            console.print("[red]❌ Please specify --file path/to/tickers.csv[/red]")

    elif args.command == 'help':
        show_help()

    elif args.command == 'guide':
        show_guide()

    # Only show "Done" for action commands, not help/guide
    if args.command not in ['help', 'guide']:
        console.print("\n[green]Done! 🎯[/green]\n")


if __name__ == "__main__":
    main()
