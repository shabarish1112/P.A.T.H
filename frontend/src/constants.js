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
