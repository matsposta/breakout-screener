"""
Breakout Screener API Server
============================
Provides REST API endpoints for the stock scanner.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from scanner import BreakoutScanner
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global state
scanner = BreakoutScanner()
scan_results = {'stocks': [], 'scan_time': None, 'is_scanning': False}
scan_lock = threading.Lock()


def run_scan_async():
    """Run scan in background thread."""
    global scan_results
    
    with scan_lock:
        scan_results['is_scanning'] = True
    
    try:
        results = scanner.scan_all()
        
        with scan_lock:
            scan_results['stocks'] = results
            scan_results['scan_time'] = datetime.now().isoformat()
            scan_results['is_scanning'] = False
            
            # Save to file
            with open('scan_results.json', 'w') as f:
                json.dump(scan_results, f, indent=2)
                
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
        'is_scanning': scan_results.get('is_scanning', False),
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
        'scan_time': datetime.now().isoformat()
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
        'stocks_count': len(scan_results.get('stocks', []))
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


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
    
    print("Starting Breakout Screener API Server...")
    print(f"API available at http://localhost:{port}")
    print()
    print("Endpoints:")
    print("  GET  /api/results  - Get scan results")
    print("  POST /api/scan     - Trigger new scan")
    print("  GET  /api/stock/<symbol> - Get single stock")
    print()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
