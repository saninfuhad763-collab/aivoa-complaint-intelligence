import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchComplaintById } from '../../features/complaints/complaintSlice.js';

export default function SavedComplaintsList() {
  const dispatch = useDispatch();
  const { complaints, selectedComplaint } = useSelector((s) => s.complaints);

  const handleSelect = (id) => {
    if (selectedComplaint?.id === id) return;
    dispatch(fetchComplaintById(id));
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
                <span className={`status-badge status-${(c.status || 'NEW').toLowerCase()}`}>
                  {c.status || 'NEW'}
                </span>
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
