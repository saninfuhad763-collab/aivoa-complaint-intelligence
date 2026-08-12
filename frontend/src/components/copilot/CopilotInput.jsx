import React, { useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setInput, addMessage, clearMessages, setLoading } from '../../features/copilot/copilotSlice.js';
import { analyzeComplaint, patchAnalysisResult } from '../../features/complaints/complaintSlice.js';
import { patchMissingFields } from '../../features/risk/riskSlice.js';
import { addNotification } from '../../features/ui/uiSlice.js';

/**
 * CopilotInput
 *
 * Two distinct modes:
 *
 * INITIAL ANALYSIS — "Analyze Complaint" button
 *   → dispatches analyzeComplaint (POST /api/complaints/analyze)
 *   → overwrites analysisResult, riskAssessment, form
 *   → unchanged from previous behavior
 *
 * FOLLOW-UP — "Send" button / Enter key (when analysisResult already exists)
 *   → does NOT call analyzeComplaint
 *   → does NOT overwrite analysisResult or riskAssessment
 *   → either parses an explicit field correction and patches Redux state,
 *     or responds conversationally using the current complaint context
 *
 * FIRST MESSAGE — "Send" button when no prior analysisResult exists
 *   → falls back to the same full analysis flow as "Analyze Complaint"
 *     so the first paste-and-send still works naturally
 */

const SendIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

// ---------------------------------------------------------------------------
// CORE COMPLAINT FIELDS (mirrors backend CORE_COMPLAINT_FIELDS exactly)
// ---------------------------------------------------------------------------
const CORE_FIELDS = [
  'customer_name',
  'product_name',
  'batch_number',
  'complaint_type',
  'complaint_description',
];

const FIELD_LABELS = {
  customer_name: 'Customer Name',
  product_name: 'Product Name',
  batch_number: 'Batch / Lot Number',
  complaint_type: 'Complaint Type',
  complaint_description: 'Description',
};

// ---------------------------------------------------------------------------
// FOLLOW-UP FIELD CORRECTION PARSER
//
// Detects simple field-correction sentences and extracts the target field
// and value. Returns { field, value } or null if not a correction pattern.
//
// Supported patterns (case-insensitive):
//   "The batch number is PCM-2026-001"
//   "batch number: PCM-2026-001"
//   "The affected quantity is 48 capsules"
//   "Set product name to Paracetamol 500mg"
//   "Change complaint description to: Customer reports discoloration."
// ---------------------------------------------------------------------------

const FIELD_PATTERNS = [
  // customer_name
  { pattern: /customer[\s_]?name(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'customer_name' },
  // product_name
  { pattern: /product[\s_]?name(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'product_name' },
  // product_strength
  { pattern: /(?:strength|dosage|form|product[\s_]?strength)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'product_strength' },
  // batch_number
  { pattern: /(?:batch|lot|batch[\s_]?number|lot[\s_]?number)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'batch_number' },
  // complaint_type
  { pattern: /complaint[\s_]?type(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'complaint_type' },
  // complaint_date
  { pattern: /complaint[\s_]?date(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(.+)/i, field: 'complaint_date' },
  // manufacturing_date
  { pattern: /(?:manufacturing[\s_]?date|manufactured[\s_]?on|manufactured)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])?\s+(.+)/i, field: 'manufacturing_date' },
  // expiry_date
  { pattern: /(?:expiry[\s_]?date|expiry|expiration[\s_]?date|expires[\s_]?on)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])?\s+(.+)/i, field: 'expiry_date' },
  // affected_quantity — extract the numeric portion
  { pattern: /(?:affected[\s_]?quantity|quantity[\s_]?affected|quantity)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+(\d+(?:\.\d+)?)/i, field: 'affected_quantity' },
  // affected_quantity_unit — extract unit from quantity sentence
  { pattern: /(?:affected[\s_]?quantity|quantity[\s_]?affected|quantity)(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])\s+\d+(?:\.\d+)?\s+(.+)/i, field: 'affected_quantity_unit' },
  // complaint_description — only when user explicitly asks to change/update it
  {
    pattern: /(?:change|update|set|replace)\s+(?:the\s+)?(?:complaint[\s_]?)?description(?:\s+(?:field\s+)?(?:is|to|as|=|:)|[:=])?\s*:?\s+(.+)/i,
    field: 'complaint_description',
  },
];

function parseFieldCorrection(text) {
  const corrections = {};
  for (const { pattern, field } of FIELD_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      const val = match[1].trim().replace(/[.!?]+$/, '').trim();
      if (val) {
        corrections[field] = val;
      }
    }
  }
  return Object.keys(corrections).length > 0 ? corrections : null;
}

// ---------------------------------------------------------------------------
// CONTEXTUAL COPILOT RESPONSE GENERATOR
//
// Generates a plain-language assistant response WITHOUT calling Groq/LLM.
// Uses the current Redux state to give meaningful guidance.
// ---------------------------------------------------------------------------

function buildContextualResponse({ text, complaintData, missingFields }) {
  const instruction = text.toLowerCase();
  const missing = (missingFields || []).filter((f) => CORE_FIELDS.includes(f));
  const presentCoreFields = CORE_FIELDS.filter((f) => {
    const val = (complaintData || {})[f];
    return val !== null && val !== undefined && val !== '';
  });

  // --- Help / missing information requests ---
  if (
    instruction.includes('help') ||
    instruction.includes('missing') ||
    instruction.includes('fill') ||
    instruction.includes('what') ||
    instruction.includes('incomplete')
  ) {
    if (missing.length === 0) {
      return `✅ The complaint is complete — all required fields are present. You can now save it using the **Save Complaint** button.`;
    }
    const missingList = missing.map((f) => `• **${FIELD_LABELS[f] || f}**`).join('\n');
    return `The following required fields are still missing:\n\n${missingList}\n\nPlease provide this information and I will update the complaint form. For example, you can say:\n*"The batch number is PCM-2026-001"*`;
  }

  // --- Status / summary requests ---
  if (
    instruction.includes('status') ||
    instruction.includes('summary') ||
    instruction.includes('progress')
  ) {
    const readyCount = presentCoreFields.length;
    return `Complaint progress: **${readyCount}/5 required fields** are complete.${missing.length > 0 ? ` Still missing: ${missing.map((f) => FIELD_LABELS[f] || f).join(', ')}.` : ' All required fields are present.'}`;
  }

  // --- Default fallback ---
  if (missing.length > 0) {
    const missingList = missing.map((f) => `• **${FIELD_LABELS[f] || f}**`).join('\n');
    return `I can help update the complaint. The following required fields are currently missing:\n\n${missingList}\n\nYou can provide corrections directly. For example:\n*"The batch number is PCM-2026-001"*\n*"The affected quantity is 48 capsules."*`;
  }

  return `All required complaint fields are present. Use **Save Complaint** to save the record. If you need to correct a specific field, describe the correction (e.g. *"The batch number is PCM-2026-001"*).`;
}

// ---------------------------------------------------------------------------
// COMPONENT
// ---------------------------------------------------------------------------

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

  // -------------------------------------------------------------------------
  // performInitialAnalysis — full LangGraph extraction
  // Used by: "Analyze Complaint" button AND first Send with no prior analysis
  // -------------------------------------------------------------------------
  const performInitialAnalysis = async (textToAnalyze, sourceType = 'text') => {
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

  // -------------------------------------------------------------------------
  // handleFollowUp — Copilot conversational mode (NO analyzeComplaint call)
  //
  // Called by handleSend() when a prior analysis already exists.
  // Does NOT overwrite analysisResult, riskAssessment, or complaint_description.
  //
  // Two sub-cases:
  //   A. Explicit field correction detected → patchAnalysisResult
  //   B. General instruction / question → contextual assistant response
  // -------------------------------------------------------------------------
  const handleFollowUp = (text) => {
    const complaintData = analysisResult?.complaint_data || {};
    const currentMissingFields = analysisResult?.missing_fields || [];

    const corrections = parseFieldCorrection(text);

    if (corrections) {
      // Case A — field correction
      dispatch(patchAnalysisResult({ fields: corrections }));

      // Recompute missing_fields to keep ComplaintnessChecker in sync
      const mergedData = { ...complaintData, ...corrections };
      const updatedMissing = CORE_FIELDS.filter((f) => {
        const val = mergedData[f];
        return val === null || val === undefined || val === '';
      });
      dispatch(patchMissingFields(updatedMissing));

      const fieldNames = Object.keys(corrections)
        .map((f) => FIELD_LABELS[f] || f)
        .join(', ');
      const resolvedFields = Object.keys(corrections).filter(
        (f) => CORE_FIELDS.includes(f) && currentMissingFields.includes(f)
      );

      let reply = `Updated **${fieldNames}**.`;
      if (resolvedFields.length > 0) {
        reply += ` ✅ Required field${resolvedFields.length > 1 ? 's' : ''} now resolved.`;
      }
      if (updatedMissing.length > 0) {
        reply += ` Still missing: ${updatedMissing.map((f) => FIELD_LABELS[f] || f).join(', ')}.`;
      } else {
        reply += ' All required fields are now present — complaint is ready to save.';
      }

      dispatch(addMessage({ role: 'assistant', content: reply }));
    } else {
      // Case B — general instruction / question → contextual response, no state change
      const response = buildContextualResponse({
        text,
        complaintData,
        missingFields: currentMissingFields,
      });
      dispatch(addMessage({ role: 'assistant', content: response }));
    }
  };

  // -------------------------------------------------------------------------
  // handleSend — dispatched by Send button and Enter key
  //
  // Routing logic:
  //   1. If no prior analysisResult exists → treat as first complaint input
  //      → run full analysis (same as Analyze Complaint button)
  //   2. If analysisResult already exists → treat as follow-up
  //      → run handleFollowUp (no analyzeComplaint call)
  // -------------------------------------------------------------------------
  const handleSend = () => {
    const text = input.trim();
    if (!text || isProcessing) return;

    dispatch(addMessage({ role: 'user', content: text }));
    dispatch(setInput(''));
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    if (analysisResult) {
      // Follow-up mode: complaint already analyzed — do NOT re-run full analysis
      handleFollowUp(text);
    } else {
      // First message: no prior analysis — treat as initial complaint input
      performInitialAnalysis(text, 'text');
    }
  };

  // -------------------------------------------------------------------------
  // handleAnalyze — "Analyze Complaint" button
  //
  // Always runs the full analysis flow.
  // If textarea is empty and analysis already exists, blocks redundant re-analysis.
  // -------------------------------------------------------------------------
  const handleAnalyze = () => {
    const text = input.trim();

    // Block re-analysis when textarea is empty and analysis already exists
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
      performInitialAnalysis(text, 'text');
    } else {
      // Use latest user message from conversation if input is empty
      const userMsgs = messages.filter((m) => m.role === 'user');
      if (userMsgs.length > 0) {
        const lastText = userMsgs[userMsgs.length - 1].content;
        performInitialAnalysis(lastText, 'text');
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
          placeholder={
            analysisResult
              ? 'Ask a question or provide a field correction…'
              : 'Type a message or paste complaint text…'
          }
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
