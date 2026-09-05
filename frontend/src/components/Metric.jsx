import React from 'react';
import './Metric.css';

export function Metric({ label, value, subtitle, trend, trendType = 'neutral', icon }) {
  return (
    <div className="metric-card">
      <div className="metric-header">
        <span className="metric-label">{label}</span>
        {icon && <div className="metric-icon-wrap">{icon}</div>}
      </div>
      <div className="metric-value-row">
        <span className="metric-value">{value}</span>
        {trend && (
          <span className={`metric-trend ${trendType}`}>
            {trend}
          </span>
        )}
      </div>
      {subtitle && <p className="metric-subtitle">{subtitle}</p>}
    </div>
  );
}

export default Metric;
