import React from 'react';
import { useSelector } from 'react-redux';

/**
 * ComplaintnessChecker
 *
 * Communicates complaint readiness using the authoritative 5-field core completeness rule
 * from backend LangGraph validation (missingFields):
 *   CORE_COMPLAINT_FIELDS: customer_name, product_name, batch_number, complaint_type, complaint_description
 *
 * Readiness states:
 *   - READY: All 5 required fields present → "🟢 Complaint Ready"
 *   - INCOMPLETE: 1+ required fields missing → "🟠 Information Needed"
 *
 * Optional fields (manufacturing_date, expiry_date, etc.) are shown in an informational section
 * and DO NOT affect readiness.
 */

const CheckIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const AlertIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

const InfoIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="16" x2="12" y2="12"/>
    <line x1="12" y1="8" x2="12.01" y2="8"/>
  </svg>
);

const CORE_FIELD_LABELS = {
  customer_name: 'Customer Name',
  product_name: 'Product Name',
  batch_number: 'Batch / Lot Number',
  complaint_type: 'Complaint Type',
  complaint_description: 'Description',
};

const OPTIONAL_FIELD_LABELS = {
  manufacturing_date: 'Manufacturing Date',
  expiry_date: 'Expiry Date',
  product_strength: 'Strength / Form',
  affected_quantity: 'Affected Quantity',
};

export default function ComplaintnessChecker() {
  const { missingFields } = useSelector((s) => s.risk);
  const { analysisResult, selectedComplaint } = useSelector((s) => s.complaints);
  const hasData = Boolean(analysisResult || selectedComplaint);

  if (!hasData) {
    return (
      <div className="completeness-card" role="region" aria-label="Complaint Readiness">
        <div className="completeness-header">
          <span className="completeness-title">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M9 11l3 3L22 4"/>
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
            </svg>
            Completeness Check
          </span>
          <span className="completeness-badge completeness-needed">
            <AlertIcon />
            Awaiting Analysis
          </span>
        </div>
        <div style={{ padding: '14px 14px', textAlign: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
          Completeness check will evaluate required fields after complaint analysis.
        </div>
      </div>
    );
  }

  const missingCore = missingFields || [];
  // Safely access complaint_data: analysisResult may be null when a saved
  // complaint has been reopened without re-running analysis.
  const complaintData = analysisResult?.complaint_data ?? selectedComplaint ?? {};
  const validationErrors = analysisResult?.validation_errors || [];

  // Single source of truth for readiness: all 5 core required fields present
  const isReady = missingCore.length === 0;

  // Identify empty optional fields for informational display ONLY (does not affect readiness)
  const missingOptional = Object.keys(OPTIONAL_FIELD_LABELS).filter((f) => {
    const val = complaintData[f];
    return val === null || val === undefined || val === '';
  });

  const extraErrors = validationErrors.filter(
    (e) => !e.startsWith('Missing required complaint details')
  );

  return (
    <div className="completeness-card" role="region" aria-label="Complaint Readiness">
      <div className="completeness-header">
        <span className="completeness-title">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
          Completeness Check
        </span>
        <span className={`completeness-badge ${isReady ? 'completeness-ready' : 'completeness-needed'}`}>
          {isReady ? <CheckIcon /> : <AlertIcon />}
          {isReady ? 'Complaint Ready' : 'Information Needed'}
        </span>
      </div>

      <div className="completeness-body">
        {isReady ? (
          <div className="completeness-ok">
            All required complaint information is present.
          </div>
        ) : (
          <div className="completeness-section">
            <div className="completeness-section-label">
              Missing Required Information ({missingCore.length})
            </div>
            <ul className="completeness-fields-list">
              {missingCore.map((f) => (
                <li key={f} className="completeness-field-item">
                  <AlertIcon />
                  {CORE_FIELD_LABELS[f] || f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {extraErrors.length > 0 && (
          <div className="completeness-section">
            <div className="completeness-section-label">Validation Warnings</div>
            <ul className="completeness-fields-list">
              {extraErrors.map((err, i) => (
                <li key={i} className="completeness-field-item completeness-warning">
                  <AlertIcon />
                  {err}
                </li>
              ))}
            </ul>
          </div>
        )}

        {missingOptional.length > 0 && (
          <div className="completeness-section completeness-optional-section">
            <div className="completeness-section-label">Optional Information</div>
            <ul className="completeness-fields-list">
              {missingOptional.map((f) => (
                <li key={f} className="completeness-field-item completeness-optional-item">
                  <InfoIcon />
                  {OPTIONAL_FIELD_LABELS[f] || f}
                </li>
              ))}
            </ul>
          </div>
        )}

        {!isReady && (
          <p className="completeness-hint">
            Ask the AI Copilot to help fill in missing information, or edit the form fields directly.
          </p>
        )}
      </div>
    </div>
  );
}
