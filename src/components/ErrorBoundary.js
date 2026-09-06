import React from 'react';

export default class ErrorBoundary extends React.Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center p-6" role="alert">
        <div className="max-w-lg">
          <h1 className="text-2xl mb-4">This page ran into a problem</h1>
          <p className="text-white/70 mb-6">Reload the page to try again. Any unsaved changes may need to be entered again.</p>
          <button className="bg-emerald-400 text-black px-5 py-3 mr-5" onClick={() => window.location.reload()}>Reload page</button>
          <a href="/" className="underline">Go to home</a>
        </div>
      </div>
    );
  }
}
