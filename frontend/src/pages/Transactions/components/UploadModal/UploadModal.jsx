import { useState, useRef } from 'react';
import { X, Upload, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { uploadStatement } from '../../../../services/transactionService';
import './UploadModal.css';

export default function UploadModal({ isOpen, onClose, onSuccess }) {
  const [status, setStatus] = useState('idle');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFile = (f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are accepted. Export your bank statement as CSV and try again.');
      setStatus('error');
      return;
    }
    setFile(f);
    setStatus('selected');
    setError('');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleFileInput = (e) => handleFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    setError('');
    try {
      const data = await uploadStatement(file);
      setResult(data);
      setStatus('success');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Something went wrong while processing your statement. Please try again.'
      );
      setStatus('error');
    }
  };

  const reset = () => {
    setStatus('idle');
    setFile(null);
    setResult(null);
    setError('');
    setDragging(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleClose = () => {
    if (status === 'success') {
      onSuccess();
    } else {
      reset();
      onClose();
    }
  };

  const handleDone = () => {
    onSuccess();
    reset();
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>

        <div className="modal-header">
          <div>
            <h2 className="modal-title">Upload Statement</h2>
            <p className="modal-subtitle">Import transactions from your bank CSV export.</p>
          </div>
          <button className="modal-close" onClick={handleClose} aria-label="Close">
            <X size={16} strokeWidth={2} />
          </button>
        </div>

        <div className="modal-body">
          {status === 'idle' && (
            <div
              className={`upload-zone${dragging ? ' upload-zone--dragging' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="upload-zone-input"
                onChange={handleFileInput}
              />
              <div className="upload-zone-icon">
                <Upload size={22} strokeWidth={1.5} />
              </div>
              <p className="upload-zone-primary">
                Drag &amp; drop your bank statement
              </p>
              <p className="upload-zone-secondary">
                or <span className="upload-zone-link">click to browse</span> — CSV files only
              </p>
              <div className="upload-zone-hint">
                Expected columns: <code>date</code>, <code>merchant</code>, <code>amount</code>
              </div>
            </div>
          )}

          {status === 'selected' && (
            <div className="upload-selected">
              <div className="upload-file-row">
                <div className="upload-file-icon">
                  <FileText size={20} strokeWidth={1.5} />
                </div>
                <div className="upload-file-info">
                  <span className="upload-file-name">{file.name}</span>
                  <span className="upload-file-size">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
                <button className="upload-file-remove" onClick={reset}>
                  <X size={14} strokeWidth={2} />
                </button>
              </div>
              <p className="upload-selected-hint">
                FinMate will auto-categorize each transaction during import.
              </p>
            </div>
          )}

          {status === 'uploading' && (
            <div className="upload-progress">
              <div className="upload-spinner" />
              <p className="upload-progress-text">Processing your statement...</p>
              <p className="upload-progress-sub">Categorizing transactions automatically.</p>
            </div>
          )}

          {status === 'success' && (
            <div className="upload-success">
              <div className="upload-success-icon">
                <CheckCircle size={32} strokeWidth={1.5} />
              </div>
              <p className="upload-success-title">Import complete</p>
              <p className="upload-success-count">
                <strong>{result?.transactions_imported?.toLocaleString('en-IN')}</strong> transactions imported successfully.
              </p>
              <p className="upload-success-sub">
                All transactions have been auto-categorized and are ready to view.
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="upload-error-state">
              <div className="upload-error-icon">
                <AlertCircle size={28} strokeWidth={1.5} />
              </div>
              <p className="upload-error-title">Import failed</p>
              <p className="upload-error-msg">{error}</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {status === 'idle' && (
            <button className="modal-btn-secondary" onClick={handleClose}>
              Cancel
            </button>
          )}

          {status === 'selected' && (
            <>
              <button className="modal-btn-secondary" onClick={reset}>
                Change file
              </button>
              <button className="modal-btn-primary" onClick={handleUpload}>
                <Upload size={13} strokeWidth={2} />
                Import transactions
              </button>
            </>
          )}

          {status === 'uploading' && (
            <button className="modal-btn-primary" disabled>
              Processing...
            </button>
          )}

          {status === 'success' && (
            <button className="modal-btn-primary" onClick={handleDone}>
              View transactions
            </button>
          )}

          {status === 'error' && (
            <>
              <button className="modal-btn-secondary" onClick={handleClose}>
                Cancel
              </button>
              <button className="modal-btn-primary" onClick={reset}>
                Try again
              </button>
            </>
          )}
        </div>

      </div>
    </div>
  );
}
