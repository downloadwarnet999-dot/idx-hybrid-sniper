"""
Daily Market Data Update Script
Runs via GitHub Actions to update market data automatically

Optimized for large watchlists (500+ tickers) with:
- Rate limiting (delays between requests)
- Retry logic for failed tickers
- Progress tracking and time estimation
- Graceful error handling
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

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

# Configuration
DELAY_BETWEEN_REQUESTS = 1.0  # seconds (avoid rate limiting)
MAX_RETRIES = 3  # retry failed tickers
BATCH_SIZE = 50  # show progress every N tickers


def update_with_retry(ticker: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, str]:
    """
    Update ticker with retry logic

    Args:
        ticker: Stock ticker to update
        max_retries: Maximum retry attempts

    Returns:
        Tuple of (success, message)
    """
    for attempt in range(max_retries):
        try:
            success, message = data_engine.update_ticker_data(ticker)

            if success:
                return True, message

            # Failed, retry after longer delay
            if attempt < max_retries - 1:
                time.sleep(2.0)  # Wait 2 seconds before retry

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2.0)
            else:
                return False, f"Error after {max_retries} attempts: {str(e)}"

    return False, "Failed after all retries"


def format_time(seconds: float) -> str:
    """Format seconds into readable time string"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"


def main():
    """Update all tickers in watchlist"""
    start_time = time.time()
    print(f"=== Market Data Update Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    # Get tickers from watchlist
    tickers = data_engine.get_tickers()
    total_tickers = len(tickers)

    print(f"Found {total_tickers} tickers in watchlist")

    if not tickers:
        print("No tickers in watchlist!")
        print("Add tickers via web app or import CSV first.")
        return

    # Estimate time
    estimated_time = total_tickers * (DELAY_BETWEEN_REQUESTS + 0.5)  # 0.5s avg fetch time
    print(f"Estimated time: {format_time(estimated_time)}")
    print(f"Rate limiting: {DELAY_BETWEEN_REQUESTS}s delay between requests")
    print(f"Retry policy: Up to {MAX_RETRIES} attempts per ticker\n")

    # Update each ticker
    success_count = 0
    error_count = 0
    updated_count = 0
    skipped_count = 0
    failed_tickers: List[str] = []

    for i, ticker in enumerate(tickers, 1):
        # Progress indicator
        progress_pct = (i / total_tickers) * 100
        elapsed = time.time() - start_time

        if i > 1:
            avg_time_per_ticker = elapsed / (i - 1)
            remaining_tickers = total_tickers - i
            eta = remaining_tickers * avg_time_per_ticker
            eta_str = format_time(eta)
        else:
            eta_str = "calculating..."

        print(f"[{i}/{total_tickers}] ({progress_pct:.1f}%) {ticker}...", end=" ", flush=True)

        try:
            # Update with retry
            success, message = update_with_retry(ticker)

            if success:
                # Check if actually updated or just up-to-date
                if "Added" in message or "Saved" in message:
                    print(f"OK - {message}")
                    updated_count += 1
                else:
                    print(f"SKIP - {message}")
                    skipped_count += 1
                success_count += 1
            else:
                print(f"FAIL - {message}")
                error_count += 1
                failed_tickers.append(ticker)

        except Exception as e:
            print(f"ERROR - {str(e)}")
            error_count += 1
            failed_tickers.append(ticker)

        # Rate limiting delay (except for last ticker)
        if i < total_tickers:
            time.sleep(DELAY_BETWEEN_REQUESTS)

        # Batch progress update
        if i % BATCH_SIZE == 0:
            print(f"\n--- Progress: {i}/{total_tickers} | Success: {success_count} | Failed: {error_count} | ETA: {eta_str} ---\n")

    # Final summary
    elapsed_total = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"=== Update Complete ===")
    print(f"{'='*60}")
    print(f"Total tickers:   {total_tickers}")
    print(f"Success:         {success_count} ({success_count/total_tickers*100:.1f}%)")
    print(f"  - Updated:     {updated_count}")
    print(f"  - Skipped:     {skipped_count} (already up-to-date)")
    print(f"Failed:          {error_count} ({error_count/total_tickers*100:.1f}%)")
    print(f"Total time:      {format_time(elapsed_total)}")
    print(f"Avg per ticker:  {elapsed_total/total_tickers:.2f}s")
    print(f"Completed at:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Show failed tickers if any
    if failed_tickers:
        print(f"\nFailed tickers ({len(failed_tickers)}):")
        for ticker in failed_tickers[:20]:  # Show first 20
            print(f"  - {ticker}")
        if len(failed_tickers) > 20:
            print(f"  ... and {len(failed_tickers) - 20} more")

    print(f"{'='*60}\n")

    # Exit with error code if too many failures
    failure_rate = error_count / total_tickers if total_tickers > 0 else 0

    if failure_rate > 0.5:  # More than 50% failed
        print("CRITICAL: High failure rate (>50%)!")
        sys.exit(1)
    elif failure_rate > 0.2:  # More than 20% failed
        print("WARNING: Elevated failure rate (>20%)")
        sys.exit(1)
    else:
        print("Market data updated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
