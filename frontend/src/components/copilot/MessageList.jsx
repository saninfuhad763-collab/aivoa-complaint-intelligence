import React from 'react';
import { useSelector } from 'react-redux';

const roleLabel = { user: 'You', assistant: 'Copilot', system: 'System' };

const BotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.5" className="message-empty-icon-svg"
    aria-hidden="true">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <line x1="12" y1="7" x2="12" y2="11" />
    <circle cx="8" cy="16" r="1" fill="currentColor" />
    <circle cx="16" cy="16" r="1" fill="currentColor" />
  </svg>
);

export default function MessageList() {
  const messages = useSelector((s) => s.copilot.messages);
  const copilotLoading = useSelector((s) => s.copilot.loading);
  const analysisLoading = useSelector((s) => s.complaints.analysisLoading);
  const isProcessing = copilotLoading || analysisLoading;

  const bottomRef = React.useRef(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  if (messages.length === 0 && !isProcessing) {
    return (
      <div className="message-empty" role="status">
        <div className="message-empty-icon">
          <BotIcon />
        </div>
        <div className="message-empty-title">AI Copilot</div>
        <div className="message-empty-sub">
          Paste complaint text or upload a PDF, then click{' '}
          <strong>Analyze Complaint</strong> to begin AI-assisted extraction.
        </div>
      </div>
    );
  }

  return (
    <div className="message-area" role="log" aria-label="Copilot conversation" aria-live="polite">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`message message-${msg.role}`}
          role="article"
          aria-label={`${roleLabel[msg.role] || msg.role} message`}
        >
          <div className="message-bubble">{msg.content}</div>
          <div className="message-meta">
            <span className="message-role">{roleLabel[msg.role] || msg.role}</span>
            <span>
              {msg.timestamp
                ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : ''}
            </span>
          </div>
        </div>
      ))}
      {isProcessing && (
        <div className="message message-assistant" role="article" aria-label="Copilot processing message">
          <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="btn-spinner" aria-hidden="true" style={{ width: 14, height: 14, borderWidth: 2 }} />
            <span>Analyzing complaint with AI Copilot…</span>
          </div>
          <div className="message-meta">
            <span className="message-role">Copilot</span>
            <span>Processing</span>
          </div>
        </div>
      )}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
