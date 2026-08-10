import React, { useRef } from 'react';

const UploadIcon = () => (
  <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
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
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function DocumentUpload({ file, onFileChange }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = React.useState(false);

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type === 'application/pdf') {
      onFileChange(dropped);
    }
  };

  const handleInputChange = (e) => {
    const selected = e.target.files[0];
    if (selected) onFileChange(selected);
  };

  return (
    <div className="doc-upload-section">
      <div className="doc-upload-label">Document / PDF Upload</div>

      {file ? (
        <div className="file-selected">
          <PdfIcon />
          <span className="file-name" title={file.name}>{file.name}</span>
          <span className="file-size">{formatBytes(file.size)}</span>
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
        </div>
      ) : (
        <div
          className={`dropzone${dragging ? ' drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          aria-label="Upload PDF file — drag and drop or click to browse"
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleInputChange}
            aria-hidden="true"
            tabIndex={-1}
          />
          <div className="dropzone-inner">
            <UploadIcon />
            <span className="dropzone-text">Drop PDF or click to browse</span>
            <span className="dropzone-hint">PDF only — processing in next phase</span>
          </div>
        </div>
      )}
    </div>
  );
}
