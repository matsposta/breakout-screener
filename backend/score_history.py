"""
Score History Tracker
=====================
Tracks daily breakout scores for all stocks over time.
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


class ScoreHistoryTracker:
    """Tracks historical breakout scores for trend analysis."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.lookback_days = 60  # Track 60 days of score history
        self.init_database()
    
    def init_database(self):
        """Initialize database tables for score history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                score INTEGER NOT NULL,
                price REAL,
                prior_move_pct REAL,
                pullback_pct REAL,
                volume_decline_pct REAL,
                sma10_slope REAL,
                sma20_slope REAL,
                distance_to_breakout REAL,
                UNIQUE(symbol, date)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_score_history_symbol ON score_history(symbol)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_score_history_date ON score_history(date)
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
    
    def calculate_daily_scores(self, symbol: str) -> List[Dict]:
        """Calculate breakout score for each trading day in the lookback period."""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days + 60)
            
            df = ticker.history(start=start_date, end=end_date)
            
            if len(df) < 70:
                return []
            
            # Calculate SMAs for full dataset
            df['SMA10'] = self.calculate_sma(df['Close'], 10)
            df['SMA20'] = self.calculate_sma(df['Close'], 20)
            
            daily_scores = []
            dates = df.index.tolist()
            
            # Calculate score for each day in the lookback period
            for i in range(60, len(df)):
                current_date = dates[i]
                data = df.iloc[:i+1].copy()
                current_price = data['Close'].iloc[-1]
                
                # Find prior move
                lookback = min(60, len(data) - 1)
                recent_prices = data['Close'].tail(lookback)
                min_price = recent_prices.min()
                max_price = recent_prices.max()
                prior_move_pct = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                
                # Consolidation analysis
                consol_data = data.tail(20)
                recent_high = consol_data['High'].max()
                pullback_pct = ((recent_high - current_price) / recent_high) * 100 if recent_high > 0 else 0
                
                # Volume decline
                first_half_vol = consol_data['Volume'].head(10).mean()
                second_half_vol = consol_data['Volume'].tail(10).mean()
                volume_decline_pct = ((first_half_vol - second_half_vol) / first_half_vol) * 100 if first_half_vol > 0 else 0
                
                # SMA slopes
                sma10_slope = self.calculate_slope(data['SMA10'], 10)
                sma20_slope = self.calculate_slope(data['SMA20'], 10)
                
                # Distance to breakout
                distance_to_breakout = ((recent_high - current_price) / current_price) * 100 if current_price > 0 else 0
                
                # Range tightening
                highs = consol_data['High'].values
                lows = consol_data['Low'].values
                first_half_range = highs[:10].max() - lows[:10].min() if len(highs) >= 10 else 0
                second_half_range = highs[10:].max() - lows[10:].min() if len(highs) >= 20 else 0
                range_tightening = second_half_range < first_half_range
                
                # Above SMAs
                above_sma10 = current_price > data['SMA10'].iloc[-1] if pd.notna(data['SMA10'].iloc[-1]) else False
                above_sma20 = current_price > data['SMA20'].iloc[-1] if pd.notna(data['SMA20'].iloc[-1]) else False
                
                # Calculate score
                score = 0
                if prior_move_pct >= 30: score += 15
                if prior_move_pct >= 50: score += 5
                if prior_move_pct >= 75: score += 5
                if sma10_slope > 0: score += 10
                if sma20_slope > 0: score += 5
                if sma10_slope > sma20_slope > 0: score += 5
                if pullback_pct <= 25: score += 8
                if pullback_pct <= 15: score += 4
                if pullback_pct <= 10: score += 3
                if volume_decline_pct >= 20: score += 5
                if volume_decline_pct >= 40: score += 5
                if volume_decline_pct >= 60: score += 5
                if range_tightening: score += 10
                if distance_to_breakout <= 5: score += 5
                if distance_to_breakout <= 2: score += 5
                if above_sma10: score += 3
                if above_sma20: score += 2
                
                score = min(100, score)
                
                daily_scores.append({
                    'symbol': symbol,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'score': score,
                    'price': round(current_price, 2),
                    'prior_move_pct': round(prior_move_pct, 1),
                    'pullback_pct': round(pullback_pct, 1),
                    'volume_decline_pct': round(volume_decline_pct, 0),
                    'sma10_slope': round(sma10_slope, 2),
                    'sma20_slope': round(sma20_slope, 2),
                    'distance_to_breakout': round(distance_to_breakout, 1)
                })
            
            return daily_scores
            
        except Exception as e:
            print(f"Error calculating scores for {symbol}: {e}")
            return []
    
    def save_scores(self, scores: List[Dict]):
        """Save daily scores to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for score in scores:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO score_history 
                    (symbol, date, score, price, prior_move_pct, pullback_pct, 
                     volume_decline_pct, sma10_slope, sma20_slope, distance_to_breakout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    score['symbol'],
                    score['date'],
                    score['score'],
                    score['price'],
                    score['prior_move_pct'],
                    score['pullback_pct'],
                    score['volume_decline_pct'],
                    score['sma10_slope'],
                    score['sma20_slope'],
                    score['distance_to_breakout']
                ))
            except Exception as e:
                print(f"Error saving score for {score['symbol']}: {e}")
        
        conn.commit()
        conn.close()
    
    def build_history(self, symbols: List[str], max_workers: int = 5):
        """Build score history for all symbols."""
        print(f"Building score history for {len(symbols)} stocks...")
        print(f"Tracking {self.lookback_days} days of history")
        print()
        
        all_scores = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.calculate_daily_scores, s): s for s in symbols}
            
            for i, future in enumerate(as_completed(futures), 1):
                symbol = futures[future]
                try:
                    scores = future.result()
                    if scores:
                        all_scores.extend(scores)
                        print(f"[{i}/{len(symbols)}] {symbol}: {len(scores)} days tracked")
                    else:
                        print(f"[{i}/{len(symbols)}] {symbol}: No data")
                except Exception as e:
                    print(f"[{i}/{len(symbols)}] {symbol}: Error - {e}")
        
        if all_scores:
            self.save_scores(all_scores)
        
        return len(all_scores)
    
    def get_stock_history(self, symbol: str, days: int = 60) -> List[Dict]:
        """Get score history for a single stock."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, score, price, prior_move_pct, pullback_pct, 
                   volume_decline_pct, sma10_slope, sma20_slope, distance_to_breakout
            FROM score_history
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (symbol.upper(), days))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'date': row[0],
                'score': row[1],
                'price': row[2],
                'prior_move_pct': row[3],
                'pullback_pct': row[4],
                'volume_decline_pct': row[5],
                'sma10_slope': row[6],
                'sma20_slope': row[7],
                'distance_to_breakout': row[8]
            })
        
        conn.close()
        return list(reversed(history))  # Return in chronological order
    
    def get_trending_stocks(self, min_increase: int = 10, days: int = 5) -> List[Dict]:
        """Find stocks with increasing scores over recent days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            WITH recent_scores AS (
                SELECT symbol, date, score,
                       ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) as rn
                FROM score_history
            ),
            score_changes AS (
                SELECT 
                    a.symbol,
                    a.score as current_score,
                    b.score as past_score,
                    a.score - b.score as score_change
                FROM recent_scores a
                JOIN recent_scores b ON a.symbol = b.symbol
                WHERE a.rn = 1 AND b.rn = ?
            )
            SELECT symbol, current_score, past_score, score_change
            FROM score_changes
            WHERE score_change >= ?
            ORDER BY score_change DESC
            LIMIT 20
        ''', (days, min_increase))
        
        trending = []
        for row in cursor.fetchall():
            trending.append({
                'symbol': row[0],
                'current_score': row[1],
                'past_score': row[2],
                'score_change': row[3]
            })
        
        conn.close()
        return trending
    
    def get_all_latest_scores(self) -> List[Dict]:
        """Get latest score for all stocks with history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            WITH latest AS (
                SELECT symbol, MAX(date) as max_date
                FROM score_history
                GROUP BY symbol
            )
            SELECT s.symbol, s.date, s.score, s.price
            FROM score_history s
            JOIN latest l ON s.symbol = l.symbol AND s.date = l.max_date
            ORDER BY s.score DESC
        ''')
        
        scores = []
        for row in cursor.fetchall():
            scores.append({
                'symbol': row[0],
                'date': row[1],
                'score': row[2],
                'price': row[3]
            })
        
        conn.close()
        return scores
    
    def get_chart_data(self, symbols: List[str] = None, days: int = 30) -> Dict:
        """Get chart data for multiple stocks."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbols:
            placeholders = ','.join(['?' for _ in symbols])
            cursor.execute(f'''
                SELECT symbol, date, score, price
                FROM score_history
                WHERE symbol IN ({placeholders})
                  AND date >= date('now', '-{days} days')
                ORDER BY symbol, date
            ''', [s.upper() for s in symbols])
        else:
            # Get top 10 stocks by latest score
            cursor.execute(f'''
                WITH latest AS (
                    SELECT symbol, MAX(date) as max_date
                    FROM score_history
                    GROUP BY symbol
                ),
                top_stocks AS (
                    SELECT s.symbol
                    FROM score_history s
                    JOIN latest l ON s.symbol = l.symbol AND s.date = l.max_date
                    ORDER BY s.score DESC
                    LIMIT 10
                )
                SELECT s.symbol, s.date, s.score, s.price
                FROM score_history s
                WHERE s.symbol IN (SELECT symbol FROM top_stocks)
                  AND s.date >= date('now', '-{days} days')
                ORDER BY s.symbol, s.date
            ''')
        
        # Organize by symbol
        chart_data = {}
        for row in cursor.fetchall():
            symbol = row[0]
            if symbol not in chart_data:
                chart_data[symbol] = []
            chart_data[symbol].append({
                'date': row[1],
                'score': row[2],
                'price': row[3]
            })
        
        conn.close()
        return chart_data
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for score history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total stocks tracked
        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM score_history')
        total_stocks = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(date), MAX(date) FROM score_history')
        row = cursor.fetchone()
        date_range = {'start': row[0], 'end': row[1]} if row[0] else None
        
        # Stocks currently above 75
        cursor.execute('''
            WITH latest AS (
                SELECT symbol, MAX(date) as max_date
                FROM score_history
                GROUP BY symbol
            )
            SELECT COUNT(*)
            FROM score_history s
            JOIN latest l ON s.symbol = l.symbol AND s.date = l.max_date
            WHERE s.score >= 75
        ''')
        hot_count = cursor.fetchone()[0]
        
        # Average score
        cursor.execute('''
            WITH latest AS (
                SELECT symbol, MAX(date) as max_date
                FROM score_history
                GROUP BY symbol
            )
            SELECT AVG(s.score)
            FROM score_history s
            JOIN latest l ON s.symbol = l.symbol AND s.date = l.max_date
        ''')
        avg_score = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_stocks': total_stocks,
            'date_range': date_range,
            'hot_count': hot_count,
            'average_score': round(avg_score, 1) if avg_score else 0
        }


# Global instance
score_tracker = ScoreHistoryTracker()
