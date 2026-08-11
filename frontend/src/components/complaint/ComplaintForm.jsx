import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createNewComplaint, clearAnalysisResult } from '../../features/complaints/complaintSlice.js';
import { clearRiskAssessment } from '../../features/risk/riskSlice.js';
import { addNotification } from '../../features/ui/uiSlice.js';
import RiskAssessment from './RiskAssessment.jsx';

const INITIAL_FORM = {
  complaint_number: '',
  complaint_source: '',
  customer_name: '',
  product_name: '',
  product_strength: '',
  batch_number: '',
  manufacturing_date: '',
  expiry_date: '',
  affected_quantity: '',
  affected_quantity_unit: '',
  complaint_type: '',
  complaint_date: '',
  complaint_description: '',
  status: 'NEW',
};

const COMPLAINT_TYPES = [
  '', 'Quality Defect', 'Packaging Defect', 'Mislabeling',
  'Contamination', 'Efficacy Concern', 'Adverse Reaction',
  'Foreign Matter', 'Temperature Excursion', 'Other',
];

const COMPLAINT_SOURCES = [
  { value: '', label: '— Select source —' },
  { value: 'email', label: 'Email' },
  { value: 'web_form', label: 'Web Form' },
  { value: 'pdf_upload', label: 'PDF Upload' },
  { value: 'phone', label: 'Phone' },
  { value: 'letter', label: 'Letter' },
  { value: 'other', label: 'Other' },
];

const QUANTITY_UNITS = [
  '', 'tablets', 'capsules', 'vials', 'ampoules',
  'bottles', 'sachets', 'patches', 'units', 'kg', 'liters',
];

const STATUS_OPTIONS = [
  { value: 'NEW', label: 'New' },
  { value: 'IN_REVIEW', label: 'In Review' },
  { value: 'UNDER_INVESTIGATION', label: 'Under Investigation' },
  { value: 'CLOSED', label: 'Closed' },
  { value: 'REJECTED', label: 'Rejected' },
];

const ALLOWED_SOURCES = new Set(['email', 'web_form', 'pdf_upload', 'phone', 'letter', 'other']);

const normalizeComplaintSource = (incomingSource, existingSource) => {
  if (existingSource && ALLOWED_SOURCES.has(existingSource)) {
    return existingSource;
  }
  if (!incomingSource) {
    return existingSource || '';
  }
  const lower = String(incomingSource).trim().toLowerCase();
  if (ALLOWED_SOURCES.has(lower)) {
    return lower;
  }
  return 'other';
};

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const { loading, error, analysisResult } = useSelector((s) => s.complaints);

  const [form, setForm] = useState(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    if (analysisResult?.complaint_data) {
      const data = analysisResult.complaint_data;
      setForm((prevForm) => {
        const updated = { ...prevForm };
        Object.keys(data).forEach((key) => {
          if (key === 'complaint_source') {
            updated.complaint_source = normalizeComplaintSource(data.complaint_source, prevForm.complaint_source);
          } else if (key in updated && data[key] !== null && data[key] !== undefined && data[key] !== '') {
            updated[key] = String(data[key]);
          }
        });
        if (!updated.complaint_number || !updated.complaint_number.trim()) {
          const year = new Date().getFullYear();
          const rand = Math.floor(100 + Math.random() * 900);
          updated.complaint_number = `COMP-${year}-${rand}`;
        }
        return updated;
      });
    }
  }, [analysisResult]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!form.complaint_number.trim()) {
      errs.complaint_number = 'Complaint number is required.';
    }
    if (form.affected_quantity !== '' && Number(form.affected_quantity) < 0) {
      errs.affected_quantity = 'Quantity must be non-negative.';
    }
    return errs;
  };

  const buildPayload = () => {
    const payload = { ...form };
    // Remove empty optional fields so backend receives null, not ""
    Object.keys(payload).forEach((k) => {
      if (payload[k] === '') {
        payload[k] = null;
      }
    });
    if (payload.affected_quantity !== null) {
      payload.affected_quantity = Number(payload.affected_quantity);
    }
    return payload;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    const result = await dispatch(createNewComplaint(buildPayload()));
    if (createNewComplaint.fulfilled.match(result)) {
      dispatch(addNotification({
        type: 'success',
        message: `Complaint ${result.payload.complaint_number} saved successfully.`,
      }));
      setForm(INITIAL_FORM);
      setFieldErrors({});
    } else {
      dispatch(addNotification({
        type: 'error',
        message: result.payload || 'Failed to save complaint.',
      }));
    }
  };

  const handleReset = () => {
    setForm(INITIAL_FORM);
    setFieldErrors({});
    dispatch(clearAnalysisResult());
    dispatch(clearRiskAssessment());
  };

  return (
    <div className="panel panel-left">
      {/* Panel header */}
      <div className="panel-header">
        <span className="panel-title">Log Customer Complaint</span>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleReset}
          title="Clear form"
        >
          Clear
        </button>
      </div>

      {/* Form body */}
      <form onSubmit={handleSave} noValidate aria-label="Complaint entry form">
        <div className="complaint-form-container">

          {/* Section: Identification */}
          <div className="form-section">
            <div className="form-section-title">Identification</div>
            <div className="form-grid form-grid-2">
              <div className="form-field">
                <label className="form-label" htmlFor="complaint_number">
                  Complaint Number <span className="required-mark" aria-hidden="true">*</span>
                </label>
                <input
                  id="complaint_number"
                  name="complaint_number"
                  type="text"
                  className={`form-input${fieldErrors.complaint_number ? ' error' : ''}`}
                  placeholder="COMP-2024-001"
                  value={form.complaint_number}
                  onChange={handleChange}
                  autoComplete="off"
                  aria-required="true"
                  aria-describedby={fieldErrors.complaint_number ? 'cn-error' : undefined}
                />
                {fieldErrors.complaint_number && (
                  <span id="cn-error" className="field-error" role="alert">
                    {fieldErrors.complaint_number}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="complaint_source">
                  Complaint Source
                </label>
                <select
                  id="complaint_source"
                  name="complaint_source"
                  className="form-select"
                  value={form.complaint_source}
                  onChange={handleChange}
                >
                  {COMPLAINT_SOURCES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="complaint_date">
                  Complaint Date
                </label>
                <input
                  id="complaint_date"
                  name="complaint_date"
                  type="date"
                  className="form-input"
                  value={form.complaint_date}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="customer_name">
                  Customer Name
                </label>
                <input
                  id="customer_name"
                  name="customer_name"
                  type="text"
                  className="form-input"
                  placeholder="Reporting customer or facility"
                  value={form.customer_name}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="complaint_type">
                  Complaint Type
                </label>
                <select
                  id="complaint_type"
                  name="complaint_type"
                  className="form-select"
                  value={form.complaint_type}
                  onChange={handleChange}
                >
                  {COMPLAINT_TYPES.map((t) => (
                    <option key={t} value={t}>{t || '— Select type —'}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Section: Product Information */}
          <div className="form-section">
            <div className="form-section-title">Product Information</div>
            <div className="form-grid form-grid-2">
              <div className="form-field">
                <label className="form-label" htmlFor="product_name">Product Name</label>
                <input
                  id="product_name"
                  name="product_name"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Amoxicillin"
                  value={form.product_name}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="product_strength">Strength / Form</label>
                <input
                  id="product_strength"
                  name="product_strength"
                  type="text"
                  className="form-input"
                  placeholder="e.g. 500mg capsules"
                  value={form.product_strength}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="batch_number">Batch / Lot Number</label>
                <input
                  id="batch_number"
                  name="batch_number"
                  type="text"
                  className="form-input"
                  placeholder="BCH-20241001"
                  value={form.batch_number}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="affected_quantity">
                  Affected Quantity
                </label>
                <div className="quantity-row">
                  <input
                    id="affected_quantity"
                    name="affected_quantity"
                    type="number"
                    min="0"
                    step="any"
                    className={`form-input${fieldErrors.affected_quantity ? ' error' : ''}`}
                    placeholder="0"
                    value={form.affected_quantity}
                    onChange={handleChange}
                    aria-describedby={fieldErrors.affected_quantity ? 'qty-error' : undefined}
                  />
                  <select
                    id="affected_quantity_unit"
                    name="affected_quantity_unit"
                    className="form-select"
                    value={form.affected_quantity_unit}
                    onChange={handleChange}
                    aria-label="Quantity unit"
                  >
                    {QUANTITY_UNITS.map((u) => (
                      <option key={u} value={u}>{u || 'Unit'}</option>
                    ))}
                  </select>
                </div>
                {fieldErrors.affected_quantity && (
                  <span id="qty-error" className="field-error" role="alert">
                    {fieldErrors.affected_quantity}
                  </span>
                )}
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="manufacturing_date">Manufacturing Date</label>
                <input
                  id="manufacturing_date"
                  name="manufacturing_date"
                  type="date"
                  className="form-input"
                  value={form.manufacturing_date}
                  onChange={handleChange}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="expiry_date">Expiry Date</label>
                <input
                  id="expiry_date"
                  name="expiry_date"
                  type="date"
                  className="form-input"
                  value={form.expiry_date}
                  onChange={handleChange}
                />
              </div>
            </div>
          </div>

          {/* Section: Complaint Details */}
          <div className="form-section">
            <div className="form-section-title">Complaint Details</div>
            <div className="form-grid">
              <div className="form-field full-width">
                <label className="form-label" htmlFor="complaint_description">
                  Description
                </label>
                <textarea
                  id="complaint_description"
                  name="complaint_description"
                  className="form-textarea"
                  placeholder="Describe the complaint in detail — symptoms, observations, patient/customer report..."
                  value={form.complaint_description}
                  onChange={handleChange}
                  rows={4}
                />
              </div>

              <div className="form-field">
                <label className="form-label" htmlFor="status">Status</label>
                <select
                  id="status"
                  name="status"
                  className="form-select"
                  value={form.status}
                  onChange={handleChange}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Backend error display */}
          {error && (
            <div className="notification notification-error" role="alert"
              style={{ marginBottom: 12, position: 'static' }}>
              <span className="notification-message">{error}</span>
            </div>
          )}
        </div>

        {/* Form actions */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            aria-busy={loading}
          >
            {loading
              ? <><span className="btn-spinner" aria-hidden="true" />Saving…</>
              : <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                    <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                  </svg>
                  Save Complaint
                </>
            }
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleReset}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </form>

      {/* Risk Assessment card below the form */}
      <RiskAssessment />
    </div>
  );
}
