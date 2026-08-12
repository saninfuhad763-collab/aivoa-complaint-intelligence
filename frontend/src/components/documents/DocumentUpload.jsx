import React, { useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { analyzePdfComplaint } from '../../features/complaints/complaintSlice.js';
import { addMessage, setLoading } from '../../features/copilot/copilotSlice.js';
import { addNotification } from '../../features/ui/uiSlice.js';

const PaperclipIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" aria-hidden="true">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
  </svg>
);

const PdfIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" className="file-icon" aria-hidden="true">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const formatBytes = (bytes) => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function DocumentUpload({ file, onFileChange }) {
  const dispatch = useDispatch();
  const inputRef = useRef(null);
  const [dragging, setDragging] = React.useState(false);

  const copilotLoading = useSelector((s) => s.copilot.loading);
  const analysisLoading = useSelector((s) => s.complaints.analysisLoading);
  const analysisResult = useSelector((s) => s.complaints.analysisResult);

  const isProcessing = copilotLoading || analysisLoading;
  const docMeta = analysisResult?.document_metadata;

  const processSelectedPdf = async (selectedFile) => {
    if (!selectedFile || isProcessing) return;

    const isPdfExt = selectedFile.name?.toLowerCase().endsWith('.pdf');
    const isPdfMime = selectedFile.type === 'application/pdf' || selectedFile.type === 'application/x-pdf';

    if (!isPdfExt && !isPdfMime) {
      dispatch(addNotification({
        type: 'error',
        message: 'Only PDF files are accepted.',
      }));
      return;
    }

    onFileChange(selectedFile);

    dispatch(addMessage({
      role: 'user',
      content: `Uploaded PDF for AI analysis: ${selectedFile.name}`,
    }));

    dispatch(setLoading(true));

    const actionResult = await dispatch(analyzePdfComplaint(selectedFile));

    dispatch(setLoading(false));

    if (analyzePdfComplaint.fulfilled.match(actionResult)) {
      const res = actionResult.payload;
      const confPct = res.confidence != null ? Math.round(res.confidence * 100) : null;
      const pages = res.document_metadata?.page_count;

      let summary = `PDF analysis complete for ${selectedFile.name}`;
      if (pages) summary += ` (${pages} page${pages > 1 ? 's' : ''})`;
      if (confPct !== null) summary += ` with ${confPct}% confidence`;
      summary += `. Form populated and risk assessed.`;

      if (res.missing_fields && res.missing_fields.length > 0) {
        summary += ` Missing fields: ${res.missing_fields.join(', ')}.`;
      }

      dispatch(addMessage({
        role: 'assistant',
        content: summary,
      }));

      dispatch(addNotification({
        type: 'success',
        message: `PDF document '${selectedFile.name}' analyzed successfully.`,
      }));
    } else {
      const errMsg = actionResult.payload || 'Failed to analyze PDF document.';
      dispatch(addMessage({
        role: 'system',
        content: `PDF Analysis error: ${errMsg}`,
      }));
      dispatch(addNotification({
        type: 'error',
        message: errMsg,
      }));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isProcessing) setDragging(true);
  };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (isProcessing) return;
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      processSelectedPdf(dropped);
    }
  };

  const handleInputChange = (e) => {
    const selected = e.target.files[0];
    if (selected && !isProcessing) {
      processSelectedPdf(selected);
    }
  };

  return (
    <div className="doc-upload-section">
      <div className="doc-upload-label">Document / PDF Upload</div>

      {file ? (
        <div className="file-selected">
          <PdfIcon />
          <span className="file-name" title={file.name}>{file.name}</span>
          <span className="file-size">
            {formatBytes(file.size)}
            {docMeta?.page_count ? ` • ${docMeta.page_count} pg` : ''}
          </span>
          {isProcessing ? (
            <span className="btn-spinner" aria-hidden="true" style={{ width: 14, height: 14 }} />
          ) : (
            <button
              type="button"
              className="file-clear"
              onClick={() => onFileChange(null)}
              aria-label="Remove selected file"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      ) : (
        <div
          className={`dropzone${dragging ? ' drag-active' : ''}${isProcessing ? ' disabled' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          role="button"
          tabIndex={isProcessing ? -1 : 0}
          aria-label="Upload PDF file — drag and drop or click to browse"
          onClick={() => !isProcessing && inputRef.current?.click()}
          onKeyDown={(e) => !isProcessing && e.key === 'Enter' && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleInputChange}
            aria-hidden="true"
            tabIndex={-1}
            disabled={isProcessing}
          />
          <div className="dropzone-compact-inner">
            {isProcessing ? (
              <>
                <span className="btn-spinner" aria-hidden="true" style={{ width: 14, height: 14 }} />
                <span className="dropzone-text">Extracting & analyzing PDF…</span>
              </>
            ) : (
              <>
                <span className="btn-attach-pill">
                  <PaperclipIcon />
                  Attach PDF
                </span>
                <span className="dropzone-hint">PDF upload for AI complaint extraction</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
