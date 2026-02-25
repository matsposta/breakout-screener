#!/usr/bin/env python3
"""
=============================================================================
BREAKOUT STOCK SCREENER - Standalone Version
=============================================================================

A simple, single-file stock screener that identifies bull flag / breakout patterns.

USAGE:
    python breakout_scanner_standalone.py

REQUIREMENTS:
    pip install yfinance pandas numpy

The script will:
1. Scan ~70 momentum stocks for breakout patterns
2. Score each stock 0-100 based on criteria
3. Print a summary of the best setups
4. Save detailed results to scan_results.json

=============================================================================
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import sys

warnings.filterwarnings('ignore')

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def color_print(text, color=Colors.WHITE, bold=False):
    """Print colored text to terminal."""
    prefix = Colors.BOLD if bold else ''
    print(f"{prefix}{color}{text}{Colors.END}")


# =============================================================================
# STOCK UNIVERSE - Customize this list with your preferred stocks
# =============================================================================

STOCK_UNIVERSE = [
    # AI / Tech Growth
    'NVDA', 'PLTR', 'SMCI', 'ARM', 'CRWD', 'NET', 'SNOW', 'DDOG', 'MDB', 'PATH',
    'AI', 'BBAI', 'SOUN', 'UPST', 'AFRM', 'SQ', 'SHOP', 'MELI',
    
    # Crypto / Fintech
    'COIN', 'MSTR', 'HOOD', 'SOFI', 'NU',
    
    # Semiconductors
    'AMD', 'AVGO', 'MRVL', 'QCOM', 'MU', 'LRCX', 'KLAC', 'AMAT', 'ASML', 'TSM',
    
    # EV / Clean Energy
    'TSLA', 'RIVN', 'LCID', 'NIO', 'ENPH', 'FSLR',
    
    # Space / Defense
    'RKLB', 'LUNR', 'ASTS', 'LMT', 'RTX', 'NOC',
    
    # Biotech
    'MRNA', 'BNTX', 'CRSP', 'NTLA',
    
    # Gaming / Entertainment
    'TTWO', 'EA', 'RBLX', 'U', 'DKNG',
    
    # High Momentum
    'CELH', 'DUOL', 'APP', 'TTD', 'ROKU', 'PINS', 'RDDT',
    
    # Quantum Computing
    'IONQ', 'RGTI', 'QUBT',
    
    # Other Growth
    'HIMS', 'GRAB', 'VRT', 'CAVA', 'ONON', 'LULU',
]


# =============================================================================
# SCREENING PARAMETERS - Adjust these to customize the scanner
# =============================================================================

CONFIG = {
    'min_price': 1.0,              # Minimum stock price ($)
    'min_adr_pct': 5.0,            # Minimum Average Daily Range (%)
    'min_dollar_volume': 3_500_000, # Minimum daily dollar volume ($)
    'min_prior_move': 30.0,        # Minimum prior move (%)
    'lookback_days': 120,          # Days of price history to analyze
    'consolidation_lookback': 20,  # Days to analyze consolidation
    'max_workers': 5,              # Parallel threads for scanning
}


# =============================================================================
# SCANNER LOGIC
# =============================================================================

def calculate_sma(prices, period):
    """Calculate Simple Moving Average."""
    return prices.rolling(window=period).mean()


def calculate_slope(series, period=10):
    """Calculate the slope of a series (as percentage of mean)."""
    if len(series) < period:
        return 0.0
    recent = series.tail(period).dropna()
    if len(recent) < 2:
        return 0.0
    x = np.arange(len(recent))
    slope, _ = np.polyfit(x, recent.values, 1)
    return (slope / recent.mean()) * 100


def find_prior_move(prices, lookback=60):
    """Find the largest upward move in the lookback period."""
    if len(prices) < lookback:
        lookback = len(prices)
    
    recent = prices.tail(lookback)
    min_idx = recent.idxmin()
    min_price = recent[min_idx]
    
    after_low = recent[recent.index >= min_idx]
    if len(after_low) < 2:
        return 0.0
    
    max_price = after_low.max()
    return ((max_price - min_price) / min_price) * 100


def analyze_consolidation(df, lookback=20):
    """Analyze consolidation pattern."""
    recent = df.tail(lookback)
    if len(recent) < 10:
        return {'pullback': 0, 'volume_decline': 0, 'tightening': False}
    
    # Pullback from high
    high = recent['High'].max()
    current = recent['Close'].iloc[-1]
    pullback = ((high - current) / high) * 100
    
    # Volume decline
    first_half = recent['Volume'].head(len(recent)//2).mean()
    second_half = recent['Volume'].tail(len(recent)//2).mean()
    vol_decline = ((first_half - second_half) / first_half) * 100 if first_half > 0 else 0
    
    # Range tightening
    highs = recent['High'].values
    lows = recent['Low'].values
    first_range = highs[:len(highs)//2].max() - lows[:len(lows)//2].min()
    second_range = highs[len(highs)//2:].max() - lows[len(lows)//2:].min()
    tightening = second_range < first_range
    
    return {
        'pullback': pullback,
        'volume_decline': vol_decline,
        'tightening': tightening
    }


def calculate_score(metrics):
    """Calculate breakout score (0-100)."""
    score = 0
    
    # Prior move (max 25)
    if metrics['prior_move'] >= 30: score += 15
    if metrics['prior_move'] >= 50: score += 5
    if metrics['prior_move'] >= 75: score += 5
    
    # SMA slopes (max 20)
    if metrics['sma10_slope'] > 0: score += 10
    if metrics['sma20_slope'] > 0: score += 5
    if metrics['sma10_slope'] > metrics['sma20_slope'] > 0: score += 5
    
    # Pullback (max 15)
    if metrics['pullback'] <= 25: score += 8
    if metrics['pullback'] <= 15: score += 4
    if metrics['pullback'] <= 10: score += 3
    
    # Volume decline (max 15)
    if metrics['vol_decline'] >= 20: score += 5
    if metrics['vol_decline'] >= 40: score += 5
    if metrics['vol_decline'] >= 60: score += 5
    
    # Tightening (max 10)
    if metrics['tightening']: score += 10
    
    # Distance to breakout (max 10)
    if metrics['distance'] <= 5: score += 5
    if metrics['distance'] <= 2: score += 5
    
    # Above SMAs (max 5)
    if metrics['above_sma10']: score += 3
    if metrics['above_sma20']: score += 2
    
    return min(100, score)


def scan_stock(symbol):
    """Scan a single stock for breakout setup."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='6mo')
        
        if len(df) < 50:
            return None
        
        price = df['Close'].iloc[-1]
        
        # Basic filters
        if price < CONFIG['min_price']:
            return None
        
        # Calculate SMAs
        df['SMA10'] = calculate_sma(df['Close'], 10)
        df['SMA20'] = calculate_sma(df['Close'], 20)
        
        # ADR check
        daily_range = ((df['High'] - df['Low']) / df['Low']) * 100
        adr = daily_range.tail(14).mean()
        if adr < CONFIG['min_adr_pct']:
            return None
        
        # Dollar volume check
        avg_vol = df['Volume'].tail(20).mean()
        dollar_vol = avg_vol * price
        if dollar_vol < CONFIG['min_dollar_volume']:
            return None
        
        # Metrics
        prior_move = find_prior_move(df['Close'])
        consolidation = analyze_consolidation(df)
        sma10_slope = calculate_slope(df['SMA10'])
        sma20_slope = calculate_slope(df['SMA20'])
        
        # Distance to breakout
        recent_high = df.tail(20)['High'].max()
        distance = ((recent_high - price) / price) * 100
        
        metrics = {
            'prior_move': prior_move,
            'sma10_slope': sma10_slope,
            'sma20_slope': sma20_slope,
            'pullback': consolidation['pullback'],
            'vol_decline': consolidation['volume_decline'],
            'tightening': consolidation['tightening'],
            'distance': distance,
            'above_sma10': price > df['SMA10'].iloc[-1] if pd.notna(df['SMA10'].iloc[-1]) else False,
            'above_sma20': price > df['SMA20'].iloc[-1] if pd.notna(df['SMA20'].iloc[-1]) else False,
        }
        
        score = calculate_score(metrics)
        
        # Get company info
        try:
            info = ticker.info
            name = info.get('shortName', symbol)
            sector = info.get('sector', 'Unknown')
        except:
            name = symbol
            sector = 'Unknown'
        
        status = 'ready' if score >= 75 else 'forming' if score >= 50 else 'watching'
        
        return {
            'symbol': symbol,
            'name': name,
            'sector': sector,
            'price': round(price, 2),
            'score': score,
            'status': status,
            'prior_move_pct': round(prior_move, 1),
            'sma10_slope': round(sma10_slope, 2),
            'sma20_slope': round(sma20_slope, 2),
            'pullback_pct': round(consolidation['pullback'], 1),
            'volume_decline_pct': round(consolidation['volume_decline'], 0),
            'range_tightening': consolidation['tightening'],
            'distance_to_breakout': round(distance, 1),
            'adr_pct': round(adr, 1),
            'avg_volume_millions': round(avg_vol / 1_000_000, 2),
            'dollar_volume_millions': round(dollar_vol / 1_000_000, 1),
        }
        
    except Exception as e:
        return None


def run_scan():
    """Run the full scan on all stocks."""
    print()
    color_print("=" * 70, Colors.CYAN)
    color_print("  BREAKOUT STOCK SCREENER", Colors.CYAN, bold=True)
    color_print("  Bull Flag & Consolidation Pattern Detector", Colors.CYAN)
    color_print("=" * 70, Colors.CYAN)
    print()
    
    symbols = list(set(STOCK_UNIVERSE))
    total = len(symbols)
    results = []
    
    color_print(f"Scanning {total} stocks...\n", Colors.WHITE)
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        futures = {executor.submit(scan_stock, s): s for s in symbols}
        
        for i, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            result = future.result()
            
            if result:
                results.append(result)
                if result['status'] == 'ready':
                    icon, color = '🟢', Colors.GREEN
                elif result['status'] == 'forming':
                    icon, color = '🟡', Colors.YELLOW
                else:
                    icon, color = '⚪', Colors.WHITE
                
                print(f"[{i:3}/{total}] {icon} {symbol:6} Score: {result['score']:3}")
            else:
                print(f"[{i:3}/{total}] ❌ {symbol:6} Filtered out")
    
    elapsed = time.time() - start_time
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Summary
    ready = [r for r in results if r['status'] == 'ready']
    forming = [r for r in results if r['status'] == 'forming']
    watching = [r for r in results if r['status'] == 'watching']
    
    print()
    color_print("=" * 70, Colors.CYAN)
    color_print(f"  SCAN COMPLETE - {len(results)} stocks passed filters in {elapsed:.1f}s", Colors.CYAN, bold=True)
    color_print("=" * 70, Colors.CYAN)
    print()
    
    color_print(f"  🟢 Ready to Break:    {len(ready)}", Colors.GREEN, bold=True)
    color_print(f"  🟡 Pattern Forming:   {len(forming)}", Colors.YELLOW, bold=True)
    color_print(f"  ⚪ On Watchlist:      {len(watching)}", Colors.WHITE)
    print()
    
    # Top picks
    if ready:
        color_print("TOP BREAKOUT CANDIDATES:", Colors.GREEN, bold=True)
        color_print("-" * 70, Colors.GREEN)
        print(f"  {'Symbol':<8} {'Score':>6} {'Prior Move':>12} {'Distance':>10} {'Pullback':>10}")
        print(f"  {'-'*8:<8} {'-'*6:>6} {'-'*12:>12} {'-'*10:>10} {'-'*10:>10}")
        for stock in ready[:10]:
            print(f"  {stock['symbol']:<8} {stock['score']:>6} {stock['prior_move_pct']:>11.1f}% {stock['distance_to_breakout']:>9.1f}% {stock['pullback_pct']:>9.1f}%")
        print()
    
    if forming:
        color_print("PATTERNS FORMING (Watch Closely):", Colors.YELLOW, bold=True)
        color_print("-" * 70, Colors.YELLOW)
        for stock in forming[:5]:
            print(f"  {stock['symbol']:<8} Score: {stock['score']:>3} | Move: {stock['prior_move_pct']:>5.1f}% | Distance: {stock['distance_to_breakout']:>5.1f}%")
        print()
    
    # Save to JSON
    output = {
        'scan_time': datetime.now().isoformat(),
        'total_scanned': total,
        'total_passed': len(results),
        'summary': {
            'ready': len(ready),
            'forming': len(forming),
            'watching': len(watching)
        },
        'stocks': results
    }
    
    with open('scan_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    color_print(f"📁 Full results saved to: scan_results.json", Colors.CYAN)
    print()
    
    return results


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    try:
        results = run_scan()
    except KeyboardInterrupt:
        print("\n\nScan cancelled by user.")
        sys.exit(0)
    except Exception as e:
        color_print(f"\nError: {e}", Colors.RED)
        sys.exit(1)
