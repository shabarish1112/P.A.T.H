const meta = {
  Critical: { icon: '◆', className: 'risk-critical' },
  High: { icon: '▲', className: 'risk-high' },
  Medium: { icon: '●', className: 'risk-medium' },
  Low: { icon: '■', className: 'risk-low' },
  Normal: { icon: '○', className: 'risk-normal' },
};

export function RiskBadge({ risk = 'Normal' }) {
  const item = meta[risk] || meta.Normal;
  return (
    <span className={`risk-badge ${item.className}`} aria-label={`Risk level ${risk}`}>
      <span aria-hidden="true">{item.icon}</span> {risk}
    </span>
  );
}
