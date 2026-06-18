import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.fallback) return this.fallback;
      
      return (
        <div className="p-12 text-center bg-red-50 rounded-xl border border-red-200">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h2 className="text-xl font-bold text-red-900 mb-2">Something went wrong</h2>
          <p className="text-red-600 mb-6 max-w-md mx-auto">
            The application encountered an unexpected error. Please try refreshing the page or contact support if the issue persists.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md font-bold hover:bg-red-700 transition-colors"
          >
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh Page
          </button>
        </div>
      );
    }

    return this.children;
  }

  // Helper for type safety with optional children/fallback
  private get children() { return this.props.children; }
  private get fallback() { return this.props.fallback; }
}

export default ErrorBoundary;
