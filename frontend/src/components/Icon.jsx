const paths = {
  overview: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  datasets: 'M3 6c0-4 18-4 18 0s-18 4-18 0 M3 6v12c0 4 18 4 18 0V6 M3 12c0 4 18 4 18 0',
  transactions: 'M3 4h18v16H3z M3 9h18 M9 9v11 M3 14h18',
  control:
    'M8 3a4 4 0 0 0-4 6 4 4 0 0 0 0 7 4 4 0 0 0 8 3V5a3 3 0 0 0-4-2 M16 3a4 4 0 0 1 4 6 4 4 0 0 1 0 7 4 4 0 0 1-8 3 M6 9h3 M15 15h3',
  anomalies: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6 M7 10h6 M10 7v6',
  investigation: 'M14 2H5v20h14V7z M14 2v6h5 M8 12h5 M8 16h5',
  analytics: 'M3 3v18h18 M7 16v-5 M12 16V7 M17 16V4',
  queue: 'M9 5h12 M9 12h12 M9 19h12 M2 5l2 2 3-4 M2 12l2 2 3-4 M2 19l2 2 3-4',
  admin: 'M12 2l9 4v6c0 5-9 10-9 10S3 17 3 12V6z M8 12l3 3 5-6',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14 M15 15l6 6',
  user: 'M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M4 21v-3a8 6 0 0 1 16 0v3',
  sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M12 1v3 M12 20v3 M1 12h3 M20 12h3 M4 4l2 2 M18 18l2 2 M4 20l2-2 M18 6l2-2',
  moon: 'M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11',
};

export function Icon({ name, size = 18 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] || paths.overview} />
    </svg>
  );
}
