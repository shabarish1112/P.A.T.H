export function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function ReviewBadge({ status = 'Pending Review' }) {
  const tone = status === 'Escalated' ? 'warning' : status === 'False Alert' ? 'muted' : 'neutral';
  return <Badge tone={tone}>{status}</Badge>;
}
