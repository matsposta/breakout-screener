"""
Historical Breakout Backtester
==============================
Scans historical data to find past breakout signals and tracks their performance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

DATABASE_PATH = 'breakout_signals.db'


class HistoricalBacktester:
    """Backtests breakout signals using historical data."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.min_prior_move = 30.0
        self.min_score = 75
        self.lookback_days = 90  # How far back to look for signals
        self.init_database()
    
    def init_database(self):
        """Initialize/update database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop old tables and recreate with better schema
        cursor.execute('DROP TABLE IF EXISTS historical_signals')
        cursor.execute('DROP TABLE IF EXISTS historical_performance')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_date TEXT NOT NULL,
                signal_price REAL NOT NULL,
                score INTEGER NOT NULL,
                prior_move_pct REAL,
                pullback_pct REAL,
                volume_decline_pct REAL,
                distance_to_breakout REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, signal_date)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id INTEGER NOT NULL,
                days_held INTEGER NOT NULL,
                exit_date TEXT NOT NULL,
                exit_price REAL NOT NULL,
                return_pct REAL NOT NULL,
                max_gain_pct REAL,
                max_drawdown_pct REAL,
                FOREIGN KEY (signal_id) REFERENCES historical_signals(id),
                UNIQUE(signal_id, days_held)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_signals_date ON historical_signals(signal_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_signals_symbol ON historical_signals(symbol)
        ''')
        
        conn.commit()
        conn.close()
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        return prices.rolling(window=period).mean()
    
    def calculate_slope(self, series: pd.Series, period: int = 10) -> float:
        if len(series) < period:
            return 0.0
        recent = series.tail(period).dropna()
        if len(recent) < 2:
            return 0.0
        x = np.arange(len(recent))
        slope, _ = np.polyfit(x, recent.values, 1)
        return (slope / recent.mean()) * 100
    
    def calculate_score_at_date(self, df: pd.DataFrame, idx: int) -> Dict:
        """Calculate breakout score for a specific date in the dataframe."""
        if idx < 60:
            return {'score': 0}
        
        # Get data up to this date
        data = df.iloc[:idx+1].copy()
        current_price = data['Close'].iloc[-1]
        
        # Calculate SMAs
        data['SMA10'] = self.calculate_sma(data['Close'], 10)
        data['SMA20'] = self.calculate_sma(data['Close'], 20)
        
        # Find prior move (look back 60 days from this point)
        lookback = min(60, len(data) - 1)
        recent_prices = data['Close'].tail(lookback)
        
        min_idx = recent_prices.idxmin()
        min_price = recent_prices[min_idx]
        prices_after_low = recent_prices[recent_prices.index >= min_idx]
        
        if len(prices_after_low) < 2:
            return {'score': 0}
        
        max_price = prices_after_low.max()
        prior_move_pct = ((max_price - min_price) / min_price) * 100
        
        # Consolidation analysis (last 20 bars)
        consol_data = data.tail(20)
        recent_high = consol_data['High'].max()
        pullback_pct = ((recent_high - current_price) / recent_high) * 100
        
        # Volume decline
        first_half_vol = consol_data['Volume'].head(10).mean()
        second_half_vol = consol_data['Volume'].tail(10).mean()
        volume_decline_pct = ((first_half_vol - second_half_vol) / first_half_vol) * 100 if first_half_vol > 0 else 0
        
        # SMA slopes
        sma10_slope = self.calculate_slope(data['SMA10'], 10)
        sma20_slope = self.calculate_slope(data['SMA20'], 10)
        
        # Distance to breakout
        distance_to_breakout = ((recent_high - current_price) / current_price) * 100
        
        # Price above SMAs
        above_sma10 = current_price > data['SMA10'].iloc[-1] if pd.notna(data['SMA10'].iloc[-1]) else False
        above_sma20 = current_price > data['SMA20'].iloc[-1] if pd.notna(data['SMA20'].iloc[-1]) else False
        
        # Range tightening
        highs = consol_data['High'].values
        lows = consol_data['Low'].values
        first_half_range = highs[:10].max() - lows[:10].min()
        second_half_range = highs[10:].max() - lows[10:].min()
        range_tightening = second_half_range < first_half_range
        
        # Calculate score
        score = 0
        
        # Prior move (max 25)
        if prior_move_pct >= 30:
            score += 15
        if prior_move_pct >= 50:
            score += 5
        if prior_move_pct >= 75:
            score += 5
        
        # SMA slopes (max 20)
        if sma10_slope > 0:
            score += 10
        if sma20_slope > 0:
            score += 5
        if sma10_slope > sma20_slope > 0:
            score += 5
        
        # Pullback (max 15)
        if pullback_pct <= 25:
            score += 8
        if pullback_pct <= 15:
            score += 4
        if pullback_pct <= 10:
            score += 3
        
        # Volume decline (max 15)
        if volume_decline_pct >= 20:
            score += 5
        if volume_decline_pct >= 40:
            score += 5
        if volume_decline_pct >= 60:
            score += 5
        
        # Range tightening (max 10)
        if range_tightening:
            score += 10
        
        # Distance to breakout (max 10)
        if distance_to_breakout <= 5:
            score += 5
        if distance_to_breakout <= 2:
            score += 5
        
        # Above SMAs (max 5)
        if above_sma10:
            score += 3
        if above_sma20:
            score += 2
        
        return {
            'score': min(100, score),
            'price': current_price,
            'prior_move_pct': round(prior_move_pct, 1),
            'pullback_pct': round(pullback_pct, 1),
            'volume_decline_pct': round(volume_decline_pct, 0),
            'distance_to_breakout': round(distance_to_breakout, 1)
        }
    
    def find_historical_signals(self, symbol: str) -> List[Dict]:
        """Find all dates where this stock hit breakout criteria in the past."""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 60)  # Extra days for calculations
            
            df = ticker.history(start=start_date, end=end_date)
            
            if len(df) < 70:
                return []
            
            signals = []
            dates = df.index.tolist()
            
            # Scan each trading day in the lookback period
            for i in range(60, len(df) - 1):  # Start at day 60, leave room for performance calc
                metrics = self.calculate_score_at_date(df, i)
                
                if metrics['score'] >= self.min_score:
                    signal_date = dates[i]
                    
                    # Check if we already have a recent signal (avoid duplicate signals within 5 days)
                    recent_signal = False
                    for s in signals:
                        days_diff = (signal_date - s['signal_date']).days
                        if 0 < days_diff < 5:
                            recent_signal = True
                            break
                    
                    if not recent_signal:
                        signals.append({
                            'symbol': symbol,
                            'signal_date': signal_date,
                            'signal_price': metrics['price'],
                            'score': metrics['score'],
                            'prior_move_pct': metrics['prior_move_pct'],
                            'pullback_pct': metrics['pullback_pct'],
                            'volume_decline_pct': metrics['volume_decline_pct'],
                            'distance_to_breakout': metrics['distance_to_breakout']
                        })
            
            return signals
            
        except Exception as e:
            print(f"Error finding signals for {symbol}: {e}")
            return []
    
    def calculate_performance(self, symbol: str, signal_date: datetime, signal_price: float, df: pd.DataFrame) -> Dict:
        """Calculate performance at various holding periods after signal."""
        performance = {}
        
        try:
            # Filter to dates after signal
            future_data = df[df.index > signal_date]
            
            if len(future_data) == 0:
                return performance
            
            for days in [1, 5, 20, 30]:
                if len(future_data) >= days:
                    exit_idx = min(days - 1, len(future_data) - 1)
                    exit_price = future_data['Close'].iloc[exit_idx]
                    exit_date = future_data.index[exit_idx]
                    
                    return_pct = ((exit_price - signal_price) / signal_price) * 100
                    
                    # Calculate max gain and drawdown during holding period
                    holding_data = future_data.iloc[:exit_idx + 1]
                    max_price = holding_data['High'].max()
                    min_price = holding_data['Low'].min()
                    
                    max_gain_pct = ((max_price - signal_price) / signal_price) * 100
                    max_drawdown_pct = ((min_price - signal_price) / signal_price) * 100
                    
                    performance[days] = {
                        'exit_date': exit_date.strftime('%Y-%m-%d'),
                        'exit_price': round(exit_price, 2),
                        'return_pct': round(return_pct, 2),
                        'max_gain_pct': round(max_gain_pct, 2),
                        'max_drawdown_pct': round(max_drawdown_pct, 2)
                    }
        
        except Exception as e:
            print(f"Error calculating performance for {symbol}: {e}")
        
        return performance
    
    def backtest_stock(self, symbol: str) -> List[Dict]:
        """Run full backtest for a single stock."""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 60)
            
            df = ticker.history(start=start_date, end=end_date)
            
            if len(df) < 70:
                return []
            
            # Find all signals
            signals = self.find_historical_signals(symbol)
            
            # Calculate performance for each signal
            results = []
            for signal in signals:
                perf = self.calculate_performance(
                    symbol,
                    signal['signal_date'],
                    signal['signal_price'],
                    df
                )
                signal['performance'] = perf
                signal['signal_date_str'] = signal['signal_date'].strftime('%Y-%m-%d')
                results.append(signal)
            
            return results
            
        except Exception as e:
            print(f"Error backtesting {symbol}: {e}")
            return []
    
    def save_results(self, results: List[Dict]):
        """Save backtest results to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            try:
                # Insert signal
                cursor.execute('''
                    INSERT OR REPLACE INTO historical_signals 
                    (symbol, signal_date, signal_price, score, prior_move_pct, 
                     pullback_pct, volume_decline_pct, distance_to_breakout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result['symbol'],
                    result['signal_date_str'],
                    result['signal_price'],
                    result['score'],
                    result['prior_move_pct'],
                    result['pullback_pct'],
                    result['volume_decline_pct'],
                    result['distance_to_breakout']
                ))
                
                signal_id = cursor.lastrowid
                
                # Insert performance data
                for days, perf in result.get('performance', {}).items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO historical_performance
                        (signal_id, days_held, exit_date, exit_price, return_pct, 
                         max_gain_pct, max_drawdown_pct)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        signal_id,
                        days,
                        perf['exit_date'],
                        perf['exit_price'],
                        perf['return_pct'],
                        perf['max_gain_pct'],
                        perf['max_drawdown_pct']
                    ))
                
            except Exception as e:
                print(f"Error saving {result['symbol']}: {e}")
                continue
        
        conn.commit()
        conn.close()
    
    def run_backtest(self, symbols: List[str], max_workers: int = 5) -> Dict:
        """Run backtest across all symbols."""
        print(f"Running historical backtest on {len(symbols)} stocks...")
        print(f"Looking back {self.lookback_days} days for signals with score >= {self.min_score}")
        print()
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.backtest_stock, s): s for s in symbols}
            
            for i, future in enumerate(as_completed(futures), 1):
                symbol = futures[future]
                try:
                    results = future.result()
                    if results:
                        all_results.extend(results)
                        print(f"[{i}/{len(symbols)}] {symbol}: Found {len(results)} signals")
                    else:
                        print(f"[{i}/{len(symbols)}] {symbol}: No signals")
                except Exception as e:
                    print(f"[{i}/{len(symbols)}] {symbol}: Error - {e}")
        
        # Save all results
        if all_results:
            self.save_results(all_results)
        
        # Calculate aggregate stats
        stats = self.calculate_aggregate_stats()
        
        return {
            'total_signals': len(all_results),
            'signals': all_results,
            'stats': stats
        }
    
    def calculate_aggregate_stats(self) -> Dict:
        """Calculate aggregate performance statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_signals': 0,
            'returns': {},
            'by_score': {}
        }
        
        # Count total signals
        cursor.execute('SELECT COUNT(*) FROM historical_signals')
        stats['total_signals'] = cursor.fetchone()[0]
        
        if stats['total_signals'] == 0:
            conn.close()
            return stats
        
        # Calculate returns for each holding period
        for days in [1, 5, 20, 30]:
            cursor.execute('''
                SELECT 
                    AVG(return_pct),
                    AVG(CASE WHEN return_pct > 0 THEN 1.0 ELSE 0.0 END) * 100,
                    AVG(max_gain_pct),
                    AVG(max_drawdown_pct),
                    COUNT(*)
                FROM historical_performance
                WHERE days_held = ?
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
        
        # Find best holding period
        if stats['returns']:
            best_period = max(stats['returns'].items(), key=lambda x: x[1]['avg_return'])
            stats['best_holding_period'] = best_period[0]
        
        # Get recent signals with performance
        cursor.execute('''
            SELECT s.symbol, s.signal_date, s.score, s.signal_price,
                   p1.return_pct as ret_1d,
                   p5.return_pct as ret_5d,
                   p20.return_pct as ret_20d,
                   p30.return_pct as ret_30d
            FROM historical_signals s
            LEFT JOIN historical_performance p1 ON s.id = p1.signal_id AND p1.days_held = 1
            LEFT JOIN historical_performance p5 ON s.id = p5.signal_id AND p5.days_held = 5
            LEFT JOIN historical_performance p20 ON s.id = p20.signal_id AND p20.days_held = 20
            LEFT JOIN historical_performance p30 ON s.id = p30.signal_id AND p30.days_held = 30
            ORDER BY s.signal_date DESC
            LIMIT 50
        ''')
        
        stats['recent_signals'] = []
        for row in cursor.fetchall():
            stats['recent_signals'].append({
                'symbol': row[0],
                'date': row[1],
                'score': row[2],
                'price': row[3],
                'returns': {
                    '1d': row[4],
                    '5d': row[5],
                    '20d': row[6],
                    '30d': row[7]
                }
            })
        
        # Top and worst performers (5-day)
        cursor.execute('''
            SELECT s.symbol, s.signal_date, p.return_pct
            FROM historical_signals s
            JOIN historical_performance p ON s.id = p.signal_id
            WHERE p.days_held = 5
            ORDER BY p.return_pct DESC
            LIMIT 10
        ''')
        stats['top_winners'] = [{'symbol': r[0], 'date': r[1], 'return': r[2]} for r in cursor.fetchall()]
        
        cursor.execute('''
            SELECT s.symbol, s.signal_date, p.return_pct
            FROM historical_signals s
            JOIN historical_performance p ON s.id = p.signal_id
            WHERE p.days_held = 5
            ORDER BY p.return_pct ASC
            LIMIT 10
        ''')
        stats['top_losers'] = [{'symbol': r[0], 'date': r[1], 'return': r[2]} for r in cursor.fetchall()]
        
        conn.close()
        return stats
    
    def get_stats(self) -> Dict:
        """Get current aggregate statistics."""
        return self.calculate_aggregate_stats()


# Global backtester instance
backtester = HistoricalBacktester()


def main():
    """Run a full backtest."""
    from scanner import BreakoutScanner
    
    scanner = BreakoutScanner()
    symbols = scanner.get_stock_universe()
    
    # Use a smaller subset for faster testing
    # symbols = symbols[:50]
    
    bt = HistoricalBacktester()
    results = bt.run_backtest(symbols, max_workers=5)
    
    print()
    print("=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    print(f"Total signals found: {results['total_signals']}")
    print()
    
    stats = results['stats']
    if stats['returns']:
        print("PERFORMANCE BY HOLDING PERIOD:")
        print("-" * 40)
        for days, data in stats['returns'].items():
            print(f"  {days:2}D: Avg Return: {data['avg_return']:+6.2f}%  |  Win Rate: {data['win_rate']:5.1f}%  |  n={data['sample_size']}")
        
        if stats.get('best_holding_period'):
            print()
            print(f"🏆 Optimal Holding Period: {stats['best_holding_period']} days")
    
    return results


if __name__ == '__main__':
    main()
