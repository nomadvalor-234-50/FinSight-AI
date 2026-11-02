
import React, { useState } from "react";
import {
  TrendingUp, CalendarDays, Wallet, ArrowDown,
  ArrowUp, ShieldAlert, Sparkles, Info, ChartNoAxesCombined
} from "lucide-react";

export default function CashFlowForecast() {
  const [period, setPeriod] = useState("30 Days");

  return (
    <div className="forecast-page">
      <div className="forecast-header">
        <div>
          <span className="forecast-eyebrow">FINANCIAL INTELLIGENCE / FORECASTING</span>
          <h1>Cash Flow Forecast</h1>
          <p>Understand your projected financial position and prepare for future cash requirements.</p>
        </div>
        <div className="forecast-period">
          <CalendarDays size={17} />
          <select value={period} onChange={e => setPeriod(e.target.value)}>
            <option>7 Days</option>
            <option>30 Days</option>
            <option>90 Days</option>
          </select>
        </div>
      </div>

      <div className="forecast-info">
        <Info size={19} />
        <div>
          <strong>Forecasting is awaiting financial data</strong>
          <p>Connect your transactions, income, expenses and recurring commitments to generate your cash flow forecast.</p>
        </div>
      </div>

      <div className="forecast-stats">
        <div className="forecast-stat-card">
          <span><Wallet size={17} /> Projected Closing Balance</span>
          <h2>--</h2>
          <small>Awaiting financial data</small>
        </div>
        <div className="forecast-stat-card">
          <span><ArrowDown size={17} /> Expected Income</span>
          <h2>--</h2>
          <small>Awaiting financial data</small>
        </div>
        <div className="forecast-stat-card">
          <span><ArrowUp size={17} /> Expected Expenses</span>
          <h2>--</h2>
          <small>Awaiting financial data</small>
        </div>
        <div className="forecast-stat-card">
          <span><ShieldAlert size={17} /> Shortfall Risk</span>
          <h2>--</h2>
          <small>Risk analysis unavailable</small>
        </div>
      </div>

      <div className="forecast-chart-card">
        <div className="forecast-card-heading">
          <div>
            <h3>Projected Cash Balance</h3>
            <p>{period} cash flow projection</p>
          </div>
          <span className="forecast-legend">
            <i /> Forecasted Balance
          </span>
        </div>

        <div className="forecast-chart-empty">
          <div className="forecast-empty-icon">
            <ChartNoAxesCombined size={34} />
          </div>
          <h3>Your forecast will appear here</h3>
          <p>Once financial data is available, FinSight AI will visualize historical cash flow and projected future balances.</p>
        </div>
      </div>

      <div className="forecast-bottom-grid">
        <div className="forecast-detail-card">
          <h3><CalendarDays size={18} /> Upcoming Cash Movements</h3>
          <div className="forecast-detail-empty">
            <p>No upcoming cash movements available.</p>
            <span>Recurring payments and planned obligations will appear here.</span>
          </div>
        </div>

        <div className="forecast-detail-card">
          <h3><ShieldAlert size={18} /> Potential Cash Shortfalls</h3>
          <div className="forecast-detail-empty">
            <p>No risk assessment available yet.</p>
            <span>Risk alerts will be generated after forecast analysis.</span>
          </div>
        </div>
      </div>

      <div className="forecast-ai-card">
        <div className="forecast-ai-icon"><Sparkles size={22} /></div>
        <div>
          <h3>AI Forecast Explanation</h3>
          <p>FinSight AI will explain expected cash movements, identify potential liquidity problems and suggest actions based on your financial data.</p>
          <span>AI analysis will be available after backend integration.</span>
        </div>
      </div>
    </div>
  );
}
