"""
Hot Stonks API Server
=====================
Provides REST API endpoints for the stock scanner and performance tracking.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from scanner import BreakoutScanner
from tracker import PerformanceTracker, tracker
import json
import os
from datetime import datetime
import pytz
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Timezone
EASTERN = pytz.timezone('America/New_York')

# Global state
scanner = BreakoutScanner()
scan_results = {'stocks': [], 'scan_time': None, 'is_scanning': False}
scan_lock = threading.Lock()


def get_eastern_time():
    """Get current time in Eastern timezone."""
    return datetime.now(EASTERN).isoformat()


def run_scan_async():
    """Run scan in background thread."""
    global scan_results
    
    with scan_lock:
        scan_results['is_scanning'] = True
    
    try:
        results = scanner.scan_all()
        
        # Record signals for performance tracking
        for stock in results:
            if stock.get('score', 0) >= 80:
                tracker.record_signal(stock)
        
        with scan_lock:
            scan_results['stocks'] = results
            scan_results['scan_time'] = get_eastern_time()
            scan_results['is_scanning'] = False
            
            # Save to file
            with open('scan_results.json', 'w') as f:
                json.dump(scan_results, f, indent=2)
        
        # Update performance tracking in background
        threading.Thread(target=tracker.update_performance).start()
                
    except Exception as e:
        print(f"Scan error: {e}")
        with scan_lock:
            scan_results['is_scanning'] = False


@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger a new scan."""
    global scan_results
    
    with scan_lock:
        if scan_results['is_scanning']:
            return jsonify({'status': 'already_scanning'}), 409
    
    # Start scan in background
    thread = threading.Thread(target=run_scan_async)
    thread.start()
    
    return jsonify({'status': 'scan_started'})


@app.route('/api/results', methods=['GET'])
def get_results():
    """Get current scan results."""
    global scan_results
    
    # Try to load from file if no results in memory
    if not scan_results['stocks'] and os.path.exists('scan_results.json'):
        try:
            with open('scan_results.json', 'r') as f:
                scan_results = json.load(f)
        except:
            pass
    
    # Apply filters from query params
    status_filter = request.args.get('status', 'all')
    min_score = int(request.args.get('min_score', 0))
    sort_by = request.args.get('sort', 'score')
    search = request.args.get('search', '').lower()
    
    stocks = scan_results.get('stocks', [])
    
    # Filter by status
    if status_filter != 'all':
        stocks = [s for s in stocks if s['status'] == status_filter]
    
    # Filter by minimum score
    stocks = [s for s in stocks if s['score'] >= min_score]
    
    # Filter by search term
    if search:
        stocks = [s for s in stocks if 
                  search in s['symbol'].lower() or 
                  search in s.get('name', '').lower()]
    
    # Sort
    if sort_by == 'score':
        stocks.sort(key=lambda x: x['score'], reverse=True)
    elif sort_by == 'prior_move':
        stocks.sort(key=lambda x: x['prior_move_pct'], reverse=True)
    elif sort_by == 'distance':
        stocks.sort(key=lambda x: x['distance_to_breakout'])
    
    return jsonify({
        'stocks': stocks,
        'scan_time': scan_results.get('scan_time'),
        'scan_time_est': scan_results.get('scan_time'),  # Already in EST
        'is_scanning': scan_results.get('is_scanning', False),
        'total_universe': len(scanner.get_stock_universe()),
        'summary': {
            'ready': len([s for s in scan_results.get('stocks', []) if s['status'] == 'ready']),
            'forming': len([s for s in scan_results.get('stocks', []) if s['status'] == 'forming']),
            'watching': len([s for s in scan_results.get('stocks', []) if s['status'] == 'watching']),
        }
    })


@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get details for a specific stock."""
    global scan_results
    
    # Find in existing results first
    for stock in scan_results.get('stocks', []):
        if stock['symbol'].upper() == symbol.upper():
            return jsonify(stock)
    
    # If not found, scan it now
    result = scanner.scan_stock(symbol.upper())
    
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Stock not found or does not meet criteria'}), 404


@app.route('/api/scan/custom', methods=['POST'])
def custom_scan():
    """Scan a custom list of symbols."""
    data = request.json
    symbols = data.get('symbols', [])
    
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400
    
    results = []
    for symbol in symbols:
        result = scanner.scan_stock(symbol.upper())
        if result:
            results.append(result)
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'stocks': results,
        'scan_time': get_eastern_time()
    })


@app.route('/api/universe', methods=['GET'])
def get_universe():
    """Get the default stock universe."""
    return jsonify({
        'symbols': scanner.get_stock_universe(),
        'count': len(scanner.get_stock_universe())
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server status."""
    return jsonify({
        'status': 'online',
        'is_scanning': scan_results.get('is_scanning', False),
        'last_scan': scan_results.get('scan_time'),
        'stocks_count': len(scan_results.get('stocks', [])),
        'universe_count': len(scanner.get_stock_universe()),
        'current_time_est': get_eastern_time()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


# === PERFORMANCE TRACKING ENDPOINTS ===

@app.route('/api/performance/stats', methods=['GET'])
def get_performance_stats():
    """Get aggregate performance statistics."""
    try:
        stats = tracker.get_statistics_summary()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/performance/signals', methods=['GET'])
def get_signals():
    """Get recent breakout signals with performance data."""
    try:
        limit = int(request.args.get('limit', 50))
        signals = tracker.get_recent_signals(limit=limit)
        return jsonify({
            'signals': signals,
            'count': len(signals)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/performance/update', methods=['POST'])
def update_performance():
    """Manually trigger performance update."""
    try:
        threading.Thread(target=tracker.update_performance).start()
        return jsonify({'status': 'update_started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# === EDUCATIONAL CONTENT ===

@app.route('/api/learn/patterns', methods=['GET'])
def get_patterns():
    """Get pattern definitions and educational content."""
    patterns = {
        'bull_flag': {
            'name': 'Bull Flag',
            'description': 'A continuation pattern that forms after a strong upward move. The flag portion is a consolidation with lower volume before the next leg up.',
            'criteria': [
                'Strong prior upward move (30%+)',
                'Consolidation with declining volume',
                'Price holds above key moving averages',
                'Breakout occurs with volume surge'
            ],
            'psychology': 'Early buyers take profits while new buyers step in at support. The declining volume shows selling pressure is exhausted.',
            'entry_rules': [
                'Wait for price to break above the flag resistance',
                'Confirm with above-average volume on breakout',
                'Enter on the first pullback after breakout, or on break of opening range high'
            ],
            'stop_loss': 'Below the low of the flag or below the breakout candle',
            'target': 'Measured move equal to the prior upward move (flagpole height)',
            'success_rate': '65-70% when all criteria are met'
        },
        'consolidation_breakout': {
            'name': 'Consolidation Breakout',
            'description': 'A pattern where price trades in a tight range before breaking out. The tighter the range and lower the volume, the more powerful the eventual breakout.',
            'criteria': [
                'Price range tightens over multiple days',
                'Volume decreases during consolidation',
                'Moving averages converge',
                'Price near resistance level'
            ],
            'psychology': 'Supply and demand reach equilibrium. When one side wins, the move is often explosive.',
            'entry_rules': [
                'Enter when price breaks above the consolidation high',
                'Volume should increase significantly on breakout',
                'Use a tight stop below the consolidation range'
            ],
            'stop_loss': 'Below the consolidation low or midpoint',
            'target': 'Previous swing high, or 2-3x the consolidation range height',
            'success_rate': '60-65% for properly formed patterns'
        },
        'sma_support': {
            'name': 'Moving Average Support',
            'description': 'When price pulls back to a rising moving average (like 10 or 20 SMA) and bounces, it often signals continuation of the uptrend.',
            'criteria': [
                'Stock in clear uptrend',
                '10 and 20 SMA both inclining',
                'Price pulls back to touch or near the SMA',
                'Bounce with increased volume'
            ],
            'psychology': 'Institutional buyers use moving averages as reference points to add to positions.',
            'entry_rules': [
                'Buy when price bounces off the moving average',
                'Confirm the MA is still rising',
                'Look for a bullish candle pattern at the MA'
            ],
            'stop_loss': 'Below the moving average that provided support',
            'target': 'Previous high or higher, based on measured move',
            'success_rate': '55-60% in trending markets'
        },
        'volume_dry_up': {
            'name': 'Volume Dry Up',
            'description': 'When volume decreases significantly during a pullback, it indicates sellers are exhausted and the stock is ready to resume its uptrend.',
            'criteria': [
                'Volume drops 40%+ from average during pullback',
                'Price holds key support levels despite low volume',
                'No institutional selling (large red volume bars)',
                'Volatility contracts'
            ],
            'psychology': 'Low volume on pullbacks means holders are not willing to sell at current prices. Supply is limited.',
            'entry_rules': [
                'Wait for volume to spike as price turns up',
                'The first green volume bar after dry up is often the signal',
                'Combine with price breaking minor resistance'
            ],
            'stop_loss': 'Below the pullback low',
            'target': 'Retest of recent highs, then new highs',
            'success_rate': '70%+ when combined with other criteria'
        }
    }
    
    return jsonify({
        'patterns': patterns,
        'count': len(patterns)
    })


@app.route('/api/learn/metrics', methods=['GET'])
def get_metrics():
    """Get definitions for all the metrics displayed."""
    metrics = {
        'score': {
            'name': 'Hot Score',
            'range': '0-100',
            'description': 'Composite score based on how well a stock meets breakout criteria. Higher is better.',
            'interpretation': {
                '80-100': 'HOT - Prime breakout candidate, multiple criteria met',
                '60-79': 'WARMING - Pattern forming, add to watchlist',
                '40-59': 'WATCHING - Some criteria met, needs more development',
                '0-39': 'COLD - Does not currently meet breakout criteria'
            }
        },
        'prior_move_pct': {
            'name': 'Prior Move %',
            'description': 'The percentage gain in the stock before the current consolidation began.',
            'why_it_matters': 'Stocks that have made a strong move (30%+) show institutional interest and momentum.',
            'ideal_range': '30-100%+ for best setups'
        },
        'sma_slope': {
            'name': 'SMA Slope',
            'description': 'The rate of change of the moving average. Positive means uptrending.',
            'why_it_matters': 'Rising SMAs indicate sustained buying pressure and upward momentum.',
            'ideal_range': 'Positive, with 10 SMA > 20 SMA slope'
        },
        'pullback_pct': {
            'name': 'Pullback %',
            'description': 'How far the stock has pulled back from its recent high during consolidation.',
            'why_it_matters': 'Shallow pullbacks (under 20%) indicate strong hands holding and limited selling pressure.',
            'ideal_range': '5-20% for healthy consolidation'
        },
        'volume_decline_pct': {
            'name': 'Volume Decline %',
            'description': 'How much volume has decreased during the consolidation period.',
            'why_it_matters': 'Declining volume shows sellers are exhausted - key signal for imminent breakout.',
            'ideal_range': '40%+ decline from average volume'
        },
        'distance_to_breakout': {
            'name': 'Distance to Breakout',
            'description': 'How far the current price is from the consolidation high (resistance level).',
            'why_it_matters': 'Stocks closer to breakout level need less buying pressure to trigger.',
            'ideal_range': 'Under 5% for imminent breakouts'
        },
        'adr_pct': {
            'name': 'ADR %',
            'description': 'Average Daily Range - the typical daily price movement as a percentage.',
            'why_it_matters': 'Higher ADR means more volatility and potential profit (and risk) per trade.',
            'ideal_range': '5%+ for swing trading'
        },
        'days_consolidating': {
            'name': 'Days Consolidating',
            'description': 'Number of days the stock has been in the current consolidation pattern.',
            'why_it_matters': 'Longer consolidation often leads to more powerful breakouts (coiled spring effect).',
            'ideal_range': '10-30 days for best setups'
        }
    }
    
    return jsonify({
        'metrics': metrics,
        'count': len(metrics)
    })


@app.route('/api/learn/strategy', methods=['GET'])
def get_strategy():
    """Get the complete trading strategy guide."""
    strategy = {
        'overview': {
            'name': 'Breakout Swing Trading Strategy',
            'description': 'A momentum-based strategy that identifies stocks consolidating after a strong move, then entering when they break out to new highs.',
            'timeframe': 'Swing trading (1-20 day holds)',
            'best_market_conditions': 'Works best when 10 SMA is above 20 SMA on major indexes (QQQ, SPY)'
        },
        'setup_criteria': {
            'description': 'What to look for before a trade',
            'checklist': [
                '✓ Prior move of 30%+ in recent weeks',
                '✓ 10 and 20 SMA both inclining (positive slope)',
                '✓ Orderly pullback to or near the moving averages',
                '✓ Volume drying up (40%+ decline) during pullback',
                '✓ Price within 5% of breakout level',
                '✓ ADR of 5%+ for sufficient volatility',
                '✓ Hot Score of 80+ for highest probability'
            ]
        },
        'entry_rules': {
            'description': 'When and how to enter the trade',
            'rules': [
                'Wait for the stock to break above consolidation resistance',
                'Confirm breakout with volume at least 50% above average',
                'Enter on the opening range breakout (1-min or 5-min chart)',
                'Alternative: Enter on first pullback after breakout'
            ],
            'timing': 'Best entries are within the first 30 minutes of market open'
        },
        'position_sizing': {
            'description': 'How much to buy',
            'rule': 'Risk no more than 1% of account per trade',
            'formula': 'Position Size = (Account × 0.01) ÷ (Entry Price - Stop Price)',
            'example': 'If account is $50,000, entry is $100, stop is $95: Position = ($500) ÷ ($5) = 100 shares'
        },
        'stop_loss': {
            'description': 'Where to place your stop',
            'rules': [
                'Initial stop: Below the low of the breakout day',
                'Alternative: Below the 10 SMA if tighter stop needed',
                'Never risk more than 1R (your planned risk amount)'
            ]
        },
        'profit_taking': {
            'description': 'When to sell',
            'rules': [
                'First target: Take 20-30% off at 2-3R profit',
                'Move stop to breakeven after first target',
                'Trail remaining position with 10 SMA',
                'Exit fully when price closes below 10 SMA',
                'Never let a winner turn into a loser'
            ]
        },
        'risk_management': {
            'description': 'Protecting your capital',
            'rules': [
                'Maximum 3-5 open positions at once',
                'Reduce size when market SMAs cross bearish',
                'Take smaller positions in first trades until proven',
                'Never average down on losing positions',
                'Keep a trading journal'
            ]
        }
    }
    
    return jsonify(strategy)


if __name__ == '__main__':
    # Load existing results if available
    if os.path.exists('scan_results.json'):
        try:
            with open('scan_results.json', 'r') as f:
                scan_results = json.load(f)
            print(f"Loaded {len(scan_results.get('stocks', []))} stocks from cache")
        except:
            pass
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') is None
    
    print("=" * 50)
    print("🔥 HOT STONKS API SERVER")
    print("=" * 50)
    print(f"API available at http://localhost:{port}")
    print(f"Current time (EST): {get_eastern_time()}")
    print()
    print("Endpoints:")
    print("  GET  /api/results          - Get scan results")
    print("  POST /api/scan             - Trigger new scan")
    print("  GET  /api/stock/<symbol>   - Get single stock")
    print("  GET  /api/performance/stats - Get performance statistics")
    print("  GET  /api/learn/patterns   - Get pattern definitions")
    print("  GET  /api/learn/metrics    - Get metric definitions")
    print("  GET  /api/learn/strategy   - Get trading strategy guide")
    print()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
