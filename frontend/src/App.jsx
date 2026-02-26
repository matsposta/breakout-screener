import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ResponsiveContainer, Area, ComposedChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Cell
} from 'recharts';

// Icons
const Icons = {
  Fire: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 23c-4.97 0-9-3.582-9-8 0-2.79 1.578-5.273 4-6.818V6c0-.552.447-1 1-1s1 .448 1 1v1.618c.93-.583 1.96-1.015 3-1.29V4c0-.552.447-1 1-1s1 .448 1 1v2c.552 0 1.103.046 1.649.133C17.618 4.038 19.5 2 19.5 2s.5 2.5-.5 5c1.828 1.5 3 3.953 3 6.5 0 5.247-4.253 9.5-9.5 9.5h-.5z"/>
    </svg>
  ),
  TrendingUp: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
  Eye: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  Book: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  ),
  BarChart2: ({ size = 24 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
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
  RefreshCw: ({ className = '' }) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  ),
  Target: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  ),
  Award: ({ size = 20 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="8" r="7" />
      <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88" />
    </svg>
  ),
  CheckCircle: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  XCircle: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  ArrowUp: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="19" x2="12" y2="5" />
      <polyline points="5 12 12 5 19 12" />
    </svg>
  ),
  ArrowDown: ({ size = 14 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19" />
      <polyline points="19 12 12 19 5 12" />
    </svg>
  ),
};

// API Configuration
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Format date to Eastern Time display
const formatEasternTime = (isoString) => {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    timeZone: 'America/New_York',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }) + ' ET';
};

// Hot Score Badge
const HotScoreBadge = ({ score }) => {
  const isHot = score >= 80;
  const isWarm = score >= 60 && score < 80;
  
  return (
    <div className={`relative group cursor-pointer transition-transform hover:scale-105 ${isHot ? 'animate-pulse' : ''}`}>
      <div className={`
        w-16 h-16 rounded-2xl flex items-center justify-center font-black text-xl
        ${isHot ? 'bg-gradient-to-br from-orange-500 to-red-600 text-white shadow-lg shadow-orange-500/30' : 
          isWarm ? 'bg-gradient-to-br from-amber-500 to-orange-500 text-white' : 
          'bg-slate-800 text-slate-400'}
      `}>
        {score}
      </div>
      {isHot && (
        <div className="absolute -top-1 -right-1">
          <span className="flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-orange-500 items-center justify-center">
              <Icons.Fire size={10} />
            </span>
          </span>
        </div>
      )}
    </div>
  );
};

// Status Chip
const StatusChip = ({ status }) => {
  const configs = {
    ready: { bg: 'bg-gradient-to-r from-orange-500 to-red-500', text: 'text-white', label: 'HOT', icon: Icons.Fire },
    forming: { bg: 'bg-gradient-to-r from-amber-500 to-orange-500', text: 'text-white', label: 'WARMING', icon: Icons.TrendingUp },
    watching: { bg: 'bg-slate-700', text: 'text-slate-300', label: 'WATCHING', icon: Icons.Eye },
  };
  const config = configs[status] || configs.watching;
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold tracking-wide ${config.bg} ${config.text} shadow-sm`}>
      <Icon size={12} />
      {config.label}
    </span>
  );
};

// Mini Chart Component
const MiniChart = ({ data, height = 60 }) => {
  if (!data || data.length === 0) {
    return <div className={`w-full bg-slate-800/50 rounded-lg animate-pulse`} style={{height}} />;
  }
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 5, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f97316" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="price" stroke="#f97316" strokeWidth={2} fill="url(#chartGradient)" />
        <Line type="monotone" dataKey="sma10" stroke="#22c55e" strokeWidth={1.5} dot={false} />
        <Line type="monotone" dataKey="sma20" stroke="#eab308" strokeWidth={1.5} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

// Criteria Row
const CriteriaRow = ({ label, met, value }) => (
  <div className={`flex items-center justify-between py-2 px-3 rounded-lg transition-all ${met ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-slate-800/30'}`}>
    <div className="flex items-center gap-2">
      {met ? <Icons.CheckCircle size={14} className="text-emerald-400" /> : <Icons.XCircle size={14} className="text-slate-500" />}
      <span className={`text-sm ${met ? 'text-emerald-400' : 'text-slate-400'}`}>{label}</span>
    </div>
    <span className={`text-sm font-mono font-medium ${met ? 'text-emerald-400' : 'text-slate-500'}`}>{value}</span>
  </div>
);

// Performance Return Badge
const ReturnBadge = ({ days, value }) => {
  const isPositive = value > 0;
  const displayValue = value === '--' ? '--' : `${isPositive ? '+' : ''}${value}%`;
  return (
    <div className={`text-center p-3 rounded-xl ${value === '--' ? 'bg-slate-800/50' : isPositive ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
      <div className="text-xs text-slate-400 mb-1">{days}D</div>
      <div className={`text-lg font-bold ${value === '--' ? 'text-slate-500' : isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
        {displayValue}
      </div>
    </div>
  );
};

// Stock Card Component
const StockCard = ({ stock, expanded, onToggle, rank }) => {
  const criteria = [
    { label: 'Prior Move ≥30%', met: stock.prior_move_pct >= 30, value: `${stock.prior_move_pct}%` },
    { label: '10 SMA Inclining', met: stock.sma10_slope > 0, value: stock.sma10_slope?.toFixed(2) },
    { label: '20 SMA Inclining', met: stock.sma20_slope > 0, value: stock.sma20_slope?.toFixed(2) },
    { label: 'Pullback ≤20%', met: stock.pullback_pct <= 20, value: `${stock.pullback_pct}%` },
    { label: 'Volume Decline', met: stock.volume_decline_pct >= 40, value: `${stock.volume_decline_pct}%` },
    { label: 'ADR ≥5%', met: stock.adr_pct >= 5, value: `${stock.adr_pct}%` },
  ];
  const metCount = criteria.filter(c => c.met).length;

  return (
    <div className={`group relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 rounded-2xl border overflow-hidden transition-all duration-300
      ${expanded ? 'border-orange-500/50 shadow-xl shadow-orange-500/10' : 'border-slate-700/50 hover:border-slate-600'}
      ${stock.score >= 80 ? 'ring-1 ring-orange-500/20' : ''}`}>
      
      {rank <= 3 && (
        <div className={`absolute top-4 left-4 w-8 h-8 rounded-full flex items-center justify-center text-sm font-black
          ${rank === 1 ? 'bg-gradient-to-br from-yellow-400 to-amber-500 text-black' : 
            rank === 2 ? 'bg-gradient-to-br from-slate-300 to-slate-400 text-black' : 
            'bg-gradient-to-br from-amber-600 to-amber-700 text-white'}`}>
          #{rank}
        </div>
      )}

      <div className="p-5 cursor-pointer" onClick={onToggle}>
        <div className="flex items-center gap-5">
          <HotScoreBadge score={stock.score} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-2xl font-black text-white tracking-tight">{stock.symbol}</h3>
              <StatusChip status={stock.status} />
            </div>
            <p className="text-sm text-slate-400 truncate">{stock.name}</p>
            <div className="flex items-center gap-4 mt-2 flex-wrap">
              <span className="text-xl font-bold text-white">${stock.price}</span>
              <span className="text-xs px-2 py-1 rounded-md bg-blue-500/20 text-blue-400 font-medium">{stock.market_cap_fmt || 'N/A'}</span>
              <span className="text-xs px-2 py-1 rounded-md bg-slate-800 text-slate-400">{stock.sector}</span>
              <span className="text-xs text-slate-500">{metCount}/6 criteria met</span>
            </div>
          </div>
          <div className="hidden sm:block w-40 h-16">
            <MiniChart data={stock.chart_data} height={64} />
          </div>
          <div className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>
            <Icons.ChevronDown />
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-700/50 bg-slate-900/80 backdrop-blur">
          <div className="p-5 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-bold text-orange-400 mb-3 flex items-center gap-2">
                <Icons.Target size={14} />
                BREAKOUT CRITERIA
              </h4>
              <div className="space-y-2">
                {criteria.map((c, i) => <CriteriaRow key={i} {...c} />)}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold text-orange-400 mb-3 flex items-center gap-2">
                <Icons.BarChart2 size={14} />
                PRICE ACTION
              </h4>
              <div className="bg-slate-800/50 rounded-xl p-3 h-40">
                <MiniChart data={stock.chart_data} height={130} />
              </div>
              <div className="flex items-center justify-center gap-6 mt-3 text-xs">
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-orange-500 rounded" /><span className="text-slate-400">Price</span></span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-emerald-500 rounded" /><span className="text-slate-400">10 SMA</span></span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-amber-500 rounded" /><span className="text-slate-400">20 SMA</span></span>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-bold text-orange-400 mb-3 flex items-center gap-2">
                <Icons.Award size={14} />
                KEY METRICS
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 text-center col-span-2">
                  <div className="text-xs text-blue-400 uppercase">Market Cap</div>
                  <div className="text-lg font-bold text-blue-400">{stock.market_cap_fmt || 'N/A'}</div>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-500 uppercase">Distance</div>
                  <div className={`text-lg font-bold ${stock.distance_to_breakout <= 3 ? 'text-orange-400' : 'text-slate-300'}`}>{stock.distance_to_breakout}%</div>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-500 uppercase">Days Tight</div>
                  <div className="text-lg font-bold text-slate-300">{stock.days_consolidating}</div>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-500 uppercase">ADR%</div>
                  <div className="text-lg font-bold text-slate-300">{stock.adr_pct}%</div>
                </div>
                <div className="bg-slate-800/50 rounded-xl p-3 text-center">
                  <div className="text-xs text-slate-500 uppercase">$ Volume</div>
                  <div className="text-lg font-bold text-slate-300">${stock.avg_dollar_volume}M</div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-gradient-to-r from-orange-500/10 to-transparent rounded-xl border border-orange-500/20">
                <div className="text-xs text-orange-400 font-medium mb-2">📊 Post-Signal Performance</div>
                <div className="grid grid-cols-4 gap-2">
                  <ReturnBadge days={1} value={stock.performance?.['1']?.return_pct || '--'} />
                  <ReturnBadge days={5} value={stock.performance?.['5']?.return_pct || '--'} />
                  <ReturnBadge days={20} value={stock.performance?.['20']?.return_pct || '--'} />
                  <ReturnBadge days={30} value={stock.performance?.['30']?.return_pct || '--'} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Stat Card Component
const StatCard = ({ icon: Icon, value, label, sublabel, active, onClick, colorClass }) => (
  <button onClick={onClick} className={`relative p-5 rounded-2xl border transition-all duration-300 text-left overflow-hidden
    ${active ? `${colorClass} border-transparent shadow-lg` : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'}`}>
    <div className="relative z-10">
      <div className="flex items-start justify-between mb-3">
        <Icon size={24} className={active ? 'text-white' : 'text-slate-400'} />
        <span className={`text-4xl font-black ${active ? 'text-white' : 'text-slate-200'}`}>{value}</span>
      </div>
      <div className={`text-sm font-bold ${active ? 'text-white/90' : 'text-white'}`}>{label}</div>
      <div className={`text-xs ${active ? 'text-white/70' : 'text-slate-400'}`}>{sublabel}</div>
    </div>
  </button>
);

// Learn Tab - Pattern Card
const PatternCard = ({ pattern }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="p-5 cursor-pointer hover:bg-slate-800/30 transition-colors" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">{pattern.name}</h3>
            <p className="text-sm text-slate-400 mt-1">{pattern.description}</p>
          </div>
          <div className={`transition-transform ${expanded ? 'rotate-180' : ''}`}>
            <Icons.ChevronDown />
          </div>
        </div>
      </div>
      {expanded && (
        <div className="border-t border-slate-800 p-5 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-orange-400 mb-2">Key Criteria</h4>
            <ul className="space-y-1">
              {pattern.criteria?.map((c, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <Icons.CheckCircle size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                  {c}
                </li>
              ))}
            </ul>
          </div>
          {pattern.psychology && (
            <div>
              <h4 className="text-sm font-bold text-blue-400 mb-2">Psychology Behind It</h4>
              <p className="text-sm text-slate-400">{pattern.psychology}</p>
            </div>
          )}
          {pattern.entry_rules && (
            <div>
              <h4 className="text-sm font-bold text-emerald-400 mb-2">Entry Rules</h4>
              <ul className="space-y-1">
                {pattern.entry_rules.map((r, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-emerald-400">{i + 1}.</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            {pattern.stop_loss && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                <h5 className="text-xs font-bold text-red-400 mb-1">Stop Loss</h5>
                <p className="text-sm text-slate-300">{pattern.stop_loss}</p>
              </div>
            )}
            {pattern.target && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3">
                <h5 className="text-xs font-bold text-emerald-400 mb-1">Target</h5>
                <p className="text-sm text-slate-300">{pattern.target}</p>
              </div>
            )}
          </div>
          {pattern.success_rate && (
            <div className="text-center py-2 bg-slate-800/50 rounded-xl">
              <span className="text-sm text-slate-400">Historical Success Rate: </span>
              <span className="text-sm font-bold text-amber-400">{pattern.success_rate}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Metric Definition Card
const MetricCard = ({ metric }) => (
  <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
    <div className="flex items-start justify-between mb-2">
      <h3 className="font-bold text-white">{metric.name}</h3>
      {metric.range && <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">{metric.range}</span>}
    </div>
    <p className="text-sm text-slate-400 mb-3">{metric.description}</p>
    {metric.why_it_matters && (
      <div className="text-xs bg-blue-500/10 border border-blue-500/20 rounded-lg p-2 mb-2">
        <span className="text-blue-400 font-medium">Why it matters: </span>
        <span className="text-slate-300">{metric.why_it_matters}</span>
      </div>
    )}
    {metric.ideal_range && (
      <div className="text-xs text-emerald-400">
        <span className="font-medium">Ideal: </span>{metric.ideal_range}
      </div>
    )}
    {metric.interpretation && (
      <div className="mt-2 space-y-1">
        {Object.entries(metric.interpretation).map(([range, desc]) => (
          <div key={range} className="text-xs flex">
            <span className="text-amber-400 font-mono w-16">{range}:</span>
            <span className="text-slate-400">{desc}</span>
          </div>
        ))}
      </div>
    )}
  </div>
);

// Performance Stats Card
const PerformanceStatsCard = ({ stats }) => {
  if (!stats || stats.total_signals === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center">
        <Icons.BarChart2 size={48} className="mx-auto text-slate-600 mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Performance Data Yet</h3>
        <p className="text-slate-400">Performance tracking starts when stocks hit 80+ score. Run scans to begin collecting data.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Historical Performance</h3>
          <span className="text-sm text-slate-400">{stats.total_signals} signals tracked</span>
        </div>
        <div className="grid grid-cols-4 gap-4">
          {[1, 5, 20, 30].map(days => {
            const data = stats.returns?.[days];
            return (
              <div key={days} className="bg-slate-800/50 rounded-xl p-4 text-center">
                <div className="text-xs text-slate-500 uppercase mb-1">{days}-Day Return</div>
                <div className={`text-2xl font-black ${data?.avg_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {data ? `${data.avg_return >= 0 ? '+' : ''}${data.avg_return}%` : '--'}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Win Rate: <span className={data?.win_rate >= 50 ? 'text-emerald-400' : 'text-slate-300'}>{data?.win_rate || '--'}%</span>
                </div>
              </div>
            );
          })}
        </div>
        {stats.best_holding_period && (
          <div className="mt-4 text-center p-3 bg-gradient-to-r from-orange-500/10 to-transparent rounded-xl border border-orange-500/20">
            <span className="text-slate-400">Optimal Holding Period: </span>
            <span className="text-orange-400 font-bold">{stats.best_holding_period} days</span>
          </div>
        )}
      </div>

      {stats.top_winners?.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4">
            <h4 className="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2">
              <Icons.ArrowUp size={14} /> Top Winners (5D)
            </h4>
            <div className="space-y-2">
              {stats.top_winners.map((w, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-white font-medium">{w.symbol}</span>
                  <span className="text-emerald-400">+{w.return}%</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
            <h4 className="text-sm font-bold text-red-400 mb-3 flex items-center gap-2">
              <Icons.ArrowDown size={14} /> Worst Performers (5D)
            </h4>
            <div className="space-y-2">
              {stats.top_losers?.map((l, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-white font-medium">{l.symbol}</span>
                  <span className="text-red-400">{l.return}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
export default function App() {
  const [activeTab, setActiveTab] = useState('scanner');
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
  const [universeCount, setUniverseCount] = useState(0);
  const [patterns, setPatterns] = useState({});
  const [metrics, setMetrics] = useState({});
  const [strategy, setStrategy] = useState({});
  const [performanceStats, setPerformanceStats] = useState(null);

  const fetchResults = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/api/results?status=${filter}&sort=${sortBy}&search=${searchTerm}`);
      if (!response.ok) throw new Error('Failed to fetch results');
      const data = await response.json();
      setStocks(data.stocks || []);
      setScanTime(data.scan_time);
      setIsScanning(data.is_scanning);
      setSummary(data.summary || { ready: 0, forming: 0, watching: 0 });
      setUniverseCount(data.total_universe || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [filter, sortBy, searchTerm]);

  const fetchLearnContent = async () => {
    try {
      const [patternsRes, metricsRes, strategyRes] = await Promise.all([
        fetch(`${API_BASE}/api/learn/patterns`),
        fetch(`${API_BASE}/api/learn/metrics`),
        fetch(`${API_BASE}/api/learn/strategy`)
      ]);
      if (patternsRes.ok) setPatterns((await patternsRes.json()).patterns || {});
      if (metricsRes.ok) setMetrics((await metricsRes.json()).metrics || {});
      if (strategyRes.ok) setStrategy(await strategyRes.json());
    } catch (err) {
      console.error('Error fetching learn content:', err);
    }
  };

  const fetchPerformanceStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/performance/stats`);
      if (response.ok) setPerformanceStats(await response.json());
    } catch (err) {
      console.error('Error fetching performance stats:', err);
    }
  };

  const triggerScan = async () => {
    try {
      setIsScanning(true);
      const response = await fetch(`${API_BASE}/api/scan`, { method: 'POST' });
      if (response.ok) {
        const pollInterval = setInterval(async () => {
          const statusResponse = await fetch(`${API_BASE}/api/status`);
          const status = await statusResponse.json();
          if (!status.is_scanning) {
            clearInterval(pollInterval);
            setIsScanning(false);
            fetchResults();
            fetchPerformanceStats();
          }
        }, 2000);
      }
    } catch (err) {
      setError('Failed to start scan');
      setIsScanning(false);
    }
  };

  useEffect(() => {
    fetchResults();
    fetchLearnContent();
    fetchPerformanceStats();
  }, [fetchResults]);

  const filteredStocks = useMemo(() => {
    let result = [...stocks];
    if (filter !== 'all') result = result.filter(s => s.status === filter);
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(s => s.symbol?.toLowerCase().includes(term) || s.name?.toLowerCase().includes(term));
    }
    if (sortBy === 'score') result.sort((a, b) => b.score - a.score);
    else if (sortBy === 'prior_move') result.sort((a, b) => b.prior_move_pct - a.prior_move_pct);
    else if (sortBy === 'distance') result.sort((a, b) => a.distance_to_breakout - b.distance_to_breakout);
    return result;
  }, [stocks, filter, searchTerm, sortBy]);

  const totalStocks = summary.ready + summary.forming + summary.watching;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-red-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      {/* Header */}
      <header className="relative border-b border-slate-800/50 bg-[#0a0a0f]/90 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 flex items-center justify-center shadow-lg shadow-orange-500/30">
                  <Icons.Fire size={28} />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-orange-400 via-red-400 to-pink-400 bg-clip-text text-transparent">
                  HOT STONKS
                </h1>
                <p className="text-sm text-slate-400">
                  {scanTime ? `Last scan: ${formatEasternTime(scanTime)}` : 'Breakout Pattern Scanner'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-xl">
                <span className="text-xs text-slate-400">Universe:</span>
                <span className="text-sm font-bold text-white">{universeCount || totalStocks}+ stocks</span>
              </div>
              <button onClick={triggerScan} disabled={isScanning}
                className={`flex items-center gap-2 px-5 py-3 rounded-xl font-medium transition-all
                  ${isScanning ? 'bg-slate-800 text-slate-400' : 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40 hover:scale-105'}`}>
                <Icons.RefreshCw className={isScanning ? 'animate-spin' : ''} />
                <span>{isScanning ? 'Scanning...' : 'Scan Now'}</span>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-2 mt-4 -mb-px">
            {[
              { id: 'scanner', label: 'Scanner', icon: Icons.Fire },
              { id: 'performance', label: 'Performance', icon: Icons.BarChart2 },
              { id: 'learn', label: 'Learn', icon: Icons.Book },
            ].map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-t-xl font-medium transition-all border-b-2 -mb-px
                  ${activeTab === tab.id 
                    ? 'bg-slate-900/80 text-orange-400 border-orange-500' 
                    : 'text-slate-400 hover:text-white border-transparent hover:bg-slate-800/30'}`}>
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* SCANNER TAB */}
        {activeTab === 'scanner' && (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <StatCard icon={Icons.Fire} value={summary.ready} label="Hot & Ready" sublabel="Score ≥75 — Prime for breakout"
                active={filter === 'ready'} onClick={() => setFilter(filter === 'ready' ? 'all' : 'ready')} colorClass="bg-gradient-to-br from-orange-500 to-red-600" />
              <StatCard icon={Icons.TrendingUp} value={summary.forming} label="Warming Up" sublabel="Score 50-74 — Pattern forming"
                active={filter === 'forming'} onClick={() => setFilter(filter === 'forming' ? 'all' : 'forming')} colorClass="bg-gradient-to-br from-amber-500 to-orange-500" />
              <StatCard icon={Icons.Eye} value={summary.watching} label="On Radar" sublabel="Score <50 — Keep watching"
                active={filter === 'watching'} onClick={() => setFilter(filter === 'watching' ? 'all' : 'watching')} colorClass="bg-gradient-to-br from-slate-600 to-slate-700" />
            </div>

            {/* Search & Sort Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 mb-6">
              <div className="relative flex-1">
                <Icons.Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input type="text" placeholder="Search stocks..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-12 pr-4 py-3.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-orange-500/50 focus:ring-2 focus:ring-orange-500/20 transition-all" />
              </div>
              <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 rounded-xl p-1.5">
                <span className="text-xs text-slate-500 px-2 hidden sm:block">Sort:</span>
                {[{ key: 'score', label: 'Score' }, { key: 'prior_move', label: 'Move %' }, { key: 'distance', label: 'Distance' }].map(opt => (
                  <button key={opt.key} onClick={() => setSortBy(opt.key)}
                    className={`px-4 py-2 text-sm rounded-lg transition-all ${sortBy === opt.key ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white font-medium shadow-sm' : 'text-slate-400 hover:text-white'}`}>
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
                <Icons.XCircle size={20} className="text-red-400" />
                <span className="text-red-400">{error}</span>
              </div>
            )}

            {/* Results Header */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white">
                {filter === 'all' ? 'All Stocks' : filter === 'ready' ? 'Hot Stocks' : filter === 'forming' ? 'Warming Up' : 'On Radar'}
                <span className="text-slate-400 font-normal ml-2">({filteredStocks.length})</span>
              </h2>
              {filter !== 'all' && <button onClick={() => setFilter('all')} className="text-sm text-orange-400 hover:text-orange-300">Show all →</button>}
            </div>

            {/* Stock Cards */}
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <Icons.RefreshCw className="animate-spin text-orange-500" size={32} />
                <span className="text-slate-400">Loading stocks...</span>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredStocks.map((stock, index) => (
                  <StockCard key={stock.symbol} stock={stock} expanded={expandedId === stock.symbol}
                    onToggle={() => setExpandedId(expandedId === stock.symbol ? null : stock.symbol)} rank={index + 1} />
                ))}
                {filteredStocks.length === 0 && (
                  <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-slate-800">
                    <Icons.Search size={48} className="mx-auto text-slate-600 mb-4" />
                    <p className="text-slate-400 text-lg">{stocks.length === 0 ? 'No scan results yet.' : 'No stocks match your criteria'}</p>
                    {stocks.length === 0 && (
                      <button onClick={triggerScan} className="mt-4 px-6 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg font-medium hover:scale-105 transition-transform">
                        Run Your First Scan
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* PERFORMANCE TAB */}
        {activeTab === 'performance' && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-black text-white mb-2">Performance Tracking</h2>
              <p className="text-slate-400">Track how breakout signals perform over time. Data collected from stocks that hit 80+ score.</p>
            </div>
            <PerformanceStatsCard stats={performanceStats} />
          </div>
        )}

        {/* LEARN TAB */}
        {activeTab === 'learn' && (
          <div className="space-y-8">
            {/* Strategy Overview */}
            {strategy.overview && (
              <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-2xl p-6">
                <h2 className="text-2xl font-black text-white mb-2">{strategy.overview.name}</h2>
                <p className="text-slate-300 mb-4">{strategy.overview.description}</p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-slate-400">Timeframe:</span> <span className="text-white font-medium">{strategy.overview.timeframe}</span></div>
                  <div><span className="text-slate-400">Best Market:</span> <span className="text-white font-medium">{strategy.overview.best_market_conditions}</span></div>
                </div>
              </div>
            )}

            {/* Patterns Section */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Icons.Target size={20} className="text-orange-400" />
                Pattern Definitions
              </h2>
              <div className="space-y-4">
                {Object.entries(patterns).map(([key, pattern]) => (
                  <PatternCard key={key} pattern={pattern} />
                ))}
              </div>
            </div>

            {/* Metrics Section */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Icons.BarChart2 size={20} className="text-orange-400" />
                Metric Definitions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(metrics).map(([key, metric]) => (
                  <MetricCard key={key} metric={metric} />
                ))}
              </div>
            </div>

            {/* Trading Checklist */}
            {strategy.setup_criteria && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">Setup Checklist</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {strategy.setup_criteria.checklist?.map((item, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-slate-300">
                      <Icons.CheckCircle size={14} className="text-emerald-400" />
                      {item.replace('✓ ', '')}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Management */}
            {strategy.risk_management && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
                <h2 className="text-xl font-bold text-white mb-4">Risk Management Rules</h2>
                <ul className="space-y-2">
                  {strategy.risk_management.rules?.map((rule, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <span className="text-red-400 font-bold">{i + 1}.</span>
                      {rule}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative border-t border-slate-800/50 mt-16">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                <Icons.Fire size={16} />
              </div>
              <span className="font-bold text-white">Hot Stonks</span>
            </div>
            <p className="text-sm text-slate-500 text-center">For educational purposes only. Not financial advice. Trade responsibly.</p>
            <div className="text-sm text-slate-500">© 2026 hotstonks.ai</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
