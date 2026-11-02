
import React, { useState } from "react";
import {
  Wallet, Plus, CalendarDays, Target, TrendingUp,
  AlertTriangle, Sparkles, Utensils, Home,
  Car, Zap, ShoppingBag, HeartPulse, MoreHorizontal
} from "lucide-react";

export default function BudgetPlanner() {
  const [period, setPeriod] = useState("Monthly");
  const [showForm, setShowForm] = useState(false);
  const [budgets, setBudgets] = useState([]);
  const [newBudget, setNewBudget] = useState({
    category: "",
    amount: "",
    period: "Monthly"
  });

  const totalBudget = budgets.reduce(
    (sum, item) => sum + item.amount, 0
  );

  function addBudget(e) {
    e.preventDefault();

    if (!newBudget.category || !newBudget.amount) return;

    setBudgets([
      ...budgets,
      {
        id: Date.now(),
        category: newBudget.category,
        amount: Number(newBudget.amount),
        spent: null,
        period: newBudget.period
      }
    ]);

    setNewBudget({
      category: "",
      amount: "",
      period: "Monthly"
    });

    setShowForm(false);
  }

  const categoryIcons = {
    Housing: Home,
    Food: Utensils,
    Transport: Car,
    Utilities: Zap,
    Shopping: ShoppingBag,
    Healthcare: HeartPulse
  };

  return (
    <div className="budget-page">
      <div className="budget-header">
        <div>
          <span className="budget-eyebrow">
            FINANCIAL MANAGEMENT / PLANNING
          </span>
          <h1>Budget Planner</h1>
          <p>
            Plan your spending, set category budgets and monitor your
            financial goals.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() => setShowForm(!showForm)}
        >
          <Plus size={17} /> Create Budget
        </button>
      </div>

      <div className="budget-notice">
        <Wallet size={21} />
        <div>
          <strong>Budget planning workspace</strong>
          <p>
            Create your budget allocations below. Actual spending,
            remaining balances and overspending analysis will be
            available after financial data integration.
          </p>
        </div>
      </div>

      <div className="budget-stats">
        <div className="budget-stat-card">
          <span><Wallet size={17} /> Total Allocated Budget</span>
          <h2>
            {budgets.length
              ? "₹" + totalBudget.toLocaleString("en-IN")
              : "--"}
          </h2>
          <small>
            {budgets.length
              ? `${budgets.length} budget allocations created`
              : "No budgets created yet"}
          </small>
        </div>

        <div className="budget-stat-card">
          <span><TrendingUp size={17} /> Actual Spending</span>
          <h2>--</h2>
          <small>Awaiting transaction data</small>
        </div>

        <div className="budget-stat-card">
          <span><Target size={17} /> Remaining Budget</span>
          <h2>--</h2>
          <small>Requires actual spending data</small>
        </div>

        <div className="budget-stat-card">
          <span><AlertTriangle size={17} /> Budget Warnings</span>
          <h2>--</h2>
          <small>Awaiting spending analysis</small>
        </div>
      </div>

      {showForm && (
        <form className="budget-form" onSubmit={addBudget}>
          <h3>Create a category budget</h3>

          <div className="budget-form-grid">
            <select
              value={newBudget.category}
              onChange={e =>
                setNewBudget({
                  ...newBudget,
                  category: e.target.value
                })
              }
              required
            >
              <option value="">Select category</option>
              <option>Housing</option>
              <option>Food</option>
              <option>Transport</option>
              <option>Utilities</option>
              <option>Shopping</option>
              <option>Healthcare</option>
              <option>Other</option>
            </select>

            <input
              type="number"
              min="1"
              placeholder="Budget amount (₹)"
              value={newBudget.amount}
              onChange={e =>
                setNewBudget({
                  ...newBudget,
                  amount: e.target.value
                })
              }
              required
            />

            <select
              value={newBudget.period}
              onChange={e =>
                setNewBudget({
                  ...newBudget,
                  period: e.target.value
                })
              }
            >
              <option>Weekly</option>
              <option>Monthly</option>
              <option>Quarterly</option>
              <option>Yearly</option>
            </select>
          </div>

          <div className="budget-form-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </button>
            <button type="submit" className="primary-button">
              Save Budget
            </button>
          </div>
        </form>
      )}

      <div className="budget-section">
        <div className="budget-section-heading">
          <div>
            <h3>Category Budget Allocations</h3>
            <p>Manage the amount you plan to spend in each category.</p>
          </div>

          <div className="budget-period">
            <CalendarDays size={16} />
            <select
              value={period}
              onChange={e => setPeriod(e.target.value)}
            >
              <option>Weekly</option>
              <option>Monthly</option>
              <option>Quarterly</option>
              <option>Yearly</option>
            </select>
          </div>
        </div>

        {budgets.filter(item => item.period === period).length === 0 ? (
          <div className="budget-empty">
            <div className="budget-empty-icon">
              <Target size={34} />
            </div>
            <h3>No budget allocations yet</h3>
            <p>
              Create your first category budget to start organizing
              your financial plan.
            </p>
            <button
              className="primary-button"
              onClick={() => {
                setNewBudget({ ...newBudget, period });
                setShowForm(true);
              }}
            >
              <Plus size={16} /> Create Your First Budget
            </button>
          </div>
        ) : (
          <div className="budget-category-list">
            {budgets
              .filter(item => item.period === period)
              .map(item => {
                const Icon = categoryIcons[item.category] || MoreHorizontal;

                return (
                  <div className="budget-category-card" key={item.id}>
                    <span className="budget-category-icon">
                      <Icon size={20} />
                    </span>

                    <div className="budget-category-details">
                      <strong>{item.category}</strong>
                      <small>Actual spending not connected</small>
                    </div>

                    <div className="budget-category-amount">
                      <strong>
                        ₹{item.amount.toLocaleString("en-IN")}
                      </strong>
                      <small>Allocated budget</small>
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>

      <div className="budget-bottom-grid">
        <div className="budget-detail-card">
          <h3><AlertTriangle size={18} /> Overspending Monitor</h3>
          <div className="budget-detail-empty">
            <p>Spending analysis is not available yet.</p>
            <span>
              Category spending will be compared against your
              allocated budgets after transaction integration.
            </span>
          </div>
        </div>

        <div className="budget-detail-card">
          <h3><Sparkles size={18} /> AI Budget Recommendations</h3>
          <div className="budget-detail-empty">
            <p>No recommendations available yet.</p>
            <span>
              AI will suggest budget adjustments based on your
              actual income and spending patterns.
            </span>
          </div>
        </div>
      </div>

      <div className="budget-goal-card">
        <div className="budget-goal-icon">
          <Target size={22} />
        </div>
        <div>
          <h3>Financial Goals</h3>
          <p>
            Savings targets and goal tracking will be available
            when financial information is connected.
          </p>
          <span>Goal tracking awaiting financial data</span>
        </div>
      </div>
    </div>
  );
}
