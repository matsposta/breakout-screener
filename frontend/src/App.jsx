import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, ResponsiveContainer,
  Area, ComposedChart, Bar, Tooltip
} from 'recharts';

// Icons (using simple SVG components to avoid dependencies)
const Icons = {
  TrendingUp: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </svg>
  ),
  Search: ({ size = 18 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  RefreshCw: ({ className = '' }) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  ),
  ChevronDown: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
  ChevronUp: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="18 15 12 9 6 15" />
    </svg>
  ),
  Zap: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  ),
  Clock: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  Activity: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  ),
  CheckCircle: ({ size = 12 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  AlertCircle: ({ size = 48 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
};

// API Configuration
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Status Badge Component
const StatusBadge = ({ status }) => {
  const configs = {
    ready: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/40', label: 'READY' },
    forming: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/40', label: 'FORMING' },
    watching: { bg: 'bg-slate-500/20', text: 'text-slate-400', border: 'border-slate-500/40', label: 'WATCHING' },
  };
  const config = configs[status] || configs.watching;
  const Icon = status === 'ready' ? Icons.Zap : status === 'forming' ? Icons.Clock : Icons.Search;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold tracking-wider ${config.bg} ${config.text} border ${config.border}`}>
      <Icon size={12} />
      {config.label}
    </span>
  );
};

// Score Gauge Component
const ScoreGauge = ({ score }) => {
  const color = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#64748b';
  const circumference = 2 * Math.PI * 36;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-20 h-20">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" fill="none" stroke="#1e293b" strokeWidth="6" />
        <circle
          cx="40" cy="40" r="36" fill="none"
          stroke={color} strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-black" style={{ color }}>{score}</span>
      </div>
    </div>
  );
};

// Mini Chart Component
const MiniChart = ({ data, showSMA = true, height = 80 }) => {
  if (!data || data.length === 0) {
    return <div className="w-full h-20 bg-slate-800 rounded animate-pulse" />;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
        <defs>
          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="price" stroke="#3b82f6" strokeWidth={2} fill="url(#priceGradient)" />
        {showSMA && <Line type="monotone" dataKey="sma10" stroke="#10b981" strokeWidth={1.5} dot={false} />}
        {showSMA && <Line type="monotone" dataKey="sma20" stroke="#f59e0b" strokeWidth={1.5} dot={false} />}
      </ComposedChart>
    </ResponsiveContainer>
  );
};

// Criteria Check Component
const CriteriaCheck = ({ label, met, value }) => (
  <div className={`flex items-center justify-between py-1.5 px-2 rounded ${met ? 'bg-emerald-500/10' : 'bg-slate-800/50'}`}>
    <span className="text-xs text-slate-400">{label}</span>
    <div className="flex items-center gap-2">
      <span className={`text-xs font-mono ${met ? 'text-emerald-400' : 'text-slate-500'}`}>{value}</span>
      {met ? <Icons.CheckCircle size={12} /> : <div className="w-3 h-3 rounded-full border border-slate-600" />}
    </div>
  </div>
);

// Stock Card Component
const StockCard = ({ stock, expanded, onToggle }) => {
  const criteria = [
    { label: 'Prior Move ≥30%', met: stock.prior_move_pct >= 30, value: `${stock.prior_move_pct}%` },
    { label: '10 SMA Inclining', met: stock.sma10_slope > 0, value: stock.sma10_slope?.toFixed(2) },
    { label: '20 SMA Inclining', met: stock.sma20_slope > 0, value: stock.sma20_slope?.toFixed(2) },
    { label: 'Pullback ≤20%', met: stock.pullback_pct <= 20, value: `${stock.pullback_pct}%` },
    { label: 'Volume Decline', met: stock.volume_decline_pct >= 40, value: `${stock.volume_decline_pct}%` },
    { label: 'ADR ≥5%', met: stock.adr_pct >= 5, value: `${stock.adr_pct}%` },
  ];

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-slate-700/50 overflow-hidden transition-all duration-300 ${expanded ? 'ring-2 ring-blue-500/50' : 'hover:border-slate-600'}`}>
      <div className="p-5 cursor-pointer" onClick={onToggle}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <ScoreGauge score={stock.score} />
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-black text-white tracking-tight">{stock.symbol}</h3>
                <StatusBadge status={stock.status} />
              </div>
              <p className="text-sm text-slate-400 mt-0.5">{stock.name}</p>
              <div className="flex items-center gap-4 mt-2">
                <span className="text-lg font-bold text-white">${stock.price}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">{stock.sector}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="w-32 h-16">
              <MiniChart data={stock.chart_data} showSMA={false} height={64} />
            </div>
            {expanded ? <Icons.ChevronUp /> : <Icons.ChevronDown />}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-700/50 p-5 bg-slate-900/50">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                <Icons.Activity size={14} />
                BREAKOUT CRITERIA
              </h4>
              <div className="space-y-1.5">
                {criteria.map((c, i) => (
                  <CriteriaCheck key={i} {...c} />
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                <Icons.TrendingUp />
                CHART ANALYSIS
              </h4>
              <div className="bg-slate-800/50 rounded-xl p-3 h-32">
                <MiniChart data={stock.chart_data} height={110} />
              </div>
              <div className="flex items-center justify-between mt-3 text-xs">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-blue-500 rounded" />
                  <span className="text-slate-400">Price</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-emerald-500 rounded" />
                  <span className="text-slate-400">10 SMA</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-0.5 bg-amber-500 rounded" />
                  <span className="text-slate-400">20 SMA</span>
                </span>
              </div>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-4 gap-3">
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">Distance to BO</div>
              <div className={`text-lg font-bold mt-1 ${stock.distance_to_breakout <= 3 ? 'text-emerald-400' : 'text-slate-300'}`}>
                {stock.distance_to_breakout}%
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">Consolidation</div>
              <div className="text-lg font-bold mt-1 text-slate-300">{stock.days_consolidating} days</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">Avg Volume</div>
              <div className="text-lg font-bold mt-1 text-slate-300">{stock.avg_volume}M</div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">$ Volume</div>
              <div className="text-lg font-bold mt-1 text-slate-300">${stock.avg_dollar_volume}M</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
export default function App() {
  const [stocks, setStocks] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [scanTime, setScanTime] = useState(null);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState({ ready: 0, forming: 0, watching: 0 });

  // Fetch results from API
  const fetchResults = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE}/api/results?status=${filter}&sort=${sortBy}&search=${searchTerm}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      
      const data = await response.json();
      setStocks(data.stocks || []);
      setScanTime(data.scan_time);
      setIsScanning(data.is_scanning);
      setSummary(data.summary || { ready: 0, forming: 0, watching: 0 });
    } catch (err) {
      setError(err.message);
      // Use mock data if API fails
      console.warn('API unavailable, using demo data');
    } finally {
      setIsLoading(false);
    }
  }, [filter, sortBy, searchTerm]);

  // Trigger a new scan
  const triggerScan = async () => {
    try {
      setIsScanning(true);
      const response = await fetch(`${API_BASE}/api/scan`, { method: 'POST' });
      
      if (response.ok) {
        // Poll for results
        const pollInterval = setInterval(async () => {
          const statusResponse = await fetch(`${API_BASE}/api/status`);
          const status = await statusResponse.json();
          
          if (!status.is_scanning) {
            clearInterval(pollInterval);
            setIsScanning(false);
            fetchResults();
          }
        }, 2000);
      }
    } catch (err) {
      setError('Failed to start scan');
      setIsScanning(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Filter stocks client-side for instant feedback
  const filteredStocks = useMemo(() => {
    let result = [...stocks];

    if (filter !== 'all') {
      result = result.filter(s => s.status === filter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(s =>
        s.symbol?.toLowerCase().includes(term) ||
        s.name?.toLowerCase().includes(term)
      );
    }

    if (sortBy === 'score') {
      result.sort((a, b) => b.score - a.score);
    } else if (sortBy === 'prior_move') {
      result.sort((a, b) => b.prior_move_pct - a.prior_move_pct);
    } else if (sortBy === 'distance') {
      result.sort((a, b) => a.distance_to_breakout - b.distance_to_breakout);
    }

    return result;
  }, [stocks, filter, searchTerm, sortBy]);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Decorative background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-full h-full bg-gradient-radial from-blue-500/5 to-transparent" />
        <div className="absolute -bottom-1/2 -left-1/2 w-full h-full bg-gradient-radial from-emerald-500/5 to-transparent" />
      </div>

      {/* Header */}
      <header className="relative border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center">
                <Icons.TrendingUp />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight">BREAKOUT SCREENER</h1>
                <p className="text-sm text-slate-400">
                  Bull Flag & Consolidation Pattern Scanner
                  {scanTime && <span className="ml-2 text-slate-500">• Last scan: {new Date(scanTime).toLocaleString()}</span>}
                </p>
              </div>
            </div>
            <button
              onClick={triggerScan}
              disabled={isScanning}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors disabled:opacity-50"
            >
              <Icons.RefreshCw className={isScanning ? 'animate-spin' : ''} />
              <span className="text-sm font-medium">{isScanning ? 'Scanning...' : 'Run Scan'}</span>
            </button>
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <button
            onClick={() => setFilter(filter === 'ready' ? 'all' : 'ready')}
            className={`p-5 rounded-2xl border transition-all ${filter === 'ready' ? 'bg-emerald-500/20 border-emerald-500/50' : 'bg-slate-900/50 border-slate-800 hover:border-emerald-500/30'}`}
          >
            <div className="flex items-center justify-between">
              <Icons.Zap size={24} />
              <span className="text-4xl font-black text-emerald-400">{summary.ready}</span>
            </div>
            <div className="text-left mt-2">
              <div className="text-sm font-bold text-white">Ready to Break</div>
              <div className="text-xs text-slate-400">Score ≥75</div>
            </div>
          </button>

          <button
            onClick={() => setFilter(filter === 'forming' ? 'all' : 'forming')}
            className={`p-5 rounded-2xl border transition-all ${filter === 'forming' ? 'bg-amber-500/20 border-amber-500/50' : 'bg-slate-900/50 border-slate-800 hover:border-amber-500/30'}`}
          >
            <div className="flex items-center justify-between">
              <Icons.Clock size={24} />
              <span className="text-4xl font-black text-amber-400">{summary.forming}</span>
            </div>
            <div className="text-left mt-2">
              <div className="text-sm font-bold text-white">Pattern Forming</div>
              <div className="text-xs text-slate-400">Score 50-74</div>
            </div>
          </button>

          <button
            onClick={() => setFilter(filter === 'watching' ? 'all' : 'watching')}
            className={`p-5 rounded-2xl border transition-all ${filter === 'watching' ? 'bg-slate-500/20 border-slate-500/50' : 'bg-slate-900/50 border-slate-800 hover:border-slate-500/30'}`}
          >
            <div className="flex items-center justify-between">
              <Icons.Search size={24} />
              <span className="text-4xl font-black text-slate-400">{summary.watching}</span>
            </div>
            <div className="text-left mt-2">
              <div className="text-sm font-bold text-white">On Watchlist</div>
              <div className="text-xs text-slate-400">Score &lt;50</div>
            </div>
          </button>
        </div>

        {/* Filters Bar */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Icons.Search size={18} />
            <input
              type="text"
              placeholder="Search by symbol or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-900/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              style={{ paddingLeft: '2.75rem' }}
            />
          </div>

          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-xl p-1">
            <span className="text-xs text-slate-500 px-2">Sort:</span>
            {[
              { key: 'score', label: 'Score' },
              { key: 'prior_move', label: 'Move %' },
              { key: 'distance', label: 'Distance' },
            ].map(opt => (
              <button
                key={opt.key}
                onClick={() => setSortBy(opt.key)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${sortBy === opt.key ? 'bg-blue-500 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Criteria Legend */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 mb-6">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Breakout Criteria (5-Step Process)</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">1</span>
              <span className="text-slate-300">Prior move ≥30%</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">2</span>
              <span className="text-slate-300">10/20 SMA inclining</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">3</span>
              <span className="text-slate-300">Orderly pullback</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">4</span>
              <span className="text-slate-300">Volume drying up</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">5</span>
              <span className="text-slate-300">Breakout on volume</span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 text-red-400">
            {error} - Make sure the backend server is running on port 5000.
          </div>
        )}

        {/* Stock Cards */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Icons.RefreshCw className="animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="space-y-4">
            {filteredStocks.map(stock => (
              <StockCard
                key={stock.symbol}
                stock={stock}
                expanded={expandedId === stock.symbol}
                onToggle={() => setExpandedId(expandedId === stock.symbol ? null : stock.symbol)}
              />
            ))}

            {filteredStocks.length === 0 && (
              <div className="text-center py-20">
                <Icons.AlertCircle size={48} />
                <p className="text-slate-400 mt-4">
                  {stocks.length === 0 
                    ? 'No scan results. Click "Run Scan" to scan stocks.' 
                    : 'No stocks match your criteria'}
                </p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative border-t border-slate-800/50 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center">
          <p className="text-xs text-slate-500">
            Based on the Bull Flag / Breakout swing trading methodology. For educational purposes only. Not financial advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
