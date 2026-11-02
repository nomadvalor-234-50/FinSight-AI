import React from "react";
import { useLocation } from "react-router-dom";
import {
  LayoutDashboard, ReceiptText, CalendarClock, TrendingUp,
  Bell, Wallet, FlaskConical, Sparkles, ChartNoAxesCombined,
  Settings, Search, CalendarDays, Plus, Download,
  Landmark, ArrowDown, ArrowUp, ShieldCheck, Zap,
  Cloud, Building2, ChevronRight, Info, Menu, SlidersHorizontal
} from "lucide-react";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";

import "./App.css";
import RecurringPayments from "./pages/RecurringPayments";
import CashFlowForecast from "./pages/CashFlowForecast";
import FinancialAlerts from "./pages/FinancialAlerts";
import BudgetPlanner from "./pages/BudgetPlanner";
import WhatIfSimulator from "./pages/WhatIfSimulator";
import AIInsights from "./pages/AIInsights";
import ForecastAccuracy from "./pages/ForecastAccuracy";
import Login from "./pages/Login";
import Register from "./pages/Register";
import SettingsPage from "./pages/Settings";
import Transactions from "./pages/Transactions";

const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Transactions", icon: ReceiptText },
  { name: "Recurring Payments", icon: CalendarClock },
  { name: "Cash Flow Forecast", icon: TrendingUp },
  { name: "Financial Alerts", icon: Bell, count: 3 },
  { name: "Budget Planner", icon: Wallet },
  { name: "What-If Simulator", icon: FlaskConical },
  { name: "AI Insights", icon: Sparkles },
  { name: "Forecast Accuracy", icon: ChartNoAxesCombined },
  { name: "Settings", icon: Settings },
];

const chartData = [
  { date: "10 Oct", balance: 250000 },
  { date: "14 Oct", balance: 270000 },
  { date: "17 Oct", balance: 220000 },
  { date: "20 Oct", balance: 380000 },
  { date: "24 Oct", balance: 482450 },
  { date: "28 Oct", balance: 250000 },
  { date: "05 Nov", balance: 18200 },
  { date: "12 Nov", balance: 310000 },
  { date: "18 Nov", balance: 390000 },
  { date: "24 Nov", balance: 350000 },
];

const transactions = [
  { name: "Google Cloud Services", id: "TXN-89024", category: "Tech & Utility", date: "23 Oct 2024", method: "Corporate Card (•• 4012)", amount: "-₹8,490.00", status: "Cleared", type: "debit" },
  { name: "Client Retainer - Zepto Labs", id: "TXN-89012", category: "Consulting Income", date: "22 Oct 2024", method: "IMPS Bank Transfer", amount: "+₹75,000.00", status: "Settled", type: "credit" },
  { name: "Blue Tokai Coffee Roasters", id: "TXN-88941", category: "Food & Dining", date: "21 Oct 2024", method: "UPI (GPay)", amount: "-₹840.00", status: "Cleared", type: "debit" },
  { name: "AWS Web Services", id: "TXN-88890", category: "Cloud Hosting", date: "19 Oct 2024", method: "Debit Card (•• 1109)", amount: "-₹14,250.00", status: "Cleared", type: "debit" },
  { name: "Swiggy Instamart", id: "TXN-88805", category: "Groceries", date: "18 Oct 2024", method: "UPI (PhonePe)", amount: "-₹1,420.00", status: "Cleared", type: "debit" },
];

const commitments = [
  { name: "HDFC Home Loan EMI", date: "Due 5 Nov · Auto-debit active", amount: "₹38,500", icon: Building2 },
  { name: "Commercial Office Lease", date: "Due 7 Nov · Action Pending", amount: "₹45,000", icon: Building2, warning: true },
  { name: "Tata Power Electricity", date: "Due 8 Nov · Auto-pay scheduled", amount: "₹4,350", icon: Zap },
  { name: "AWS Cloud Infrastructure", date: "Due 11 Nov · Auto-debit", amount: "₹18,400", icon: Cloud },
];

function StatCard({ title, amount, note, icon: Icon, color, progress }) {
  return (
    <div className="stat-card">
      <div className="stat-heading">
        <span>{title}</span>
        <span className={`stat-icon ${color}`}><Icon size={19} /></span>
      </div>
      <h2>{amount}</h2>
      <div className="stat-note">{note}</div>
      <div className="progress-track">
        <div className={`progress-fill ${color}`} style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

function Sidebar({ active, setActive }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">F</div>
        <div><strong>FinSight AI</strong><small>TREASURY ENGINE</small></div>
      </div>
      <p className="nav-label">INTELLIGENCE & LEDGERS</p>
      <nav>
        {navigation.map(({ name, icon: Icon, count }) => (
          <button
            key={name}
            className={`nav-item ${active === name ? "active" : ""}`}
            onClick={() => setActive(name)}
          >
            <Icon size={17} />
            <span>{name}</span>
            {count && <span className="nav-count">{count}</span>}
          </button>
        ))}
      </nav>
      <div className="profile">
        <div className="avatar">AS</div>
        <div><strong>Aditya Sharma</strong><small>aditya@finsight.ai</small></div>
      </div>
    </aside>
  );
}

function App() {
  const [active, setActive] = React.useState("Overview");

  const currentPath = window.location.pathname;

  if (currentPath === "/login") {
    return <Login />;
  }

  if (currentPath === "/register") {
    return <Register />;
  }

  return (
    <div className="app-shell">
      <Sidebar active={active} setActive={setActive} />

      <main className="main-area">
      {active === "Transactions" ? (
  <div className="dashboard-content"><Transactions /></div>
) : active === "Recurring Payments" ? (
  <div className="dashboard-content"><RecurringPayments /></div>
) : active === "Cash Flow Forecast" ? (
  <div className="dashboard-content"><CashFlowForecast /></div>
) : active === "Financial Alerts" ? (
  <div className="dashboard-content"><FinancialAlerts /></div>
) : active === "Budget Planner" ? (
  <div className="dashboard-content">
    <BudgetPlanner />
  </div>
  ) : active === "What-If Simulator" ? (
  <div className="dashboard-content">
    <WhatIfSimulator />
  </div>
  ) : active === "AI Insights" ? (
  <div className="dashboard-content">
    <AIInsights />
  </div>
) : active === "Forecast Accuracy" ? (
  <div className="dashboard-content">
    <ForecastAccuracy />
  </div>
) : active === "Settings" ? (
  <div className="dashboard-content">
    <SettingsPage />
  </div>
) : (
        <>
        <header className="topbar">
          <div className="breadcrumb">Treasury <ChevronRight size={14} /> <strong>Console</strong></div>
          <div className="search-box"><Search size={17} /><input placeholder="Search transactions, alerts, or categories..." /></div>
          <div className="date-chip"><CalendarDays size={16} /> Thursday, 24 Oct 2024</div>
          <span className="currency-chip">₹ INR</span>
          <button className="notification"><Bell size={19} /><i /></button>
          <button className="primary-button"><Plus size={17} /> Quick Add Transaction</button>
          <div className="avatar top-avatar">AS</div>
        </header>

        <div className="dashboard-content">
          <section className="status-bar">
            <span className="engine-status"><i /> AI Cash Flow Engine: Operational</span>
            <span className="sync-text">Real-time sync · Reserve Model v4.2</span>
            <div className="filter-group">
              <button className="selected-filter">Last 30 Days</button>
              <button>Quarter-to-date</button>
              <button>Forecast 90D</button>
              <button><SlidersHorizontal size={14} /> Filters</button>
              <button><Download size={14} /> Report</button>
            </div>
          </section>

          <section className="stats-grid">
            <StatCard title="CURRENT BALANCE" amount="₹4,82,450" note={<><b className="positive">↗ +12.4%</b> vs last month</>} icon={Landmark} color="blue" progress={78} />
            <StatCard title="TOTAL MONTHLY INCOME" amount="₹1,85,000" note={<>Expected: ₹2,10,000 <b className="blue-text">88.1%</b></>} icon={ArrowDown} color="green" progress={88} />
            <StatCard title="TOTAL MONTHLY EXPENSES" amount="₹98,420" note={<>Remaining budget: <b className="green-text">₹41,580</b></>} icon={ArrowUp} color="dark" progress={65} />
            <StatCard title="EXPECTED SAVINGS" amount="₹86,580" note={<><ShieldCheck size={13} /> Projected EOM cash buffer</>} icon={Wallet} color="blue" progress={60} />
          </section>

          <section className="warning-banner">
            <div className="warning-symbol">♨</div>
            <div className="warning-copy">
              <h3>AI Early Warning: Projected cash balance risk in 12 days</h3>
              <span className="danger-label">DEFICIT HAZARD</span>
              <p>Upcoming obligations (HDFC Home Loan EMI ₹38,500 on Nov 5 & Office Rent ₹45,000 on Nov 7) coincide with delayed client receivables. Projected balance may dip to <strong className="red-text">₹18,200</strong>, significantly below your configured <b>₹50,000</b> safety floor.</p>
            </div>
            <div className="warning-actions">
              <button className="primary-button"><TrendingUp size={16} /> View Stress Timeline</button>
              <button className="secondary-button"><FlaskConical size={16} /> Simulate Scenarios</button>
            </div>
          </section>

          <section className="dashboard-columns">
            <div className="left-column">
              <div className="panel chart-panel">
                <div className="panel-heading">
                  <div><h3>30-Day Liquidity Trajectory & Forecast</h3><p>Historical clearance transitioned into neural probabilistic projection</p></div>
                  <span className="confidence">95% Confidence Band</span>
                </div>
                <div className="chart-legend">
                  <span><i className="legend-dot" /> Historical</span>
                  <span><i className="legend-line" /> Projected</span>
                  <span className="red-text">- Safe Floor (₹50k)</span>
                </div>
                <div className="chart-wrap">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 20, right: 12, left: 0, bottom: 5 }}>
                      <defs>
                        <linearGradient id="balanceFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#1555e8" stopOpacity={0.2} />
                          <stop offset="100%" stopColor="#1555e8" stopOpacity={0.01} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#e7edf8" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip formatter={(v) => `₹${Number(v).toLocaleString("en-IN")}`} />
                      <ReferenceLine y={50000} stroke="#ef4444" strokeDasharray="5 4" />
                      <Area type="monotone" dataKey="balance" stroke="#1555e8" strokeWidth={2.5} fill="url(#balanceFill)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="chart-foot"><span>10 Oct</span><span>17 Oct</span><b>24 Oct (Today)</b><span className="red-text">05 Nov</span><span>12 Nov</span><span>24 Nov</span></div>
              </div>

              <div className="panel transactions-panel">
                <div className="panel-heading">
                  <h3>Recent Treasury Transactions <span className="small-pill">5 New</span></h3>
                  <button className="text-button">View All Transactions →</button>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead><tr><th>TRANSACTION</th><th>CATEGORY</th><th>DATE</th><th>METHOD</th><th>AMOUNT</th><th>STATUS</th></tr></thead>
                    <tbody>
                      {transactions.map((t) => (
                        <tr key={t.id}>
                          <td><strong>{t.name}</strong><small>ID: {t.id}</small></td>
                          <td><span className="category-tag">{t.category}</span></td>
                          <td>{t.date}</td><td>{t.method}</td>
                          <td className={t.type === "credit" ? "green-text amount" : "amount"}>{t.amount}</td>
                          <td><span className={`status-pill ${t.type}`}>{t.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="right-column">
              <div className="panel health-panel">
                <h3>Financial Health <Info size={15} /></h3>
                <div className="health-content">
                  <div className="health-score"><strong>84</strong><small>/ 100</small></div>
                  <div><b>Healthy · Moderate Buffer</b><p>Liquid reserves adequate for seasonal baseline fluctuations.</p></div>
                </div>
                <div className="health-row"><span>Debt-to-Income</span><b>24% <em>(Optimal)</em></b></div>
                <div className="health-row"><span>Expense Coverage</span><b>4.8 months <em>(Target 6m)</em></b></div>
                <div className="health-row"><span>Recurring Commitments</span><b>42% of OpEx</b></div>
              </div>

              <div className="panel commitments-panel">
                <div className="panel-heading"><h3>Upcoming Commitments</h3><span className="days-pill">14 Days</span></div>
                {commitments.map(({ name, date, amount, icon: Icon, warning }) => (
                  <div className={`commitment ${warning ? "commitment-warning" : ""}`} key={name}>
                    <span className="commitment-icon"><Icon size={18} /></span>
                    <div><b>{name}</b><small>{date}</small></div>
                    <strong>{amount}</strong>
                  </div>
                ))}
              </div>

              <div className="panel snapshot-panel">
                <h4>FORECAST SNAPSHOT</h4>
                <div className="snapshot-tabs"><span>7D</span><span>14D</span><b>30D</b></div>
                <div className="snapshot-info"><span>Net Delta Expected:</span><strong>-₹12,400</strong></div>
                <div className="snapshot-info"><span>Safety Coverage:</span><b className="red-text">Vulnerable on Day 12</b></div>
                <p>AI Scenario Simulator</p>
                <button className="text-button">Test Deficit Adjustments →</button>
              </div>
            </div>
          </section>
                </div>
        </>
        )}
      </main>
    </div>
  );
}

export default App;
