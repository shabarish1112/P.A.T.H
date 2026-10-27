export const REVIEW_STATUSES = ['Pending Review', 'Confirmed Finding', 'False Alert', 'Escalated'];

export const RISK_LEVELS = ['Critical', 'High', 'Medium', 'Low', 'Normal'];

export const MODEL_OPTIONS = [
  { value: 'if', label: 'Isolation Forest' },
  { value: 'eif', label: 'EIF-lite' },
  { value: 'dif', label: 'DIF-lite' },
];

export const ROLE_CAPABILITIES = {
  analyst: { review: false, admin: false },
  reviewer: { review: true, admin: false },
  admin: { review: true, admin: true },
};

export const NAV_ITEMS = [
  { to: '/workspace', label: 'Overview', icon: 'overview' },
  { to: '/datasets', label: 'Datasets', icon: 'datasets', admin: true },
  { to: '/transactions', label: 'Transactions', icon: 'transactions' },
  { to: '/control', label: 'ML Control', icon: 'control' },
  { to: '/anomalies', label: 'Anomaly Explorer', icon: 'anomalies' },
  { to: '/investigation', label: 'Investigation', icon: 'investigation' },
  { to: '/analytics', label: 'Visual Analytics', icon: 'analytics' },
  { to: '/queue', label: 'Review history', icon: 'queue' },
  { to: '/admin', label: 'Access & Audit', icon: 'admin', admin: true },
];
