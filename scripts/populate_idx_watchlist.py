"""
Populate Watchlist with All IDX Stocks
Loads all Indonesian stock tickers from tickers.csv and populates the watchlist
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.db_manager import db_manager


def load_tickers_from_csv(csv_path: Path) -> list:
    """Load tickers from CSV file"""
    tickers = []

    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found!")
        return []

    with open(csv_path, 'r') as f:
        for line in f:
            ticker = line.strip().upper()
            # Skip empty lines and headers
            if ticker and ticker not in ['TICKER', 'TICKERS', 'SYMBOL', 'SYMBOLS']:
                # Validate ticker (alphanumeric, max 10 chars)
                if ticker.isalnum() and len(ticker) <= 10:
                    tickers.append(ticker)

    return tickers


def main():
    """Populate watchlist with all IDX stocks"""
    print("="*60)
    print("IDX Watchlist Auto-Population Script")
    print("="*60)
    print()

    # Find CSV file
    project_root = Path(__file__).parent.parent
    csv_paths = [
        project_root / 'data' / 'tickers.csv.backup',
        project_root / 'data' / 'tickers.csv',
        project_root / 'tickers.csv',
    ]

    csv_file = None
    for path in csv_paths:
        if path.exists():
            csv_file = path
            break

    if not csv_file:
        print("ERROR: No ticker CSV file found!")
        print("Searched for:")
        for path in csv_paths:
            print(f"  - {path}")
        print("\nPlease ensure tickers.csv or tickers.csv.backup exists.")
        sys.exit(1)

    print(f"Found CSV: {csv_file}")

    # Load tickers from CSV
    print("Loading tickers from CSV...")
    tickers = load_tickers_from_csv(csv_file)

    if not tickers:
        print("ERROR: No valid tickers found in CSV!")
        sys.exit(1)

    print(f"Loaded {len(tickers)} tickers from CSV")

    # Show sample
    print(f"\nSample tickers (first 10):")
    for ticker in tickers[:10]:
        print(f"  - {ticker}")
    if len(tickers) > 10:
        print(f"  ... and {len(tickers) - 10} more")

    # Confirm
    print(f"\n{'='*60}")
    print(f"Ready to populate watchlist with {len(tickers)} tickers")
    print(f"This will REPLACE the current watchlist!")
    print(f"{'='*60}")

    # Clear existing watchlist
    print("\nClearing existing watchlist...")

    try:
        if db_manager.db_type == 'postgresql':
            db_manager.execute_query("TRUNCATE TABLE watchlist RESTART IDENTITY CASCADE")
        else:
            db_manager.execute_query("DELETE FROM watchlist")

        # Verify empty
        result = db_manager.execute_query("SELECT COUNT(*) FROM watchlist", fetch='one')
        count = result[0] if isinstance(result, tuple) else list(result.values())[0]

        if count > 0:
            print(f"WARNING: Table still has {count} rows after clear!")
            print("Attempting DELETE with WHERE clause...")
            db_manager.execute_query("DELETE FROM watchlist WHERE 1=1")

        print("Watchlist cleared!")

    except Exception as e:
        print(f"ERROR clearing watchlist: {e}")
        sys.exit(1)

    # Insert all tickers
    print(f"\nInserting {len(tickers)} tickers...")
    print("This may take a few minutes...\n")

    inserted = 0
    failed = 0
    batch_size = 50

    for i, ticker in enumerate(tickers, 1):
        try:
            query = "INSERT INTO watchlist (ticker) VALUES (?)"
            db_manager.execute_query(query, (ticker,))
            inserted += 1

            # Progress update every batch
            if i % batch_size == 0:
                progress = (i / len(tickers)) * 100
                print(f"Progress: {i}/{len(tickers)} ({progress:.1f}%) - {ticker}")

        except Exception as e:
            # Skip duplicates silently
            if "unique" not in str(e).lower() and "duplicate" not in str(e).lower():
                print(f"Error inserting {ticker}: {e}")
            failed += 1

    # Final verification
    print("\nVerifying final count...")
    result = db_manager.execute_query("SELECT COUNT(*) FROM watchlist", fetch='one')
    final_count = result[0] if isinstance(result, tuple) else list(result.values())[0]

    # Summary
    print(f"\n{'='*60}")
    print("=== Watchlist Population Complete ===")
    print(f"{'='*60}")
    print(f"CSV file:        {csv_file.name}")
    print(f"Tickers loaded:  {len(tickers)}")
    print(f"Successfully inserted: {inserted}")
    print(f"Failed/Skipped:  {failed}")
    print(f"Final count:     {final_count}")
    print(f"Database type:   {db_manager.db_type}")
    print(f"Completed at:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    if final_count == len(tickers):
        print("\n✅ SUCCESS! Watchlist populated with all IDX tickers!")
        print(f"\nNext steps:")
        print(f"1. Run market data update: python scripts/update_market_data.py")
        print(f"2. Or wait for daily auto-update at 18:00 WIB")
        print(f"3. Estimated update time: ~{int(final_count * 1.5 / 60)} minutes")
        return 0
    else:
        print(f"\n⚠️ WARNING: Expected {len(tickers)} but got {final_count}")
        print("Some tickers may have been skipped due to duplicates or errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
