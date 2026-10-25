import { render, screen, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ExplanationText, SignalEvidence } from '../src/components/PaymentExplanation';
import { formatPaymentDate } from '../src/lib';
import record from './fixtures/investigation.json';

afterEach(cleanup);

describe('plain-language payment evidence', () => {
  it('renders the shared headline, action, merged rows, units and low frequency', () => {
    render(
      <>
        <ExplanationText explanation={record.explanation} />
        <SignalEvidence signals={record.explanation.signals} />
      </>,
    );
    expect(screen.getByText(record.explanation.headline)).toBeInTheDocument();
    expect(screen.getByText(record.explanation.check_first)).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: 'Typical agency and scheme payment' }),
    ).toBeInTheDocument();
    expect(screen.getByText('About 7.7x')).toBeInTheDocument();
    expect(screen.getByText('1 payment')).toBeInTheDocument();
    expect(screen.getByText('First payment on record')).toBeInTheDocument();
    expect(screen.getByText('6.3%')).toBeInTheDocument();
    expect(screen.queryByText('Amount Relative To Vendor Average')).not.toBeInTheDocument();
  });

  it('uses a clear unavailable state and never changes a date-only calendar day', () => {
    render(<ExplanationText />);
    expect(screen.getByText(/No explanation is available/)).toBeInTheDocument();
    expect(formatPaymentDate('2024-04-14')).toBe('14 Apr 2024');
    expect(formatPaymentDate('2024-04-14T00:00:00Z')).toBe('14 Apr 2024');
    expect(formatPaymentDate(null)).toBe('Date unavailable');
    expect(formatPaymentDate('not-a-date')).toBe('Date unavailable');
  });
});
