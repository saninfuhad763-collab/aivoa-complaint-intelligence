import React from 'react';
import { useSelector } from 'react-redux';

/**
 * DuplicateWarning
 *
 * Advisory UI component that alerts QA/QMS users when one or more existing
 * complaints in PostgreSQL match the currently analyzed/edited complaint.
 *
 * Strictly non-blocking: does NOT disable Save Complaint or alter AI risk/readiness.
 */

const WarningIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return String(dateStr);
  }
};

export default function DuplicateWarning() {
  const { duplicateCandidates, duplicateLoading } = useSelector((s) => s.complaints);

  if (!duplicateCandidates || duplicateCandidates.length === 0) {
    return null;
  }

  return (
    <div className="duplicate-warning-card" role="region" aria-label="Potential Duplicate Complaints">
      <div className="duplicate-warning-header">
        <span className="duplicate-warning-title">
          <WarningIcon />
          Potential Duplicate Complaint Detected ({duplicateCandidates.length})
        </span>
        <span className="duplicate-warning-badge">Advisory</span>
      </div>

      <p className="duplicate-warning-subtitle">
        This complaint may match an existing record. Review candidate details before saving.
      </p>

      <div className="duplicate-candidates-list">
        {duplicateCandidates.map((cand) => (
          <div key={cand.id} className="duplicate-candidate-item">
            <div className="duplicate-candidate-top">
              <span className="duplicate-candidate-number">{cand.complaint_number}</span>
              <span className={`duplicate-confidence-tag ${cand.match_confidence === 'high' ? 'tag-high' : 'tag-med'}`}>
                {cand.match_confidence === 'high' ? 'High Match' : 'Medium Match'}
              </span>
            </div>

            <div className="duplicate-candidate-reason">
              {cand.match_reason}
            </div>

            <div className="duplicate-candidate-details">
              {cand.product_name && (
                <span className="duplicate-detail">
                  <strong>Product:</strong> {cand.product_name}
                </span>
              )}
              {cand.batch_number && (
                <span className="duplicate-detail">
                  <strong>Batch:</strong> {cand.batch_number}
                </span>
              )}
              {cand.customer_name && (
                <span className="duplicate-detail">
                  <strong>Customer:</strong> {cand.customer_name}
                </span>
              )}
              {cand.created_at && (
                <span className="duplicate-detail">
                  <strong>Logged:</strong> {formatDate(cand.created_at)}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
