import React from 'react';
import './LoadingState.css';

export function LoadingState({ message = 'Loading repair records...' }) {
  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <span className="loading-text">{message}</span>
    </div>
  );
}

export default LoadingState;
