"""
IDX Hybrid Sniper - Scan Results Cache
Persistent storage for scan results across sessions
"""

import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.strategy import Signal


# Cache file path
CACHE_DIR = Path(__file__).parent.parent / 'data'
CACHE_FILE = CACHE_DIR / 'last_scan.pkl'
CACHE_INFO_FILE = CACHE_DIR / 'last_scan_info.json'


def save_scan_results(signals: List[Signal], scan_time: datetime) -> bool:
    """
    Save scan results to persistent cache

    Args:
        signals: List of Signal objects
        scan_time: Datetime when scan was performed

    Returns:
        bool: True if save successful, False otherwise
    """
    try:
        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Convert signals to dicts for serialization
        signal_dicts = [s.to_dict() for s in signals]

        # Save signals to pickle file
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(signal_dicts, f)

        # Save metadata to JSON (human-readable)
        metadata = {
            'scan_time': scan_time.isoformat(),
            'total_signals': len(signals),
            'smc_setup': len([s for s in signals if s.signal_type == 'SMC_SETUP']),
            'smc_entry': len([s for s in signals if s.signal_type == 'SMC_ENTRY']),
            'momentum': len([s for s in signals if s.signal_type == 'MOMENTUM_ENTRY']),
            'no_signal': len([s for s in signals if s.signal_type == 'NO_SIGNAL'])
        }

        with open(CACHE_INFO_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        return True

    except Exception as e:
        print(f"Error saving scan cache: {e}")
        return False


def load_scan_results() -> Tuple[Optional[List[Signal]], Optional[datetime]]:
    """
    Load last scan results from cache

    Returns:
        Tuple of (signals_list, scan_time) or (None, None) if no cache exists
    """
    try:
        # Check if cache file exists
        if not CACHE_FILE.exists() or not CACHE_INFO_FILE.exists():
            return None, None

        # Load metadata
        with open(CACHE_INFO_FILE, 'r') as f:
            metadata = json.load(f)

        scan_time = datetime.fromisoformat(metadata['scan_time'])

        # Load signals from pickle
        with open(CACHE_FILE, 'rb') as f:
            signal_dicts = pickle.load(f)

        # Convert dicts back to Signal objects
        signals = [Signal.from_dict(d) for d in signal_dicts]

        return signals, scan_time

    except Exception as e:
        print(f"Error loading scan cache: {e}")
        return None, None


def clear_scan_cache() -> bool:
    """
    Delete cached scan results

    Returns:
        bool: True if deletion successful, False otherwise
    """
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()

        if CACHE_INFO_FILE.exists():
            CACHE_INFO_FILE.unlink()

        return True

    except Exception as e:
        print(f"Error clearing scan cache: {e}")
        return False


def get_cache_info() -> Optional[dict]:
    """
    Get metadata about cached scan without loading signals

    Returns:
        dict with cache metadata or None if no cache exists
    """
    try:
        if not CACHE_INFO_FILE.exists():
            return None

        with open(CACHE_INFO_FILE, 'r') as f:
            return json.load(f)

    except Exception as e:
        print(f"Error reading cache info: {e}")
        return None
