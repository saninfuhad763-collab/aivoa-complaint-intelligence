import React, { useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setInput, addMessage, clearMessages, setLoading } from '../../features/copilot/copilotSlice.js';
import { analyzeComplaint } from '../../features/complaints/complaintSlice.js';
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
  const copilotLoading = useSelector((s) => s.copilot.loading);
  const analysisLoading = useSelector((s) => s.complaints.analysisLoading);
  const analysisResult = useSelector((s) => s.complaints.analysisResult);
  const messages = useSelector((s) => s.copilot.messages);
  const textareaRef = useRef(null);

  const isProcessing = copilotLoading || analysisLoading;

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

  const performAnalysis = async (textToAnalyze, sourceType = 'text') => {
    if (isProcessing) return;

    dispatch(setLoading(true));

    const actionResult = await dispatch(
      analyzeComplaint({ input_text: textToAnalyze, source_type: sourceType })
    );

    dispatch(setLoading(false));

    if (analyzeComplaint.fulfilled.match(actionResult)) {
      const res = actionResult.payload;
      const confPct = res.confidence != null ? Math.round(res.confidence * 100) : null;
      const confStr = confPct !== null ? ` (${confPct}% confidence)` : '';

      let summary = `Analysis complete${confStr}. Extracted fields populated in complaint form.`;
      if (res.missing_fields && res.missing_fields.length > 0) {
        summary += ` Missing fields: ${res.missing_fields.join(', ')}.`;
      }

      dispatch(addMessage({
        role: 'assistant',
        content: summary,
      }));

      dispatch(addNotification({
        type: 'success',
        message: 'AI complaint analysis completed successfully.',
      }));
    } else {
      const errMsg = actionResult.payload || 'Failed to analyze complaint.';
      dispatch(addMessage({
        role: 'system',
        content: `Analysis error: ${errMsg}`,
      }));
      dispatch(addNotification({
        type: 'error',
        message: errMsg,
      }));
    }
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text || isProcessing) return;

    dispatch(addMessage({ role: 'user', content: text }));
    dispatch(setInput(''));
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    performAnalysis(text, 'text');
  };

  const handleAnalyze = () => {
    const text = input.trim();
    // If textarea is empty and a prior analysis already exists, block redundant re-analysis.
    if (!text && analysisResult) {
      dispatch(addNotification({
        type: 'info',
        message: 'Complaint already analyzed. Edit the form or paste new text to re-analyze.',
      }));
      return;
    }
    if (text) {
      dispatch(addMessage({ role: 'user', content: text }));
      dispatch(setInput(''));
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
      performAnalysis(text, 'text');
    } else {
      // Use latest user message from conversation if input is empty
      const userMsgs = messages.filter((m) => m.role === 'user');
      if (userMsgs.length > 0) {
        const lastText = userMsgs[userMsgs.length - 1].content;
        performAnalysis(lastText, 'text');
      } else {
        dispatch(addNotification({
          type: 'warning',
          message: 'Please enter or paste complaint text before analyzing.',
        }));
      }
    }
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
          disabled={isProcessing}
        />
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={handleSend}
          disabled={!input.trim() || isProcessing}
          aria-label="Send message"
        >
          {isProcessing ? (
            <span className="btn-spinner" aria-hidden="true" />
          ) : (
            <SendIcon />
          )}
          Send
        </button>
      </div>

      <div className="copilot-action-row">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handleAnalyze}
          disabled={isProcessing}
          aria-label="Analyze complaint"
          style={{ flex: 1 }}
        >
          {isProcessing ? (
            <span className="btn-spinner" aria-hidden="true" />
          ) : (
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          )}
          {isProcessing ? 'Analyzing…' : 'Analyze Complaint'}
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => dispatch(clearMessages())}
          disabled={isProcessing}
          aria-label="Clear conversation"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
