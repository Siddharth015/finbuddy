import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Stops a single render error from white-screening the whole Mini App. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("FinBuddy crashed:", error, info);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="app">
          <div className="state-block">
            <div className="state-emoji">😵</div>
            <div className="state-title">Something went wrong</div>
            <p className="muted state-hint">
              The app hit an unexpected error. Reload to try again.
            </p>
            <button
              className="primary"
              style={{ maxWidth: 200 }}
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
