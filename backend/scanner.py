"""
Breakout Stock Scanner
======================
Scans stocks for bull flag / breakout patterns based on swing trading methodology.

Criteria:
1. Prior big move up (30%+) over multiple days/weeks
2. 10/20 SMA inclining (sloping upward)
3. Orderly pullback to 10/20 SMA with tightening range
4. Volume drying up during consolidation
5. Stock price > $1, ADR% > 5%, Avg daily $ volume > $3.5M
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


class BreakoutScanner:
    """Scans stocks for breakout setups based on the bull flag pattern."""
    
    def __init__(self):
        self.min_price = 1.0
        self.min_adr_pct = 5.0
        self.min_dollar_volume = 3_500_000
        self.min_prior_move = 30.0  # Minimum 30% move before consolidation
        self.lookback_days = 120    # Days of history to analyze
        
    def get_stock_universe(self) -> List[str]:
        """
        Returns a comprehensive list of stock symbols to scan.
        Includes S&P 500, Nasdaq 100, Russell 2000 leaders, and momentum names.
        Total: 400+ stocks across all major sectors.
        """
        stocks = [
            # === MEGA CAP TECH ===
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA', 'BRK.B',
            
            # === AI & CLOUD ===
            'PLTR', 'SMCI', 'ARM', 'CRWD', 'NET', 'SNOW', 'DDOG', 'MDB', 'PATH',
            'AI', 'BBAI', 'SOUN', 'UPST', 'AFRM', 'NOW', 'PANW', 'ZS', 'OKTA',
            'FTNT', 'ESTC', 'CFLT', 'GTLB', 'DOCN', 'DT', 'NEWR', 'ESTC',
            'ASAN', 'MNDY', 'FROG', 'SUMO', 'PD', 'BRZE', 'AMPL',
            
            # === SEMICONDUCTORS (EXPANDED) ===
            'AMD', 'AVGO', 'MRVL', 'QCOM', 'MU', 'LRCX', 'KLAC', 'AMAT', 'ASML', 'TSM',
            'INTC', 'TXN', 'ADI', 'NXPI', 'ON', 'MPWR', 'MCHP', 'SWKS', 'QRVO',
            'WOLF', 'CRUS', 'SLAB', 'SITM', 'RMBS', 'ACLS', 'UCTT', 'AEHR', 'FORM',
            'SYNA', 'DIOD', 'POWI', 'AMBA', 'HIMX', 'AOSL', 'ALGM', 'SGH',
            
            # === CRYPTO & FINTECH (EXPANDED) ===
            'COIN', 'MSTR', 'HOOD', 'SOFI', 'NU', 'SQ', 'PYPL', 'V', 'MA', 'AXP',
            'GS', 'MS', 'JPM', 'BAC', 'C', 'WFC', 'SCHW', 'LPLA', 'IBKR',
            'UPST', 'LC', 'OPEN', 'TREE', 'NAVI', 'SLM', 'ALLY', 'COF', 'DFS',
            'MARA', 'RIOT', 'CLSK', 'CIFR', 'BITF', 'HUT', 'BTBT',
            
            # === E-COMMERCE & CONSUMER (EXPANDED) ===
            'SHOP', 'MELI', 'SE', 'BABA', 'JD', 'PDD', 'CPNG', 'ETSY', 'EBAY', 'W',
            'TGT', 'WMT', 'COST', 'HD', 'LOW', 'BBY', 'DG', 'DLTR', 'FIVE', 'OLLI',
            'LULU', 'NKE', 'DECK', 'ONON', 'BIRK', 'CROX', 'SKX', 'UAA', 'VFC',
            'GPS', 'ANF', 'AEO', 'URBN', 'EXPR', 'VSCO', 'RL', 'PVH', 'TPR',
            'ELF', 'ULTA', 'COTY', 'EL', 'SKIN', 'HIMS', 'PRCH', 'CVNA', 'CARS',
            
            # === FOOD & BEVERAGE (EXPANDED) ===
            'CELH', 'MNST', 'KO', 'PEP', 'SBUX', 'MCD', 'CMG', 'CAVA', 'DPZ', 'YUM',
            'WING', 'SHAK', 'BROS', 'DNUT', 'WEN', 'QSR', 'DIN', 'TXRH', 'CAKE',
            'PLAY', 'EAT', 'DRI', 'BLMN', 'BJRI', 'JACK', 'ARCO', 'LOCO',
            'FIZZ', 'SAM', 'BUD', 'TAP', 'STZ', 'DEO', 'BF.B',
            
            # === ELECTRIC VEHICLES & CLEAN ENERGY (EXPANDED) ===
            'TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSR', 'GOEV', 'NKLA',
            'ENPH', 'FSLR', 'RUN', 'SEDG', 'NOVA', 'MAXN', 'ARRY', 'CSIQ', 'JKS',
            'NEE', 'CEG', 'VST', 'PLUG', 'BE', 'BLDP', 'FCEL', 'BLOOM',
            'CHPT', 'EVGO', 'BLNK', 'DCFC', 'AMPX', 'PTRA', 'LEV', 'GTLB',
            'STEM', 'FLUX', 'OUST', 'LAZR', 'LIDR', 'AEVA', 'INVZ', 'VLDR',
            'ALB', 'LAC', 'LTHM', 'SQM', 'PLL', 'ALTM', 'MP', 'UUUU',
            
            # === SPACE & DEFENSE (EXPANDED) ===
            'RKLB', 'LUNR', 'ASTS', 'RDW', 'SPCE', 'MNTS', 'VORB', 'ASTR',
            'LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII', 'TDG', 'HEI',
            'KTOS', 'AVAV', 'MRCY', 'AJRD', 'BWXT', 'LDOS', 'SAIC', 'BAH',
            'PSN', 'TXT', 'ERJ', 'SPR', 'HXL', 'WWD', 'MOG.A', 'CW',
            
            # === BIOTECH & HEALTHCARE (EXPANDED) ===
            'MRNA', 'BNTX', 'CRSP', 'NTLA', 'BEAM', 'EDIT', 'RXRX', 'DNA',
            'LLY', 'NVO', 'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'BMY', 'GILD', 'REGN',
            'VRTX', 'BIIB', 'ALNY', 'EXAS', 'DXCM', 'ISRG', 'VEEV',
            'HIMS', 'DOCS', 'TDOC', 'AMWL', 'TALK', 'ACCD', 'OSH', 'PHR',
            'RGEN', 'TECH', 'BIO', 'A', 'TMO', 'DHR', 'IQV', 'MTD', 'WAT',
            'ZBH', 'SYK', 'MDT', 'BSX', 'ABT', 'EW', 'HOLX', 'ALGN', 'NVST',
            'XENE', 'SAVA', 'IMVT', 'APLS', 'KRYS', 'ARWR', 'IONS', 'SRPT',
            
            # === GAMING & ENTERTAINMENT (EXPANDED) ===
            'TTWO', 'EA', 'RBLX', 'U', 'DKNG', 'PENN', 'CHDN', 'MGM', 'CZR', 'WYNN',
            'NFLX', 'DIS', 'WBD', 'PARA', 'CMCSA', 'LYV', 'SPOT', 'TME',
            'RCL', 'CCL', 'NCLH', 'MAR', 'HLT', 'H', 'ABNB', 'BKNG', 'EXPE',
            'MTCH', 'BMBL', 'GRND', 'SKLZ',
            
            # === SOCIAL & ADVERTISING (EXPANDED) ===
            'SNAP', 'PINS', 'RDDT', 'TTD', 'ROKU', 'MGNI', 'PUBM', 'DSP',
            'APP', 'DUOL', 'PTON', 'CHGG', 'UDMY', 'COUR', 'TWOU', 'LRN',
            'DV', 'IAS', 'CRTO', 'TBLA', 'ZETA', 'SEMR',
            
            # === QUANTUM & EMERGING TECH ===
            'IONQ', 'RGTI', 'QUBT', 'ARQQ', 'QBTS',
            
            # === REAL ESTATE & INFRASTRUCTURE (EXPANDED) ===
            'AMT', 'CCI', 'EQIX', 'DLR', 'SBAC', 'SPG', 'O', 'VICI', 'GLPI',
            'VRT', 'PWR', 'EME', 'FIX', 'APO', 'KKR', 'BX', 'CG', 'ARES',
            'PLD', 'PSA', 'EXR', 'CUBE', 'LSI', 'NSA', 'REXR', 'STAG',
            'ARE', 'BXP', 'SLG', 'VNO', 'CBRE', 'JLL', 'CSGP', 'RKT',
            
            # === INDUSTRIAL & MANUFACTURING (EXPANDED) ===
            'CAT', 'DE', 'GE', 'HON', 'MMM', 'UPS', 'FDX', 'UNP', 'CSX', 'NSC',
            'URI', 'PCAR', 'ODFL', 'XPO', 'JBHT', 'CHRW', 'EXPD', 'SAIA', 'ARCB',
            'WAB', 'TTC', 'GNRC', 'SWK', 'IR', 'PNR', 'XYL', 'IEX', 'FSLR',
            'PLUG', 'SEDG', 'ENPH', 'RUN', 'NOVA', 'MAXN', 'SHLS', 'ARRY',
            
            # === SOFTWARE & SAAS (EXPANDED) ===
            'CRM', 'ADBE', 'ORCL', 'SAP', 'WDAY', 'TEAM', 'ZM', 'DOCU', 'BILL',
            'HUBS', 'TWLO', 'ZI', 'MNDY', 'FROG', 'ASAN', 'SUMO', 'S',
            'GTLB', 'ESTC', 'MDB', 'CFLT', 'NEWR', 'DDOG', 'SPLK', 'COUP',
            'APPF', 'APPN', 'BASE', 'BAND', 'LPSN', 'NICE', 'MANH', 'TYL',
            'CDNS', 'SNPS', 'ANSS', 'PTC', 'AZPN', 'ALTR', 'QTWO', 'NCNO',
            
            # === CYBERSECURITY (EXPANDED) ===
            'CRWD', 'FTNT', 'PANW', 'ZS', 'OKTA', 'QLYS', 'TENB', 'RPD', 'CYBR',
            'S', 'VRNS', 'SAIL', 'BB', 'RDWR', 'OSPN', 'SCWX', 'NSIT',
            
            # === RECENT IPOS & HIGH GROWTH ===
            'GRAB', 'IONQ', 'JOBY', 'ACHR', 'LILM', 'EVTL', 'VFS', 'SLDP', 'QS',
            'IOT', 'TOST', 'BRDS', 'CART', 'ARM', 'BIRK', 'ONON', 'CAVA',
            
            # === ADDITIONAL RUSSELL 2000 MOMENTUM ===
            'AXON', 'TMDX', 'INTA', 'KTOS', 'IRDM', 'GRMN', 'TER', 'ENTG',
            'MKTX', 'PAYC', 'PCTY', 'WK', 'ZEN', 'AMPL', 'PD',
            'TGTX', 'EXEL', 'INCY', 'PCVX', 'VKTX', 'DAWN', 'SRRK',
            'SMMT', 'CLOV', 'CANO', 'ALHC', 'OSCR', 'CLVR', 'NTRA',
            'RELY', 'DLO', 'PAYO', 'FLYW', 'RELY', 'MQ', 'AFRM',
            
            # === ENERGY & COMMODITIES ===
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY', 'DVN', 'HAL', 'MPC',
            'VLO', 'PSX', 'PBF', 'DINO', 'HES', 'FANG', 'PXD', 'APA',
            'CTRA', 'OVV', 'RRC', 'AR', 'SWN', 'EQT', 'CNX',
            'FCX', 'NEM', 'GOLD', 'AEM', 'WPM', 'FNV', 'RGLD',
            'AA', 'NUE', 'STLD', 'CLF', 'X', 'RS', 'ATI', 'CMC',
            
            # === TELECOM & MEDIA ===
            'T', 'VZ', 'TMUS', 'CHTR', 'FYBR', 'LUMN', 'USM',
            
            # === CANNABIS ===
            'TLRY', 'CGC', 'ACB', 'SNDL', 'OGI', 'HEXO', 'VFF', 'GRWG',
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for s in stocks:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        
        return unique
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()
    
    def calculate_adr(self, high: pd.Series, low: pd.Series, period: int = 14) -> float:
        """Calculate Average Daily Range as percentage."""
        daily_range_pct = ((high - low) / low) * 100
        return daily_range_pct.tail(period).mean()
    
    def calculate_slope(self, series: pd.Series, period: int = 10) -> float:
        """Calculate the slope of a series over the last n periods."""
        if len(series) < period:
            return 0.0
        recent = series.tail(period).dropna()
        if len(recent) < 2:
            return 0.0
        x = np.arange(len(recent))
        slope, _ = np.polyfit(x, recent.values, 1)
        # Normalize by the mean value to get a percentage slope
        return (slope / recent.mean()) * 100
    
    def find_prior_move(self, prices: pd.Series, lookback: int = 60) -> Dict:
        """
        Find the largest upward move in the lookback period.
        Returns the move percentage, start date, and end date.
        """
        if len(prices) < lookback:
            lookback = len(prices)
        
        recent_prices = prices.tail(lookback)
        
        # Find the swing low (minimum) and subsequent high
        min_idx = recent_prices.idxmin()
        min_price = recent_prices[min_idx]
        
        # Look for the high after the low
        prices_after_low = recent_prices[recent_prices.index >= min_idx]
        if len(prices_after_low) < 2:
            return {'move_pct': 0, 'start_date': None, 'end_date': None}
        
        max_idx = prices_after_low.idxmax()
        max_price = prices_after_low[max_idx]
        
        move_pct = ((max_price - min_price) / min_price) * 100
        
        return {
            'move_pct': move_pct,
            'start_date': min_idx,
            'end_date': max_idx,
            'start_price': min_price,
            'end_price': max_price
        }
    
    def analyze_consolidation(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Analyze the consolidation pattern in recent price action.
        Looks for:
        - Tightening range (higher lows, lower highs)
        - Declining volume
        - Price holding above key SMAs
        """
        recent = df.tail(lookback).copy()
        
        if len(recent) < 10:
            return {
                'pullback_pct': 0,
                'volume_decline_pct': 0,
                'range_tightening': False,
                'days_consolidating': 0,
                'above_sma10': False,
                'above_sma20': False
            }
        
        # Calculate pullback from recent high
        recent_high = recent['High'].max()
        current_price = recent['Close'].iloc[-1]
        pullback_pct = ((recent_high - current_price) / recent_high) * 100
        
        # Volume analysis - compare recent volume to volume during the move up
        first_half_vol = recent['Volume'].head(len(recent)//2).mean()
        second_half_vol = recent['Volume'].tail(len(recent)//2).mean()
        
        if first_half_vol > 0:
            volume_decline_pct = ((first_half_vol - second_half_vol) / first_half_vol) * 100
        else:
            volume_decline_pct = 0
        
        # Check for tightening range (lower highs and higher lows)
        highs = recent['High'].values
        lows = recent['Low'].values
        
        # Simple check: is the range narrowing?
        first_half_range = highs[:len(highs)//2].max() - lows[:len(lows)//2].min()
        second_half_range = highs[len(highs)//2:].max() - lows[len(lows)//2:].min()
        range_tightening = second_half_range < first_half_range
        
        # Check if price is above SMAs
        above_sma10 = current_price > recent['SMA10'].iloc[-1] if 'SMA10' in recent else False
        above_sma20 = current_price > recent['SMA20'].iloc[-1] if 'SMA20' in recent else False
        
        return {
            'pullback_pct': pullback_pct,
            'volume_decline_pct': volume_decline_pct,
            'range_tightening': bool(range_tightening),
            'days_consolidating': lookback,
            'above_sma10': bool(above_sma10),
            'above_sma20': bool(above_sma20)
        }
    
    def calculate_distance_to_breakout(self, df: pd.DataFrame, lookback: int = 20) -> float:
        """
        Calculate how close the stock is to breaking out.
        Returns percentage distance to the consolidation high.
        """
        recent = df.tail(lookback)
        consolidation_high = recent['High'].max()
        current_price = df['Close'].iloc[-1]
        
        distance_pct = ((consolidation_high - current_price) / current_price) * 100
        return distance_pct
    
    def calculate_breakout_score(self, metrics: Dict) -> int:
        """
        Calculate a 0-100 score based on how well the stock meets breakout criteria.
        """
        score = 0
        
        # Prior move (max 25 points)
        prior_move = metrics.get('prior_move_pct', 0)
        if prior_move >= 30:
            score += 15
        if prior_move >= 50:
            score += 5
        if prior_move >= 75:
            score += 5
        
        # SMA slopes (max 20 points)
        sma10_slope = metrics.get('sma10_slope', 0)
        sma20_slope = metrics.get('sma20_slope', 0)
        if sma10_slope > 0:
            score += 10
        if sma20_slope > 0:
            score += 5
        if sma10_slope > sma20_slope > 0:
            score += 5
        
        # Pullback depth (max 15 points)
        pullback = metrics.get('pullback_pct', 100)
        if pullback <= 25:
            score += 8
        if pullback <= 15:
            score += 4
        if pullback <= 10:
            score += 3
        
        # Volume decline (max 15 points)
        vol_decline = metrics.get('volume_decline_pct', 0)
        if vol_decline >= 20:
            score += 5
        if vol_decline >= 40:
            score += 5
        if vol_decline >= 60:
            score += 5
        
        # Range tightening (max 10 points)
        if metrics.get('range_tightening', False):
            score += 10
        
        # Distance to breakout (max 10 points)
        distance = metrics.get('distance_to_breakout', 100)
        if distance <= 5:
            score += 5
        if distance <= 2:
            score += 5
        
        # Price above SMAs (max 5 points)
        if metrics.get('above_sma10', False):
            score += 3
        if metrics.get('above_sma20', False):
            score += 2
        
        return min(100, score)
    
    def scan_stock(self, symbol: str) -> Optional[Dict]:
        """
        Scan a single stock for breakout setup.
        Returns metrics dictionary or None if stock doesn't meet basic criteria.
        """
        try:
            # Download stock data
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            df = ticker.history(start=start_date, end=end_date)
            
            if len(df) < 50:
                return None
            
            # Get current price
            current_price = df['Close'].iloc[-1]
            
            # Check minimum price
            if current_price < self.min_price:
                return None
            
            # Calculate SMAs
            df['SMA10'] = self.calculate_sma(df['Close'], 10)
            df['SMA20'] = self.calculate_sma(df['Close'], 20)
            df['SMA50'] = self.calculate_sma(df['Close'], 50)
            df['SMA200'] = self.calculate_sma(df['Close'], 200)
            
            # Calculate ADR
            adr = self.calculate_adr(df['High'], df['Low'])
            if adr < self.min_adr_pct:
                return None
            
            # Calculate average dollar volume
            avg_volume = df['Volume'].tail(20).mean()
            avg_dollar_volume = avg_volume * current_price
            if avg_dollar_volume < self.min_dollar_volume:
                return None
            
            # Find prior move
            prior_move = self.find_prior_move(df['Close'], lookback=60)
            
            # Analyze consolidation
            consolidation = self.analyze_consolidation(df, lookback=20)
            
            # Calculate SMA slopes
            sma10_slope = self.calculate_slope(df['SMA10'], period=10)
            sma20_slope = self.calculate_slope(df['SMA20'], period=10)
            
            # Distance to breakout
            distance_to_breakout = self.calculate_distance_to_breakout(df, lookback=20)
            
            # Compile all metrics
            metrics = {
                'symbol': symbol,
                'price': round(current_price, 2),
                'prior_move_pct': round(prior_move['move_pct'], 1),
                'sma10_slope': round(sma10_slope, 2),
                'sma20_slope': round(sma20_slope, 2),
                'pullback_pct': round(consolidation['pullback_pct'], 1),
                'volume_decline_pct': round(consolidation['volume_decline_pct'], 0),
                'range_tightening': consolidation['range_tightening'],
                'days_consolidating': consolidation['days_consolidating'],
                'above_sma10': consolidation['above_sma10'],
                'above_sma20': consolidation['above_sma20'],
                'distance_to_breakout': round(distance_to_breakout, 1),
                'adr_pct': round(adr, 1),
                'avg_volume': round(avg_volume / 1_000_000, 2),  # In millions
                'avg_dollar_volume': round(avg_dollar_volume / 1_000_000, 1),  # In millions
            }
            
            # Calculate score
            metrics['score'] = self.calculate_breakout_score(metrics)
            
            # Determine status
            if metrics['score'] >= 75:
                metrics['status'] = 'ready'
            elif metrics['score'] >= 50:
                metrics['status'] = 'forming'
            else:
                metrics['status'] = 'watching'
            
            # Get company info
            try:
                info = ticker.info
                metrics['name'] = info.get('shortName', symbol)
                metrics['sector'] = info.get('sector', 'Unknown')
                metrics['industry'] = info.get('industry', 'Unknown')
            except:
                metrics['name'] = symbol
                metrics['sector'] = 'Unknown'
                metrics['industry'] = 'Unknown'
            
            # Get chart data for frontend
            chart_data = []
            for idx, row in df.tail(60).iterrows():
                chart_data.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'price': round(row['Close'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'open': round(row['Open'], 2),
                    'volume': int(row['Volume']),
                    'sma10': round(row['SMA10'], 2) if pd.notna(row['SMA10']) else None,
                    'sma20': round(row['SMA20'], 2) if pd.notna(row['SMA20']) else None,
                })
            metrics['chart_data'] = chart_data
            
            return metrics
            
        except Exception as e:
            print(f"Error scanning {symbol}: {str(e)}")
            return None
    
    def scan_all(self, symbols: List[str] = None, max_workers: int = 5) -> List[Dict]:
        """
        Scan all stocks in parallel.
        Returns list of stocks that meet criteria, sorted by score.
        """
        if symbols is None:
            symbols = self.get_stock_universe()
        
        results = []
        total = len(symbols)
        
        print(f"Scanning {total} stocks...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.scan_stock, symbol): symbol for symbol in symbols}
            
            for i, future in enumerate(as_completed(futures), 1):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                        status_icon = '🟢' if result['status'] == 'ready' else '🟡' if result['status'] == 'forming' else '⚪'
                        print(f"[{i}/{total}] {status_icon} {symbol}: Score {result['score']}")
                    else:
                        print(f"[{i}/{total}] ❌ {symbol}: Filtered out")
                except Exception as e:
                    print(f"[{i}/{total}] ❌ {symbol}: Error - {str(e)}")
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results


def main():
    """Run the scanner and save results to JSON."""
    scanner = BreakoutScanner()
    
    print("=" * 60)
    print("BREAKOUT STOCK SCANNER")
    print("Bull Flag / Consolidation Pattern Detector")
    print("=" * 60)
    print()
    
    start_time = time.time()
    results = scanner.scan_all()
    elapsed = time.time() - start_time
    
    print()
    print("=" * 60)
    print(f"SCAN COMPLETE - {len(results)} stocks found in {elapsed:.1f}s")
    print("=" * 60)
    print()
    
    # Summary stats
    ready = [r for r in results if r['status'] == 'ready']
    forming = [r for r in results if r['status'] == 'forming']
    watching = [r for r in results if r['status'] == 'watching']
    
    print(f"🟢 Ready to Break:    {len(ready)}")
    print(f"🟡 Pattern Forming:   {len(forming)}")
    print(f"⚪ On Watchlist:      {len(watching)}")
    print()
    
    # Show top picks
    if ready:
        print("TOP BREAKOUT CANDIDATES:")
        print("-" * 40)
        for stock in ready[:5]:
            print(f"  {stock['symbol']:6} | Score: {stock['score']:3} | Prior Move: {stock['prior_move_pct']:5.1f}% | Distance: {stock['distance_to_breakout']:5.1f}%")
    
    # Save to JSON
    output = {
        'scan_time': datetime.now().isoformat(),
        'total_scanned': len(scanner.get_stock_universe()),
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
    
    print()
    print(f"Results saved to scan_results.json")
    
    return results


if __name__ == '__main__':
    main()
