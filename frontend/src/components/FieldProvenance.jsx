import { useEffect, useCallback } from 'react';
import './FieldProvenance.css';

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function getConfidenceColor(confidence) {
  if (confidence > 85) return 'green';
  if (confidence >= 60) return 'yellow';
  return 'red';
}

function FieldProvenance({ field, onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  const confidenceColor = getConfidenceColor(field.confidence);
  const resolvedConflicts = field.conflicts?.filter(c => c.resolved) || [];
  const unresolvedConflicts = field.conflicts?.filter(c => !c.resolved) || [];

  return (
    <div className="provenance-backdrop" onClick={handleBackdropClick}>
      <div className="provenance-panel">
        {/* Header */}
        <div className="provenance-header">
          <div>
            <h2 className="provenance-title">
              {field.name.replace(/_/g, ' ')}
            </h2>
            <p className="provenance-subtitle">Field Provenance</p>
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* Value */}
        <div className="provenance-section">
          <div className="provenance-value-header">
            <span className="provenance-label">Value</span>
            <div className="provenance-badges">
              {field.source === 'inferred' && (
                <span className="badge badge-inferred">INFERRED</span>
              )}
              <span className={`badge badge-confidence badge-${confidenceColor}`}>
                {field.confidence}% confidence
              </span>
            </div>
          </div>
          <div className="provenance-value">
            {formatValue(field.value)}
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="provenance-section">
          <span className="provenance-label">Confidence Level</span>
          <div className="confidence-bar-container">
            <div className="confidence-bar">
              <div
                className={`confidence-bar-fill confidence-bar-${confidenceColor}`}
                style={{ width: `${field.confidence}%` }}
              />
            </div>
            <div className="confidence-bar-labels">
              <span>0%</span>
              <span className={`confidence-current confidence-text-${confidenceColor}`}>
                {field.confidence}%
              </span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Source */}
        <div className="provenance-section">
          <span className="provenance-label">Source Document</span>
          <div className="provenance-source-doc">
            <span className="source-doc-icon">📄</span>
            <span className="source-doc-name">{field.source_doc}</span>
          </div>
        </div>

        {/* Location */}
        <div className="provenance-section">
          <span className="provenance-label">Location in Document</span>
          <div className="provenance-location">
            <span className="location-icon">📍</span>
            <span>{field.source_location}</span>
          </div>
        </div>

        {/* Reasoning */}
        <div className="provenance-section">
          <span className="provenance-label">Reasoning</span>
          <div className="provenance-reasoning">
            {field.reasoning}
          </div>
        </div>

        {/* Conflicts */}
        {field.conflicts && field.conflicts.length > 0 && (
          <div className="provenance-section">
            <span className="provenance-label">
              Conflicts ({field.conflicts.length})
            </span>

            {resolvedConflicts.length > 0 && (
              <div className="conflicts-group">
                <span className="conflicts-group-label conflicts-resolved">
                  ✓ Resolved ({resolvedConflicts.length})
                </span>
                {resolvedConflicts.map((conflict, idx) => (
                  <div key={idx} className="conflict-item conflict-resolved">
                    <div className="conflict-value">
                      <span className="conflict-value-text">
                        {formatValue(conflict.value)}
                      </span>
                      <span className="conflict-status">Accepted</span>
                    </div>
                    <div className="conflict-source">
                      📄 {conflict.source_doc}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {unresolvedConflicts.length > 0 && (
              <div className="conflicts-group">
                <span className="conflicts-group-label conflicts-unresolved">
                  ✗ Unresolved ({unresolvedConflicts.length})
                </span>
                {unresolvedConflicts.map((conflict, idx) => (
                  <div key={idx} className="conflict-item conflict-unresolved">
                    <div className="conflict-value">
                      <span className="conflict-value-text">
                        {formatValue(conflict.value)}
                      </span>
                      <span className="conflict-status">Rejected</span>
                    </div>
                    <div className="conflict-source">
                      📄 {conflict.source_doc}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default FieldProvenance;
