import React from 'react';
import { useSelector } from 'react-redux';

const ShieldIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const severityLabel = (v) => {
  if (!v) return null;
  const lower = v.toLowerCase();
  const map = { low: 'low', medium: 'medium', high: 'high', critical: 'critical' };
  return map[lower] || null;
};

export default function RiskAssessment() {
  const { severity, riskLevel, initialAssessment, suggestedAction, confidence, missingFields } =
    useSelector((s) => s.risk);

  const hasData = severity || riskLevel || initialAssessment;
  const sevClass = severityLabel(severity) || 'pending';
  const confidencePct = confidence != null ? Math.round(confidence * 100) : null;

  return (
    <div className="risk-card" role="region" aria-label="AI Risk Assessment">
      <div className="risk-card-header">
        <span className="risk-card-title">
          <ShieldIcon />
          AI Risk Assessment
        </span>
        <span className="panel-badge badge-ai">AI</span>
      </div>

      {!hasData ? (
        <div style={{ padding: '20px 14px', textAlign: 'center' }}>
          <p className="risk-awaiting">
            Awaiting AI analysis — submit a complaint via the Copilot to generate a risk assessment.
          </p>
        </div>
      ) : (
        <div className="risk-grid">
          <div className="risk-cell">
            <div className="risk-cell-label">Severity</div>
            <span className={`risk-chip ${sevClass}`}>
              {severity || '—'}
            </span>
          </div>

          <div className="risk-cell">
            <div className="risk-cell-label">Risk Level</div>
            <span className={`risk-chip ${severityLabel(riskLevel) || 'pending'}`}>
              {riskLevel || '—'}
            </span>
          </div>

          <div className="risk-cell full">
            <div className="risk-cell-label">Initial Assessment</div>
            <div className="risk-cell-value" style={{ fontStyle: 'normal', color: 'var(--text-secondary)' }}>
              {initialAssessment || '—'}
            </div>
          </div>

          <div className="risk-cell full">
            <div className="risk-cell-label">Suggested Next Action</div>
            <div className="risk-cell-value" style={{ fontStyle: 'normal', color: 'var(--text-secondary)' }}>
              {suggestedAction || '—'}
            </div>
          </div>

          {confidencePct !== null && (
            <div className="risk-cell full">
              <div className="risk-cell-label">AI Confidence — {confidencePct}%</div>
              <div className="confidence-bar-wrap" role="progressbar"
                aria-valuenow={confidencePct} aria-valuemin="0" aria-valuemax="100"
                aria-label={`AI confidence ${confidencePct}%`}>
                <div className="confidence-bar-fill" style={{ width: `${confidencePct}%` }} />
              </div>
            </div>
          )}

          {missingFields?.length > 0 && (
            <div className="risk-cell full">
              <div className="risk-cell-label">Missing Information</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                {missingFields.map((f) => (
                  <span key={f} style={{
                    fontSize: 10, padding: '1px 6px',
                    background: 'var(--warning-muted)',
                    color: 'var(--warning)',
                    borderRadius: 3,
                  }}>{f}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
