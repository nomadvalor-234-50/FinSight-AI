
import React, { useState } from "react";
import {
  Search, Plus, Download, Upload, Filter,
  ArrowUpRight, ArrowDownRight, ReceiptText,
  MoreHorizontal, CalendarDays
} from "lucide-react";

const transactionData = [
  { id: "TXN-89024", name: "Google Cloud Services", category: "Technology", date: "24 Oct 2026", method: "Corporate Card", amount: 8490, type: "Expense", status: "Completed" },
  { id: "TXN-89012", name: "Client Retainer - Zepto Labs", category: "Income", date: "23 Oct 2026", method: "Bank Transfer", amount: 75000, type: "Income", status: "Completed" },
  { id: "TXN-88941", name: "Blue Tokai Coffee", category: "Food & Dining", date: "22 Oct 2026", method: "UPI", amount: 840, type: "Expense", status: "Completed" },
  { id: "TXN-88890", name: "AWS Web Services", category: "Technology", date: "20 Oct 2026", method: "Debit Card", amount: 14250, type: "Expense", status: "Completed" },
  { id: "TXN-88805", name: "Swiggy Instamart", category: "Groceries", date: "19 Oct 2026", method: "UPI", amount: 1420, type: "Expense", status: "Pending" },
  { id: "TXN-88752", name: "Monthly Salary", category: "Income", date: "18 Oct 2026", method: "Bank Transfer", amount: 85000, type: "Income", status: "Completed" },
  { id: "TXN-88710", name: "Office Rent", category: "Housing", date: "17 Oct 2026", method: "Bank Transfer", amount: 25000, type: "Expense", status: "Completed" },
];

const money = (amount) =>
  "₹" + amount.toLocaleString("en-IN");

function Transactions() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [transactions, setTransactions] = useState(transactionData);
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newAmount, setNewAmount] = useState("");
  const [newType, setNewType] = useState("Expense");

  const filtered = transactions.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.category.toLowerCase().includes(search.toLowerCase());

    const matchesFilter = filter === "All" || t.type === filter;
    return matchesSearch && matchesFilter;
  });

  const income = transactions
    .filter(t => t.type === "Income")
    .reduce((sum, t) => sum + t.amount, 0);

  const expenses = transactions
    .filter(t => t.type === "Expense")
    .reduce((sum, t) => sum + t.amount, 0);

  const addTransaction = (e) => {
    e.preventDefault();

    if (!newName.trim() || Number(newAmount) <= 0) return;

    setTransactions([
      {
        id: "TXN-" + Date.now().toString().slice(-6),
        name: newName,
        category: "Other",
        date: new Date().toLocaleDateString("en-IN"),
        method: "Manual Entry",
        amount: Number(newAmount),
        type: newType,
        status: "Completed",
      },
      ...transactions,
    ]);

    setNewName("");
    setNewAmount("");
    setShowForm(false);
  };

  return (
    <div className="transactions-page">
      <div className="transaction-heading">
        <div>
          <span className="page-breadcrumb">Treasury / Transactions</span>
          <h1>Transactions</h1>
          <p>Track, manage and analyse all your financial transactions.</p>
        </div>
        <div className="transaction-actions">
          <button className="transaction-outline"><Download size={16}/> Export</button>
          <button className="transaction-outline"><Upload size={16}/> Import CSV</button>
          <button className="transaction-primary" onClick={() => setShowForm(!showForm)}>
            <Plus size={17}/> Add Transaction
          </button>
        </div>
      </div>

      {showForm && (
        <form className="transaction-form" onSubmit={addTransaction}>
          <h3>Add New Transaction</h3>
          <input
            placeholder="Transaction description"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Amount in INR"
            min="1"
            value={newAmount}
            onChange={e => setNewAmount(e.target.value)}
            required
          />
          <select value={newType} onChange={e => setNewType(e.target.value)}>
            <option>Expense</option>
            <option>Income</option>
          </select>
          <button className="transaction-primary" type="submit">Save Transaction</button>
        </form>
      )}

      <div className="transaction-stats">
        <div className="transaction-stat">
          <div className="transaction-stat-icon purple"><ReceiptText/></div>
          <span>Total Transactions</span>
          <h2>{transactions.length}</h2>
          <small>Recorded transactions</small>
        </div>
        <div className="transaction-stat">
          <div className="transaction-stat-icon green"><ArrowDownRight/></div>
          <span>Total Income</span>
          <h2>{money(income)}</h2>
          <small className="income-text">Money received</small>
        </div>
        <div className="transaction-stat">
          <div className="transaction-stat-icon orange"><ArrowUpRight/></div>
          <span>Total Expenses</span>
          <h2>{money(expenses)}</h2>
          <small>Money spent</small>
        </div>
        <div className="transaction-stat">
          <div className="transaction-stat-icon blue"><ReceiptText/></div>
          <span>Net Cash Flow</span>
          <h2 className={income-expenses >= 0 ? "income-text" : "expense-text"}>
            {money(income-expenses)}
          </h2>
          <small>Income minus expenses</small>
        </div>
      </div>

      <div className="transaction-table-card">
        <div className="transaction-table-heading">
          <div>
            <h3>All Transactions</h3>
            <p>View and manage your financial activity</p>
          </div>
          <button className="transaction-outline"><CalendarDays size={15}/> Date Range</button>
        </div>

        <div className="transaction-toolbar">
          <div className="transaction-search">
            <Search size={17}/>
            <input
              placeholder="Search transactions..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="transaction-filters">
            {["All", "Income", "Expense"].map(item => (
              <button
                key={item}
                className={filter === item ? "filter-active" : ""}
                onClick={() => setFilter(item)}
              >
                {item}
              </button>
            ))}
            <button className="transaction-outline"><Filter size={15}/> Filter</button>
          </div>
        </div>

        <div className="transaction-table-scroll">
          <table className="transaction-table">
            <thead>
              <tr>
                <th>TRANSACTION</th>
                <th>CATEGORY</th>
                <th>DATE</th>
                <th>PAYMENT METHOD</th>
                <th>AMOUNT</th>
                <th>STATUS</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id}>
                  <td>
                    <strong>{t.name}</strong>
                    <small>{t.id}</small>
                  </td>
                  <td><span className="transaction-category">{t.category}</span></td>
                  <td>{t.date}</td>
                  <td>{t.method}</td>
                  <td className={t.type === "Income" ? "income-text" : "expense-text"}>
                    {t.type === "Income" ? "+" : "-"}{money(t.amount)}
                  </td>
                  <td>
                    <span className={`transaction-status ${t.status === "Pending" ? "pending" : "completed"}`}>
                      {t.status}
                    </span>
                  </td>
                  <td><button className="more-button"><MoreHorizontal size={18}/></button></td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan="7" className="empty-transactions">No transactions found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="transaction-footer">
          Showing {filtered.length} of {transactions.length} transactions
        </div>
      </div>
    </div>
  );
}

export default Transactions;
