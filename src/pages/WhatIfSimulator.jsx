
import React, { useState } from "react";
import {
  SlidersHorizontal,
  TrendingUp,
  TrendingDown,
  Wallet,
  Sparkles,
  RotateCcw,
  ArrowRight,
  Info,
  PlusCircle
} from "lucide-react";

export default function WhatIfSimulator() {
  const [scenario, setScenario] = useState("expense");
  const [changeAmount, setChangeAmount] = useState("10");
  const [duration, setDuration] = useState("3");
  const [description, setDescription] = useState("");

  const [scenarios, setScenarios] = useState([]);

  function addScenario(e) {
    e.preventDefault();

    setScenarios([
      ...scenarios,
      {
        id: Date.now(),
        type: scenario,
        amount: Number(changeAmount),
        duration: Number(duration),
        description
      }
    ]);

    setDescription("");
  }

  function resetSimulator() {
    setScenarios([]);
    setScenario("expense");
    setChangeAmount("10");
    setDuration("3");
    setDescription("");
  }

  return (
    <div className="whatif-page">
      <div className="whatif-header">
        <div>
          <span className="whatif-eyebrow">
            FINANCIAL PLANNING / SCENARIO ANALYSIS
          </span>
          <h1>What-If Simulator</h1>
          <p>
            Explore hypothetical financial changes and understand
            how different decisions could affect your future cash flow.
          </p>
        </div>

        <button className="whatif-reset-button" onClick={resetSimulator}>
          <RotateCcw size={16} /> Reset scenarios
        </button>
      </div>

      <div className="whatif-info-banner">
        <Info size={20} />
        <div>
          <strong>Scenario planning workspace</strong>
          <p>
            Configure hypothetical financial changes below.
            Forecast results will appear once your real financial
            data and simulation engine are connected.
          </p>
        </div>
      </div>

      <div className="whatif-layout">
        <div className="whatif-config-card">
          <div className="whatif-card-heading">
            <div className="whatif-heading-icon">
              <SlidersHorizontal size={19} />
            </div>
            <div>
              <h3>Configure your scenario</h3>
              <p>Adjust the variables you want to explore.</p>
            </div>
          </div>

          <form onSubmit={addScenario}>
            <label className="whatif-label">
              What would you like to simulate?
            </label>

            <div className="whatif-scenario-options">
              <button
                type="button"
                className={scenario === "income" ? "selected" : ""}
                onClick={() => setScenario("income")}
              >
                <TrendingUp size={19} />
                <span>Income change</span>
                <small>Increase or decrease income</small>
              </button>

              <button
                type="button"
                className={scenario === "expense" ? "selected" : ""}
                onClick={() => setScenario("expense")}
              >
                <TrendingDown size={19} />
                <span>Expense change</span>
                <small>Adjust spending levels</small>
              </button>

              <button
                type="button"
                className={scenario === "unexpected" ? "selected" : ""}
                onClick={() => setScenario("unexpected")}
              >
                <Wallet size={19} />
                <span>Unexpected expense</span>
                <small>Plan for a sudden cost</small>
              </button>
            </div>

            <div className="whatif-field">
              <label className="whatif-label">
                {scenario === "unexpected"
                  ? "Unexpected expense amount (₹)"
                  : "Percentage change (%)"}
              </label>

              <div className="whatif-input-wrapper">
                <input
                  type="number"
                  min="0"
                  value={changeAmount}
                  onChange={e => setChangeAmount(e.target.value)}
                  required
                />
                <span>
                  {scenario === "unexpected" ? "INR" : "%"}
                </span>
              </div>
            </div>

            <div className="whatif-field">
              <label className="whatif-label">
                Simulation duration
              </label>
              <select
                value={duration}
                onChange={e => setDuration(e.target.value)}
              >
                <option value="1">1 month</option>
                <option value="3">3 months</option>
                <option value="6">6 months</option>
                <option value="12">12 months</option>
              </select>
            </div>

            <div className="whatif-field">
              <label className="whatif-label">
                Scenario description (optional)
              </label>
              <input
                type="text"
                placeholder="e.g. New monthly subscription"
                value={description}
                onChange={e => setDescription(e.target.value)}
              />
            </div>

            <button type="submit" className="whatif-add-button">
              <PlusCircle size={17} />
              Add scenario
            </button>
          </form>
        </div>

        <div className="whatif-results-column">
          <div className="whatif-result-card">
            <div className="whatif-result-heading">
              <div>
                <h3>Simulation Results</h3>
                <p>Projected impact of your scenarios</p>
              </div>
              <span className="whatif-pending-label">
                Awaiting analysis
              </span>
            </div>

            <div className="whatif-result-empty">
              <div className="whatif-result-icon">
                <TrendingUp size={32} />
              </div>
              <h3>No simulation results yet</h3>
              <p>
                Add a scenario and connect your financial data
                to generate projected cash-flow outcomes.
              </p>
            </div>

            <div className="whatif-metrics">
              <div>
                <span>Projected balance</span>
                <strong>--</strong>
              </div>
              <div>
                <span>Cash-flow impact</span>
                <strong>--</strong>
              </div>
              <div>
                <span>Shortfall probability</span>
                <strong>--</strong>
              </div>
            </div>
          </div>

          <div className="whatif-ai-card">
            <div className="whatif-ai-title">
              <Sparkles size={19} />
              <h3>AI Scenario Insights</h3>
            </div>
            <p>
              AI-generated explanations will help you understand
              the potential risks and opportunities of each
              financial scenario.
            </p>
            <span>Insights will be available after backend integration.</span>
          </div>
        </div>
      </div>

      <div className="whatif-scenarios-card">
        <div className="whatif-scenarios-heading">
          <div>
            <h3>Your Scenarios</h3>
            <p>Hypothetical changes configured in this session.</p>
          </div>
          <span>{scenarios.length} created</span>
        </div>

        {scenarios.length === 0 ? (
          <div className="whatif-list-empty">
            <SlidersHorizontal size={27} />
            <p>No scenarios have been created.</p>
            <span>
              Use the scenario builder to add your first simulation.
            </span>
          </div>
        ) : (
          <div className="whatif-scenario-list">
            {scenarios.map((item, index) => (
              <div className="whatif-scenario-row" key={item.id}>
                <div className="whatif-scenario-number">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className="whatif-scenario-description">
                  <strong>
                    {item.description ||
                      (item.type === "income"
                        ? "Income change"
                        : item.type === "expense"
                        ? "Expense change"
                        : "Unexpected expense")}
                  </strong>
                  <small>
                    {item.type === "unexpected"
                      ? `₹${item.amount.toLocaleString("en-IN")} unexpected expense`
                      : `${item.amount}% ${item.type} change`}
                    {" · "}
                    {item.duration} months
                  </small>
                </div>

                <span className="whatif-analysis-pending">
                  Analysis pending
                </span>

                <ArrowRight size={17} />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="whatif-bottom-note">
        <Info size={17} />
        <span>
          Scenario inputs are temporary and stored only in this
          browser session. No actual financial transactions are changed.
        </span>
      </div>
    </div>
  );
}
