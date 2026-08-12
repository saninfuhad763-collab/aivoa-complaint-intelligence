import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { removeNotification } from '../../features/ui/uiSlice.js';

// Auto-dismiss durations by notification type (ms)
const DISMISS_DELAY = {
  success: 3000,
  info: 4000,
  warning: 5000,
  error: 7000,
};

function ToastItem({ notification, onDismiss }) {
  useEffect(() => {
    const delay = DISMISS_DELAY[notification.type] ?? 4000;
    const timer = setTimeout(() => onDismiss(notification.id), delay);
    return () => clearTimeout(timer);
  }, [notification.id, notification.type, onDismiss]);

  return (
    <div
      className={`notification notification-${notification.type}`}
      role="alert"
    >
      <span className="notification-message">{notification.message}</span>
      <button
        className="notification-close"
        onClick={() => onDismiss(notification.id)}
        aria-label="Dismiss notification"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

export default function AppShell({ children }) {
  const dispatch = useDispatch();
  const notifications = useSelector((s) => s.ui.notifications);

  const handleDismiss = React.useCallback(
    (id) => dispatch(removeNotification(id)),
    [dispatch]
  );

  return (
    <div className="app-shell">
      {/* ── Header ── */}
      <header className="app-header" role="banner">
        <div className="header-brand">
          {/* Logo mark */}
          <div className="header-logo-mark" aria-hidden="true">
            <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 1L2 5v6l6 4 6-4V5L8 1zm0 2.2l4 2.67v4.26L8 12.6 4 10.13V5.87L8 3.2z" />
            </svg>
          </div>
          <span className="header-title">AIVOA</span>
          <span className="header-subtitle">Complaint Intelligence</span>
        </div>

        <div className="header-right">
          <div className="status-indicator" role="status" aria-label="System online">
            <span className="status-dot" aria-hidden="true" />
            <span>System Online</span>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="workspace" role="main">
        {children}
      </main>

      {/* ── Toast Notifications ── */}
      <div
        className="notification-container"
        role="region"
        aria-label="Notifications"
        aria-live="polite"
      >
        {notifications.map((n) => (
          <ToastItem key={n.id} notification={n} onDismiss={handleDismiss} />
        ))}
      </div>
    </div>
  );
}
