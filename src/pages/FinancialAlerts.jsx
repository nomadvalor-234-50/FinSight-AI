
import React, { useState } from "react";
import {
  ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2,
  Bell, Wallet, CalendarClock, TrendingUp, Sparkles,
  Filter, Info
} from "lucide-react";

export default function FinancialAlerts() {
  const [filter, setFilter] = useState("All");

  const filters = ["All", "Critical", "High", "Medium", "Low"];

  return (
    <div className="alerts-page">
      <div className="alerts-header">
        <div>
          <span className="alerts-eyebrow">FINANCIAL INTELLIGENCE / RISK MONITORING</span>
          <h1>Financial Risk Alerts</h1>
          <p>Monitor potential financial risks and identify cash flow problems before they occur.</p>
        </div>
        <div className="alerts-status">
          <span className="alerts-status-dot" />
          Monitoring ready
        </div>
      </div>

      <div className="alerts-info">
        <ShieldAlert size={21} />
        <div>
          <strong>Risk monitoring is awaiting financial data</strong>
          <p>Connect transactions, budgets, recurring payments and forecasts to generate personalized financial risk alerts.</p>
        </div>
      </div>

      <div className="alerts-stats">
        <div className="alerts-stat-card">
          <span><Bell size={17} /> Total Alerts</span>
          <h2>--</h2>
          <small>Awaiting risk analysis</small>
        </div>
        <div className="alerts-stat-card">
          <span><AlertTriangle size={17} /> Critical Risks</span>
          <h2>--</h2>
          <small>Not yet evaluated</small>
        </div>
        <div className="alerts-stat-card">
          <span><AlertCircle size={17} /> High Risks</span>
          <h2>--</h2>
          <small>Not yet evaluated</small>
        </div>
        <div className="alerts-stat-card">
          <span><CheckCircle2 size={17} /> Resolved Alerts</span>
          <h2>--</h2>
          <small>No alert history available</small>
        </div>
      </div>

      <div className="alerts-section">
        <div className="alerts-section-heading">
          <div>
            <h3>Risk Alert Centre</h3>
            <p>Financial warnings generated from your financial activity.</p>
          </div>
          <div className="alerts-filter">
            <Filter size={15} />
            <select value={filter} onChange={e => setFilter(e.target.value)}>
              {filters.map(item => <option key={item}>{item}</option>)}
            </select>
          </div>
        </div>

        <div className="alerts-empty">
          <div className="alerts-empty-icon">
            <ShieldAlert size={34} />
          </div>
          <h3>No risk alerts available yet</h3>
          <p>Once financial data is connected, FinSight AI will analyze your cash flow and display relevant risk alerts here.</p>
        </div>
      </div>

      <div className="alerts-two-column">
        <div className="alerts-detail-card">
          <h3><Wallet size={18} /> Low Balance Monitoring</h3>
          <div className="alerts-detail-empty">
            <AlertCircle size={24} />
            <p>Balance risk analysis is not available yet.</p>
            <span>Projected balances and your safety threshold will be monitored here.</span>
          </div>
        </div>

        <div className="alerts-detail-card">
          <h3><CalendarClock size={18} /> Upcoming Payment Risks</h3>
          <div className="alerts-detail-empty">
            <CalendarClock size={24} />
            <p>No payment risk assessment available.</p>
            <span>Upcoming commitments will be evaluated against available cash.</span>
          </div>
        </div>

        <div className="alerts-detail-card">
          <h3><TrendingUp size={18} /> Overspending Detection</h3>
          <div className="alerts-detail-empty">
            <TrendingUp size={24} />
            <p>Spending analysis is awaiting data.</p>
            <span>Unusual spending and budget overruns will be highlighted here.</span>
          </div>
        </div>

        <div className="alerts-detail-card">
          <h3><Sparkles size={18} /> AI Risk Recommendations</h3>
          <div className="alerts-detail-empty">
            <Sparkles size={24} />
            <p>AI recommendations are not available yet.</p>
            <span>Personalized suggestions will be generated from identified financial risks.</span>
          </div>
        </div>
      </div>

      <div className="alerts-history">
        <div>
          <h3>Alert History</h3>
          <p>Review previously detected and resolved financial risks.</p>
        </div>
        <div className="alerts-history-empty">
          <Info size={20} />
          No alert history available yet.
        </div>
      </div>
    </div>
  );
}
