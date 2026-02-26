"""
Breakout Performance Tracker
============================
Tracks historical breakout signals and their subsequent performance.
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

DATABASE_PATH = 'breakout_signals.db'


class PerformanceTracker:
    """Tracks breakout signals and measures their performance over time."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing breakout signals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_date TEXT NOT NULL,
                signal_price REAL NOT NULL,
                score INTEGER NOT NULL,
                prior_move_pct REAL,
                distance_to_breakout REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, signal_date)
            )
        ''')
        
        # Table for storing performance measurements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL,
                days_after INTEGER NOT NULL,
                measurement_date TEXT NOT NULL,
                measurement_price REAL NOT NULL,
                return_pct REAL NOT NULL,
                high_since_signal REAL,
                low_since_signal REAL,
                max_gain_pct REAL,
                max_drawdown_pct REAL,
                FOREIGN KEY (signal_id) REFERENCES signals(id),
                UNIQUE(signal_id, days_after)
            )
        ''')
        
        # Table for aggregate statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculated_at TEXT NOT NULL,
                total_signals INTEGER,
                avg_return_1d REAL,
                avg_return_5d REAL,
                avg_return_20d REAL,
                avg_return_30d REAL,
                win_rate_1d REAL,
                win_rate_5d REAL,
                win_rate_20d REAL,
                win_rate_30d REAL,
                best_holding_period INTEGER,
                avg_max_gain REAL,
                avg_max_drawdown REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_signal(self, stock_data: Dict) -> Optional[int]:
        """
        Record a new breakout signal if score >= 80.
        Returns signal_id if recorded, None otherwise.
        """
        if stock_data.get('score', 0) < 80:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        signal_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO signals 
                (symbol, signal_date, signal_price, score, prior_move_pct, distance_to_breakout)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                stock_data['symbol'],
                signal_date,
                stock_data['price'],
                stock_data['score'],
                stock_data.get('prior_move_pct', 0),
                stock_data.get('distance_to_breakout', 0)
            ))
            conn.commit()
            
            if cursor.rowcount > 0:
                signal_id = cursor.lastrowid
                print(f"📊 Recorded signal: {stock_data['symbol']} @ ${stock_data['price']} (Score: {stock_data['score']})")
                return signal_id
            return None
            
        except Exception as e:
            print(f"Error recording signal: {e}")
            return None
        finally:
            conn.close()
    
    def update_performance(self, days_list: List[int] = [1, 5, 20, 30]):
        """
        Update performance measurements for all signals that need updating.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all signals that might need performance updates
        cursor.execute('''
            SELECT id, symbol, signal_date, signal_price 
            FROM signals 
            WHERE date(signal_date) <= date('now', '-1 day')
        ''')
        
        signals = cursor.fetchall()
        
        for signal_id, symbol, signal_date, signal_price in signals:
            signal_dt = datetime.strptime(signal_date, '%Y-%m-%d')
            
            for days in days_list:
                # Check if we already have this measurement
                cursor.execute('''
                    SELECT id FROM performance 
                    WHERE signal_id = ? AND days_after = ?
                ''', (signal_id, days))
                
                if cursor.fetchone():
                    continue  # Already measured
                
                # Check if enough time has passed
                measurement_date = signal_dt + timedelta(days=days)
                if measurement_date > datetime.now():
                    continue  # Not enough time has passed
                
                # Get the price data
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(
                        start=signal_dt - timedelta(days=1),
                        end=measurement_date + timedelta(days=1)
                    )
                    
                    if len(hist) < 2:
                        continue
                    
                    # Get price at measurement date (or closest)
                    measurement_price = hist['Close'].iloc[-1]
                    return_pct = ((measurement_price - signal_price) / signal_price) * 100
                    
                    # Calculate high/low since signal
                    high_since = hist['High'].max()
                    low_since = hist['Low'].min()
                    max_gain_pct = ((high_since - signal_price) / signal_price) * 100
                    max_drawdown_pct = ((low_since - signal_price) / signal_price) * 100
                    
                    cursor.execute('''
                        INSERT INTO performance 
                        (signal_id, days_after, measurement_date, measurement_price, 
                         return_pct, high_since_signal, low_since_signal, max_gain_pct, max_drawdown_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        signal_id, days, measurement_date.strftime('%Y-%m-%d'),
                        measurement_price, return_pct, high_since, low_since,
                        max_gain_pct, max_drawdown_pct
                    ))
                    
                    print(f"📈 {symbol} {days}D: {return_pct:+.1f}% (Max gain: {max_gain_pct:+.1f}%)")
                    
                except Exception as e:
                    print(f"Error updating {symbol} performance: {e}")
                    continue
        
        conn.commit()
        conn.close()
    
    def calculate_statistics(self) -> Dict:
        """Calculate aggregate statistics from all tracked signals."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_signals': 0,
            'returns': {},
            'win_rates': {},
            'best_holding_period': None,
            'avg_max_gain': 0,
            'avg_max_drawdown': 0
        }
        
        # Count total signals
        cursor.execute('SELECT COUNT(*) FROM signals')
        stats['total_signals'] = cursor.fetchone()[0]
        
        if stats['total_signals'] == 0:
            conn.close()
            return stats
        
        # Calculate returns and win rates for each period
        for days in [1, 5, 20, 30]:
            cursor.execute('''
                SELECT AVG(return_pct), 
                       AVG(CASE WHEN return_pct > 0 THEN 1.0 ELSE 0.0 END) * 100,
                       AVG(max_gain_pct),
                       AVG(max_drawdown_pct),
                       COUNT(*)
                FROM performance 
                WHERE days_after = ?
            ''', (days,))
            
            row = cursor.fetchone()
            if row and row[4] > 0:
                stats['returns'][days] = {
                    'avg_return': round(row[0] or 0, 2),
                    'win_rate': round(row[1] or 0, 1),
                    'avg_max_gain': round(row[2] or 0, 2),
                    'avg_max_drawdown': round(row[3] or 0, 2),
                    'sample_size': row[4]
                }
        
        # Determine best holding period
        if stats['returns']:
            best_period = max(stats['returns'].items(), key=lambda x: x[1]['avg_return'])
            stats['best_holding_period'] = best_period[0]
        
        # Save to statistics table
        cursor.execute('''
            INSERT INTO statistics 
            (calculated_at, total_signals, avg_return_1d, avg_return_5d, 
             avg_return_20d, avg_return_30d, win_rate_1d, win_rate_5d,
             win_rate_20d, win_rate_30d, best_holding_period)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            stats['total_signals'],
            stats['returns'].get(1, {}).get('avg_return'),
            stats['returns'].get(5, {}).get('avg_return'),
            stats['returns'].get(20, {}).get('avg_return'),
            stats['returns'].get(30, {}).get('avg_return'),
            stats['returns'].get(1, {}).get('win_rate'),
            stats['returns'].get(5, {}).get('win_rate'),
            stats['returns'].get(20, {}).get('win_rate'),
            stats['returns'].get(30, {}).get('win_rate'),
            stats['best_holding_period']
        ))
        
        conn.commit()
        conn.close()
        
        return stats
    
    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """Get recent signals with their performance data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, s.symbol, s.signal_date, s.signal_price, s.score,
                   s.prior_move_pct, s.distance_to_breakout
            FROM signals s
            ORDER BY s.signal_date DESC
            LIMIT ?
        ''', (limit,))
        
        signals = []
        for row in cursor.fetchall():
            signal = {
                'id': row[0],
                'symbol': row[1],
                'signal_date': row[2],
                'signal_price': row[3],
                'score': row[4],
                'prior_move_pct': row[5],
                'distance_to_breakout': row[6],
                'performance': {}
            }
            
            # Get performance data
            cursor.execute('''
                SELECT days_after, return_pct, max_gain_pct, max_drawdown_pct
                FROM performance
                WHERE signal_id = ?
            ''', (row[0],))
            
            for perf_row in cursor.fetchall():
                signal['performance'][perf_row[0]] = {
                    'return_pct': round(perf_row[1], 2),
                    'max_gain_pct': round(perf_row[2], 2),
                    'max_drawdown_pct': round(perf_row[3], 2)
                }
            
            signals.append(signal)
        
        conn.close()
        return signals
    
    def get_statistics_summary(self) -> Dict:
        """Get the latest statistics summary."""
        stats = self.calculate_statistics()
        
        # Get some recent winners/losers for context
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Best performers (5-day return)
        cursor.execute('''
            SELECT s.symbol, s.signal_date, p.return_pct
            FROM signals s
            JOIN performance p ON s.id = p.signal_id
            WHERE p.days_after = 5
            ORDER BY p.return_pct DESC
            LIMIT 5
        ''')
        stats['top_winners'] = [
            {'symbol': row[0], 'date': row[1], 'return': round(row[2], 1)}
            for row in cursor.fetchall()
        ]
        
        # Worst performers
        cursor.execute('''
            SELECT s.symbol, s.signal_date, p.return_pct
            FROM signals s
            JOIN performance p ON s.id = p.signal_id
            WHERE p.days_after = 5
            ORDER BY p.return_pct ASC
            LIMIT 5
        ''')
        stats['top_losers'] = [
            {'symbol': row[0], 'date': row[1], 'return': round(row[2], 1)}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return stats


# Initialize global tracker
tracker = PerformanceTracker()
