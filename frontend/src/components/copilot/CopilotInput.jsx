import React, { useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setInput, addMessage, clearMessages } from '../../features/copilot/copilotSlice.js';
import { addNotification } from '../../features/ui/uiSlice.js';

const SendIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

export default function CopilotInput() {
  const dispatch = useDispatch();
  const input = useSelector((s) => s.copilot.input);
  const loading = useSelector((s) => s.copilot.loading);
  const textareaRef = useRef(null);

  const handleInputChange = (e) => {
    dispatch(setInput(e.target.value));
    // Auto-resize
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    dispatch(addMessage({ role: 'user', content: text }));
    dispatch(setInput(''));
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    // UI-only placeholder response — AI integration in next phase
    setTimeout(() => {
      dispatch(addMessage({
        role: 'system',
        content: 'AI analysis is not yet connected. This will be implemented in the LangGraph/Groq integration phase.',
      }));
    }, 400);
  };

  const handleAnalyze = () => {
    dispatch(addNotification({
      type: 'info',
      message: 'AI analysis will be available after LangGraph/Groq integration.',
    }));
    dispatch(addMessage({
      role: 'system',
      content: 'AI extraction is coming in the next phase. Paste complaint text or upload a PDF to prepare.',
    }));
  };

  return (
    <div className="copilot-input-section">
      <div className="copilot-input-row">
        <textarea
          ref={textareaRef}
          className="copilot-textarea"
          placeholder="Type a message or paste complaint text…"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          rows={1}
          aria-label="Copilot message input"
          aria-multiline="true"
        />
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={handleSend}
          disabled={!input.trim() || loading}
          aria-label="Send message"
        >
          <SendIcon />
          Send
        </button>
      </div>

      <div className="copilot-action-row">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handleAnalyze}
          disabled={loading}
          aria-label="Analyze complaint"
          style={{ flex: 1 }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Analyze Complaint
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => dispatch(clearMessages())}
          disabled={loading}
          aria-label="Clear conversation"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
