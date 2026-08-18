import { useState, useCallback, useRef } from 'react';
import './UploadScreen.css';

function UploadScreen({ onUpload, isLoading, error }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      setSelectedFiles(files);
    }
  }, []);

  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
  }, []);

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleSubmit = useCallback(() => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles);
    }
  }, [selectedFiles, onUpload]);

  const handleDemoClick = useCallback(() => {
    onUpload([]);
  }, [onUpload]);

  return (
    <div className="upload-screen">
      <div className="upload-container">
        <div
          className={`upload-dropzone ${isDragOver ? 'drag-over' : ''} ${selectedFiles.length > 0 ? 'has-files' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.csv,.xlsx,.xls,.json,.txt,.doc,.docx"
            onChange={handleFileSelect}
            className="file-input"
          />

          <div className="upload-icon">
            {isDragOver ? '📥' : '📄'}
          </div>

          <div className="upload-text">
            {isDragOver ? (
              <p className="upload-text-primary">Drop files here</p>
            ) : selectedFiles.length > 0 ? (
              <>
                <p className="upload-text-primary">
                  {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
                </p>
                <p className="upload-text-secondary">
                  {selectedFiles.map(f => f.name).join(', ')}
                </p>
              </>
            ) : (
              <>
                <p className="upload-text-primary">
                  Drag & drop product source documents
                </p>
                <p className="upload-text-secondary">
                  or click to browse • PDF, CSV, Excel, JSON, TXT
                </p>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="upload-error">
            <span className="upload-error-icon">⚠️</span>
            {error}
          </div>
        )}

        <div className="upload-actions">
          {selectedFiles.length > 0 && (
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Processing...
                </>
              ) : (
                <>
                  Analyze Documents
                  <span className="btn-icon">→</span>
                </>
              )}
            </button>
          )}

          <button
            className="btn-demo"
            onClick={handleDemoClick}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Loading Demo...
              </>
            ) : (
              'View Demo Product'
            )}
          </button>
        </div>

        <div className="upload-hint">
          <p>
            💡 <strong>Tip:</strong> In demo mode, this loads a sample product record from mock data.
            Connect the real API to analyze your actual documents.
          </p>
        </div>
      </div>
    </div>
  );
}

export default UploadScreen;
