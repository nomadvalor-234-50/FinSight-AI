
import React from "react";
import {
  Sparkles, Brain, TrendingUp, ShieldAlert,
  Lightbulb, RefreshCw, Info
} from "lucide-react";

export default function AIInsights() {
  return (
    <div className="remaining-page">
      <div className="remaining-header">
        <div>
          <span className="remaining-eyebrow">INTELLIGENCE / ANALYSIS</span>
          <h1>AI Financial Insights</h1>
          <p>Understand your financial patterns through explainable AI analysis.</p>
        </div>
        <span className="remaining-status"><Sparkles size={14}/> AI analysis pending</span>
      </div>

      <div className="remaining-banner">
        <Info size={20}/>
        <div>
          <strong>Your AI insights workspace is ready</strong>
          <p>Insights will be generated after real transaction, income, expense and forecast data is connected.</p>
        </div>
      </div>

      <div className="remaining-grid">
        <div className="remaining-card">
          <Sparkles/>
          <h3>Personalized Financial Insights</h3>
          <p>AI will identify meaningful patterns in your financial activity and explain why they matter.</p>
          <span>Awaiting financial data</span>
        </div>
        <div className="remaining-card">
          <TrendingUp/>
          <h3>Spending Pattern Analysis</h3>
          <p>Discover changes in spending behaviour and categories that may need attention.</p>
          <span>Awaiting transaction history</span>
        </div>
        <div className="remaining-card">
          <ShieldAlert/>
          <h3>Financial Risk Detection</h3>
          <p>Understand potential cash shortages, unusual spending and upcoming financial pressure.</p>
          <span>Awaiting forecast data</span>
        </div>
        <div className="remaining-card">
          <Lightbulb/>
          <h3>Smart Recommendations</h3>
          <p>Receive explainable suggestions to improve budgeting and financial stability.</p>
          <span>Awaiting AI analysis</span>
        </div>
      </div>

      <div className="remaining-panel">
        <h3><Brain size={19}/> AI Explanation Centre</h3>
        <div className="remaining-empty">
          <Sparkles size={30}/>
          <h3>No AI explanations available yet</h3>
          <p>When the analysis engine is connected, each insight will include its supporting financial data, reasoning and recommended action.</p>
        </div>
      </div>

      <div className="remaining-panel">
        <h3><RefreshCw size={18}/> Recent Insight History</h3>
        <div className="remaining-empty">
          <p>No generated insights to display.</p>
        </div>
      </div>
    </div>
  );
}
