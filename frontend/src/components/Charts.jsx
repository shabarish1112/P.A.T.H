import { memo } from 'react';

export const LineChart = memo(function LineChart({ points }) {
  if (!points?.length) return <div className="chart-empty">No trend data yet.</div>;
  const width = 720;
  const height = 220;
  const pad = 40;
  const max = Math.max(1, ...points.flatMap((point) => [point.current, point.previous]));
  const x = (index) => pad + (index * (width - pad * 2)) / Math.max(points.length - 1, 1);
  const y = (value) => height - pad - (value / max) * (height - pad * 2);
  const line = (key) => points.map((point, index) => `${x(index)},${y(point[key])}`).join(' ');
  return (
    <div
      className="chart-wrap"
      role="img"
      aria-label="Current and previous flagged transaction trend"
    >
      <svg viewBox={`0 0 ${width} ${height}`} className="line-chart">
        {[0, 0.5, 1].map((ratio) => (
          <g key={ratio}>
            <line
              x1={pad}
              y1={y(max * ratio)}
              x2={width - pad}
              y2={y(max * ratio)}
              className="grid-line"
            />
            <text x={pad - 8} y={y(max * ratio) + 4} textAnchor="end" className="chart-axis">
              {new Intl.NumberFormat('en-IN', { notation: 'compact' }).format(max * ratio)}
            </text>
          </g>
        ))}
        <polyline points={line('previous')} className="line previous" fill="none" />
        <polyline points={line('current')} className="line current" fill="none" />
        {points.map((point, index) => (
          <g key={point.bucket}>
            <circle cx={x(index)} cy={y(point.current)} r="8" fill="transparent">
              <title>{`${point.bucket}: Current ${point.current}, Previous ${point.previous}`}</title>
            </circle>
          </g>
        ))}
      </svg>
      <div className="chart-labels">
        {points.map((point) => (
          <span key={point.bucket}>{point.bucket}</span>
        ))}
      </div>
    </div>
  );
});
