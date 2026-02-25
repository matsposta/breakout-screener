# 📈 Breakout Stock Screener

A powerful stock screener that identifies **bull flag and consolidation breakout patterns** based on swing trading methodology.

![Breakout Screener](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 What It Does

This screener automatically scans stocks looking for the classic **breakout setup**:

1. **Prior big move (30%+)** - Stock has made a significant run up
2. **Inclining SMAs** - 10 and 20-day moving averages trending upward
3. **Orderly pullback** - Price consolidates with tightening range
4. **Volume drying up** - Decreasing volume during consolidation
5. **Near breakout level** - Price approaching resistance

Each stock gets a **Breakout Score (0-100)** based on how well it meets these criteria.

## 🚀 Quick Start

### Option 1: Run the Scanner Only (Simplest)

```bash
# 1. Navigate to backend folder
cd backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the scanner
python scanner.py
```

This will scan ~70 momentum stocks and output results to `scan_results.json`.

### Option 2: Full App with Web Interface

#### Backend Setup
```bash
# Terminal 1: Start the API server
cd backend
pip install -r requirements.txt
python server.py
```

#### Frontend Setup
```bash
# Terminal 2: Start the React app
cd frontend
npm install
npm start
```

Open http://localhost:3000 in your browser.

## 📊 Understanding the Results

### Status Categories

| Status | Score | Meaning |
|--------|-------|---------|
| 🟢 **READY** | 75-100 | Meets most/all criteria, potential breakout imminent |
| 🟡 **FORMING** | 50-74 | Pattern developing, add to watchlist |
| ⚪ **WATCHING** | 0-49 | Doesn't meet enough criteria yet |

### Key Metrics

| Metric | What It Means |
|--------|---------------|
| **Prior Move %** | How much the stock ran before consolidating |
| **SMA Slopes** | Positive = uptrending, negative = downtrending |
| **Pullback %** | How far price has pulled back from highs |
| **Volume Decline %** | How much volume has decreased (higher = better) |
| **Distance to BO** | How close to breaking out (lower = closer) |
| **ADR %** | Average Daily Range - volatility measure |

## 🔧 Configuration

### Customize Stock Universe

Edit `backend/scanner.py` and modify the `get_stock_universe()` method:

```python
def get_stock_universe(self) -> List[str]:
    # Add your own stocks here
    return ['AAPL', 'MSFT', 'GOOGL', 'YOUR_STOCK']
```

### Adjust Screening Criteria

Modify the thresholds in the `BreakoutScanner` class:

```python
class BreakoutScanner:
    def __init__(self):
        self.min_price = 1.0           # Minimum stock price
        self.min_adr_pct = 5.0         # Minimum ADR%
        self.min_dollar_volume = 3_500_000  # Min daily $ volume
        self.min_prior_move = 30.0     # Min prior move %
        self.lookback_days = 120       # Days of history
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/results` | GET | Get scan results with optional filters |
| `/api/scan` | POST | Trigger a new scan |
| `/api/stock/<symbol>` | GET | Get details for a specific stock |
| `/api/scan/custom` | POST | Scan a custom list of symbols |
| `/api/universe` | GET | Get the default stock list |
| `/api/status` | GET | Check server status |

### Query Parameters for `/api/results`

- `status` - Filter by status: `all`, `ready`, `forming`, `watching`
- `sort` - Sort by: `score`, `prior_move`, `distance`
- `search` - Search by symbol or name
- `min_score` - Minimum score filter

## 📁 Project Structure

```
breakout-screener/
├── backend/
│   ├── scanner.py      # Core scanning logic
│   ├── server.py       # Flask API server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx     # Main React component
│   │   └── index.js    # Entry point
│   ├── public/
│   │   └── index.html
│   └── package.json
└── README.md
```

## 🎓 Trading Strategy Overview

This screener is based on the **bull flag / breakout** swing trading methodology:

### Entry Rules
1. Wait for the stock to break out of consolidation
2. Enter on the 1-min or 5-min opening range high
3. Stop loss at the low of the day
4. Confirm breakout on the daily chart

### Position Sizing
- Risk 1% of account per trade
- Position size = Risk Amount / (Entry - Stop)
- This allows large positions with controlled risk

### Sell Rules
- First partial sell (10-30%) when up 5x risk
- Move stop to breakeven after first sell
- Exit full position when price closes below 10 SMA

### Market Conditions
- Best when 10 SMA is above 20 SMA on $QQQ/$SPY
- Reduce size or avoid when 10 SMA is below 20 SMA

## ⚠️ Disclaimer

This tool is for **educational purposes only**. It is not financial advice. Trading stocks involves risk, and you can lose money. Always do your own research and consider consulting a financial advisor before making investment decisions.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new screening criteria
- Improve the UI
- Add more data sources
- Fix bugs

## 📜 License

MIT License - feel free to use and modify as you wish.
