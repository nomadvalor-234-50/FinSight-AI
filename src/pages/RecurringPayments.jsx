
import React, { useState } from "react";
import {
  CalendarClock, Search, Plus, RefreshCw, ArrowUpRight,
  CheckCircle2, AlertCircle, Clock, MoreHorizontal,
  Home, Zap, Cloud, CreditCard, ShieldCheck
} from "lucide-react";

const initialPayments = [
  { id: 1, name: "House Rent", category: "Housing", amount: 10000, frequency: "Monthly", nextDate: "05 Nov 2026", status: "Upcoming", icon: Home, color: "purple" },
  { id: 2, name: "Electricity Bill", category: "Utilities", amount: 1850, frequency: "Monthly", nextDate: "08 Nov 2026", status: "Upcoming", icon: Zap, color: "orange" },
  { id: 3, name: "AWS Cloud Services", category: "Technology", amount: 2499, frequency: "Monthly", nextDate: "10 Nov 2026", status: "Active", icon: Cloud, color: "blue" },
  { id: 4, name: "Netflix Subscription", category: "Entertainment", amount: 649, frequency: "Monthly", nextDate: "12 Nov 2026", status: "Active", icon: CreditCard, color: "red" },
  { id: 5, name: "Internet Connection", category: "Utilities", amount: 999, frequency: "Monthly", nextDate: "15 Nov 2026", status: "Active", icon: Zap, color: "green" },
  { id: 6, name: "Gym Membership", category: "Lifestyle", amount: 1500, frequency: "Monthly", nextDate: "20 Nov 2026", status: "Active", icon: CreditCard, color: "purple" },
];

const money = (amount) =>
  "₹" + amount.toLocaleString("en-IN");

export default function RecurringPayments() {
  const [payments, setPayments] = useState(initialPayments);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [showForm, setShowForm] = useState(false);
  const [newPayment, setNewPayment] = useState({
    name: "", category: "Utilities", amount: "", frequency: "Monthly", nextDate: ""
  });

  const total = payments.reduce((sum, p) => sum + p.amount, 0);
  const filtered = payments.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) &&
    (filter === "All" || p.status === filter)
  );

  function addPayment(e) {
    e.preventDefault();
    if (!newPayment.name || !newPayment.amount || !newPayment.nextDate) return;

    setPayments([
      ...payments,
      {
        ...newPayment,
        id: Date.now(),
        amount: Number(newPayment.amount),
        nextDate: new Date(newPayment.nextDate).toLocaleDateString("en-IN", {
          day: "2-digit", month: "short", year: "numeric"
        }),
        status: "Active",
        icon: CreditCard,
        color: "blue"
      }
    ]);

    setNewPayment({
      name: "", category: "Utilities", amount: "", frequency: "Monthly", nextDate: ""
    });
    setShowForm(false);
  }

  return (
    <div className="recurring-page">
      <div className="recurring-header">
        <div>
          <div className="page-eyebrow">FINANCIAL MANAGEMENT / COMMITMENTS</div>
          <h1>Recurring Payments</h1>
          <p>Track regular expenses, subscriptions and upcoming financial commitments.</p>
        </div>
        <button className="primary-button" onClick={() => setShowForm(!showForm)}>
          <Plus size={17} /> Add Recurring Payment
        </button>
      </div>

      <div className="recurring-stats">
        <div className="recurring-stat-card">
          <span>Total Monthly Commitments</span>
          <h2>{money(total)}</h2>
          <small><CalendarClock size={14} /> Across {payments.length} payments</small>
        </div>
        <div className="recurring-stat-card">
          <span>Active Payments</span>
          <h2>{payments.filter(p => p.status === "Active").length}</h2>
          <small><CheckCircle2 size={14} /> Currently monitored</small>
        </div>
        <div className="recurring-stat-card">
          <span>Upcoming Payments</span>
          <h2>{payments.filter(p => p.status === "Upcoming").length}</h2>
          <small><Clock size={14} /> Scheduled commitments</small>
        </div>
        <div className="recurring-stat-card">
          <span>Annual Commitment</span>
          <h2>{money(total * 12)}</h2>
          <small><ArrowUpRight size={14} /> Estimated yearly outflow</small>
        </div>
      </div>

      {showForm && (
        <form className="recurring-form" onSubmit={addPayment}>
          <h3>Add a recurring payment</h3>
          <div className="recurring-form-grid">
            <input
              placeholder="Payment name"
              value={newPayment.name}
              onChange={e => setNewPayment({...newPayment, name: e.target.value})}
              required
            />
            <select
              value={newPayment.category}
              onChange={e => setNewPayment({...newPayment, category: e.target.value})}
            >
              <option>Utilities</option>
              <option>Housing</option>
              <option>Technology</option>
              <option>Entertainment</option>
              <option>Lifestyle</option>
              <option>Other</option>
            </select>
            <input
              type="number"
              min="1"
              placeholder="Amount in ₹"
              value={newPayment.amount}
              onChange={e => setNewPayment({...newPayment, amount: e.target.value})}
              required
            />
            <select
              value={newPayment.frequency}
              onChange={e => setNewPayment({...newPayment, frequency: e.target.value})}
            >
              <option>Monthly</option>
              <option>Weekly</option>
              <option>Quarterly</option>
              <option>Yearly</option>
            </select>
            <input
              type="date"
              value={newPayment.nextDate}
              onChange={e => setNewPayment({...newPayment, nextDate: e.target.value})}
              required
            />
          </div>
          <div className="recurring-form-actions">
            <button type="button" className="secondary-button" onClick={() => setShowForm(false)}>Cancel</button>
            <button type="submit" className="primary-button">Save Payment</button>
          </div>
        </form>
      )}

      <div className="recurring-insight">
        <div className="insight-icon"><ShieldCheck size={22} /></div>
        <div>
          <strong>Recurring payment monitoring is active</strong>
          <p>FinSight AI tracks your regular commitments to help anticipate future cash outflows and potential balance risks.</p>
        </div>
      </div>

      <div className="recurring-table-card">
        <div className="recurring-table-heading">
          <div>
            <h3>All Recurring Payments</h3>
            <p>Review and manage your detected financial commitments.</p>
          </div>
          <div className="recurring-search">
            <Search size={16} />
            <input
              placeholder="Search payments..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="recurring-filters">
          {["All", "Active", "Upcoming"].map(item => (
            <button
              key={item}
              className={filter === item ? "recurring-filter active" : "recurring-filter"}
              onClick={() => setFilter(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>PAYMENT</th>
                <th>CATEGORY</th>
                <th>AMOUNT</th>
                <th>FREQUENCY</th>
                <th>NEXT PAYMENT</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(payment => {
                const Icon = payment.icon;
                return (
                  <tr key={payment.id}>
                    <td>
                      <div className="recurring-name">
                        <span className={`recurring-icon ${payment.color}`}><Icon size={18} /></span>
                        <strong>{payment.name}</strong>
                      </div>
                    </td>
                    <td>{payment.category}</td>
                    <td className="amount">{money(payment.amount)}</td>
                    <td>{payment.frequency}</td>
                    <td>{payment.nextDate}</td>
                    <td>
                      <span className={`recurring-status ${payment.status.toLowerCase()}`}>
                        {payment.status === "Upcoming" ? <Clock size={13} /> : <CheckCircle2 size={13} />}
                        {payment.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr><td colSpan="6" className="recurring-empty">No matching payments found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="recurring-table-footer">
          Showing {filtered.length} of {payments.length} recurring payments
        </div>
      </div>
    </div>
  );
}
