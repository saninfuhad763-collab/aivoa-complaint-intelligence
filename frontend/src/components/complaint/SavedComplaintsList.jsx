import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchComplaints,
  fetchComplaintById,
  removeComplaint,
  clearAnalysisResult,
} from '../../features/complaints/complaintSlice.js';
import { clearRiskAssessment } from '../../features/risk/riskSlice.js';
import { addNotification } from '../../features/ui/uiSlice.js';

const TrashIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
  </svg>
);

export default function SavedComplaintsList() {
  const dispatch = useDispatch();
  const { complaints, selectedComplaint } = useSelector((s) => s.complaints);

  const handleSelect = (id) => {
    if (selectedComplaint?.id === id) return;
    dispatch(fetchComplaintById(id));
  };

  const handleDelete = async (e, complaint) => {
    e.stopPropagation();
    const confirmed = window.confirm(
      `Are you sure you want to delete complaint ${complaint.complaint_number}?`
    );
    if (!confirmed) return;

    // Capture selection state BEFORE dispatching, because removeComplaint.fulfilled
    // synchronously sets Redux selectedComplaint = null before the await resolves.
    const isSelected = selectedComplaint?.id === complaint.id;

    const actionResult = await dispatch(removeComplaint(complaint.id));
    if (removeComplaint.fulfilled.match(actionResult)) {
      dispatch(addNotification({
        type: 'success',
        message: `Complaint ${complaint.complaint_number} deleted successfully.`,
      }));
      dispatch(fetchComplaints());
      if (isSelected) {
        dispatch(clearAnalysisResult());
        dispatch(clearRiskAssessment());
      }
    } else {
      const errMsg = actionResult.payload || 'Failed to delete complaint.';
      dispatch(addNotification({
        type: 'error',
        message: errMsg,
      }));
    }
  };

  if (!complaints || complaints.length === 0) {
    return (
      <div className="saved-complaints-section">
        <div className="saved-complaints-header">
          <span className="saved-complaints-title">Saved Complaints</span>
          <span className="saved-complaints-count">0</span>
        </div>
        <div className="saved-complaints-empty">
          No saved complaints in database yet.
        </div>
      </div>
    );
  }

  return (
    <div className="saved-complaints-section">
      <div className="saved-complaints-header">
        <div className="saved-complaints-title-row">
          <span className="saved-complaints-title">Saved Complaints</span>
          <span className="saved-complaints-count">{complaints.length}</span>
        </div>
      </div>

      <div className="saved-complaints-list">
        {complaints.map((c) => {
          const isSelected = selectedComplaint?.id === c.id;
          return (
            <div
              key={c.id}
              className={`saved-complaint-item${isSelected ? ' selected' : ''}`}
              onClick={() => handleSelect(c.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleSelect(c.id)}
            >
              <div className="saved-complaint-main">
                <span className="saved-complaint-number">{c.complaint_number}</span>
                <div className="saved-complaint-actions">
                  <span className={`status-badge status-${(c.status || 'NEW').toLowerCase()}`}>
                    {c.status || 'NEW'}
                  </span>
                  <button
                    type="button"
                    className="btn-item-delete"
                    onClick={(e) => handleDelete(e, c)}
                    aria-label={`Delete complaint ${c.complaint_number}`}
                    title="Delete complaint"
                  >
                    <TrashIcon />
                  </button>
                </div>
              </div>
              <div className="saved-complaint-details">
                <span className="saved-complaint-customer">
                  {c.customer_name || 'No customer name'}
                </span>
                {c.product_name && (
                  <span className="saved-complaint-product"> • {c.product_name}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
