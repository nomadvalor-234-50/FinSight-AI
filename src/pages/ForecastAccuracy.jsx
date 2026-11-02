
import React from "react";
import {
  Target, Activity, BarChart3, CalendarDays,
  TrendingUp, Info, Clock
} from "lucide-react";

export default function ForecastAccuracy() {
  return (
    <div className="remaining-page">
      <div className="remaining-header">
        <div>
          <span className="remaining-eyebrow">FORECASTING / PERFORMANCE</span>
          <h1>Forecast Accuracy</h1>
          <p>Evaluate how closely predicted cash flow matches actual financial outcomes.</p>
        </div>
        <span className="remaining-status">Data integration pending</span>
      </div>

      <div className="remaining-banner">
        <Info size={20}/>
        <div>
          <strong>Forecast evaluation workspace</strong>
          <p>Accuracy metrics require historical forecasts and actual transaction data. No accuracy scores are shown until those records are available.</p>
        </div>
      </div>

      <div className="accuracy-stats">
        <div className="remaining-stat">
          <span><Target size={17}/> Forecast Accuracy</span>
          <strong>--</strong>
          <small>Requires actual and predicted values</small>
        </div>
        <div className="remaining-stat">
          <span><Activity size={17}/> Forecast Error</span>
          <strong>--</strong>
          <small>Awaiting comparison data</small>
        </div>
        <div className="remaining-stat">
          <span><BarChart3 size={17}/> Forecast Records</span>
          <strong>--</strong>
          <small>Awaiting forecast history</small>
        </div>
        <div className="remaining-stat">
          <span><Clock size={17}/> Last Evaluation</span>
          <strong>--</strong>
          <small>No evaluation performed</small>
        </div>
      </div>

      <div className="remaining-panel">
        <div className="remaining-panel-heading">
          <div>
            <h3>Predicted vs Actual Cash Flow</h3>
            <p>Compare forecasted amounts with real financial outcomes.</p>
          </div>
          <CalendarDays size={19}/>
        </div>
        <div className="remaining-empty accuracy-chart-empty">
          <BarChart3 size={34}/>
          <h3>Comparison chart not available</h3>
          <p>Historical forecast and actual cash-flow records will appear here after backend integration.</p>
        </div>
      </div>

      <div className="remaining-grid">
        <div className="remaining-panel">
          <h3><TrendingUp size={18}/> Forecast Performance Trends</h3>
          <div className="remaining-empty">
            <p>Performance trends will appear after forecast evaluations are available.</p>
          </div>
        </div>
        <div className="remaining-panel">
          <h3><Target size={18}/> Error Analysis</h3>
          <div className="remaining-empty">
            <p>Forecast deviations and error patterns are awaiting actual data.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
