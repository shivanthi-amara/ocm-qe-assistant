import React from 'react';

import { Alert, EmptyState } from '@patternfly/react-core';
import * as Sentry from '@sentry/browser';

type Props = {
  children: React.ReactNode;
};

type State = {
  error?: string;
  componentStack?: string;
};

class ErrorBoundary extends React.Component<Props, State> {
  state: State = {};

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    this.setState({ error: error.toString(), componentStack: info.componentStack ?? undefined });
    Sentry.withScope((scope) => {
      scope.setExtras({
        componentStack: info.componentStack,
      });
      Sentry.captureException(error);
    });
  }

  render() {
    const { error, componentStack } = this.state;
    if (error) {
      return (
        // Fallback UI
        <EmptyState>
          <Alert variant="danger" isInline title="Something went wrong">
            <div style={{ whiteSpace: 'pre-wrap', textAlign: 'left', fontFamily: 'monospace' }}>
              {error}
              {componentStack}
            </div>
          </Alert>
        </EmptyState>
      );
    }

    const { children } = this.props;
    return children;
  }
}

export default ErrorBoundary;
