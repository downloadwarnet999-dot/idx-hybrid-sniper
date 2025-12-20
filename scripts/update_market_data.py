"""
Daily Market Data Update Script
Runs via GitHub Actions to update market data automatically
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Set database URL from environment
if 'DATABASE_URL' in os.environ:
    # Create temporary secrets for database connection
    secrets_content = f"""
[database]
type = "postgresql"
url = "{os.environ['DATABASE_URL']}"
"""
    secrets_dir = Path(__file__).parent.parent / '.streamlit'
    secrets_dir.mkdir(exist_ok=True)
    with open(secrets_dir / 'secrets.toml', 'w') as f:
        f.write(secrets_content)

from src.data_engine import data_engine

def main():
    """Update all tickers in watchlist"""
    print(f"=== Market Data Update Started at {datetime.now()} ===\n")

    # Get tickers from watchlist
    tickers = data_engine.get_tickers()
    print(f"Found {len(tickers)} tickers in watchlist")

    if not tickers:
        print("⚠️ No tickers in watchlist!")
        print("Add tickers via web app or import CSV first.")
        return

    # Update each ticker
    success_count = 0
    error_count = 0

    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] Updating {ticker}...", end=" ")
            result = data_engine.update_ticker_data(ticker)

            if "successfully" in result or "up to date" in result:
                print("✓")
                success_count += 1
            else:
                print(f"⚠️ {result}")
                error_count += 1

        except Exception as e:
            print(f"✗ Error: {e}")
            error_count += 1

    # Summary
    print(f"\n=== Update Complete ===")
    print(f"✓ Success: {success_count}/{len(tickers)}")
    print(f"✗ Failed: {error_count}/{len(tickers)}")
    print(f"Time: {datetime.now()}")

    # Exit with error code if too many failures
    if error_count > len(tickers) * 0.3:  # More than 30% failed
        print("\n⚠️ Warning: High failure rate!")
        sys.exit(1)

    print("\n✅ Market data updated successfully!")

if __name__ == "__main__":
    main()
