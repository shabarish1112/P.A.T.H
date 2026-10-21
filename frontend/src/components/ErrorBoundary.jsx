import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('UI error boundary', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="center-screen">
          <section className="panel error-panel" role="alert">
            <p className="eyebrow">Interface error</p>
            <h1>P.A.T.H. could not render this view.</h1>
            <p className="muted">
              Your data has not been changed. Reload the page to restore the interface.
            </p>
            <button
              className="button primary"
              onClick={() => window.location.assign('/')}
              type="button"
            >
              Return to dashboard
            </button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}
