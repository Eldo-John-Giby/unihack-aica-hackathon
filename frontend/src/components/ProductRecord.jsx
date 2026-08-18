import { useMemo } from 'react';
import './ProductRecord.css';

function getConfidenceLevel(confidence) {
  if (confidence > 85) return 'high';
  if (confidence >= 60) return 'medium';
  return 'low';
}

function getConfidenceColor(confidence) {
  if (confidence > 85) return 'green';
  if (confidence >= 60) return 'yellow';
  return 'red';
}

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}

function ProductRecord({ data, onFieldClick }) {
  const fields = useMemo(() => {
    if (!data?.fields) return [];
    return Object.entries(data.fields).map(([name, fieldData]) => ({
      name,
      ...fieldData,
    }));
  }, [data]);

  const stats = useMemo(() => {
    const total = fields.length;
    const extracted = fields.filter(f => f.source === 'extracted').length;
    const inferred = fields.filter(f => f.source === 'inferred').length;
    const avgConfidence = total > 0
      ? Math.round(fields.reduce((sum, f) => sum + f.confidence, 0) / total)
      : 0;
    const hasConflicts = fields.some(f => f.conflicts?.length > 0);

    return { total, extracted, inferred, avgConfidence, hasConflicts };
  }, [fields]);

  if (!data) {
    return (
      <div className="record-empty">
        <p>No product data available</p>
      </div>
    );
  }

  return (
    <div className="product-record">
      {/* Product Header */}
      <div className="record-header">
        <div className="record-header-main">
          <span className="record-id">{data.product_id}</span>
          <h2 className="record-title">
            {data.fields.product_name?.value || 'Untitled Product'}
          </h2>
          {data.fields.brand?.value && (
            <span className="record-brand">{data.fields.brand.value}</span>
          )}
        </div>

        {/* Stats Bar */}
        <div className="record-stats">
          <div className="stat">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Fields</span>
          </div>
          <div className="stat">
            <span className="stat-value stat-extracted">{stats.extracted}</span>
            <span className="stat-label">Extracted</span>
          </div>
          <div className="stat">
            <span className="stat-value stat-inferred">{stats.inferred}</span>
            <span className="stat-label">Inferred</span>
          </div>
          <div className="stat">
            <span className={`stat-value stat-confidence ${getConfidenceColor(stats.avgConfidence)}`}>
              {stats.avgConfidence}%
            </span>
            <span className="stat-label">Avg Confidence</span>
          </div>
          {stats.hasConflicts && (
            <div className="stat stat-warning">
              <span className="stat-value">⚠️</span>
              <span className="stat-label">Conflicts</span>
            </div>
          )}
        </div>
      </div>

      {/* Fields Grid */}
      <div className="fields-grid">
        {fields.map((field) => (
          <FieldCard
            key={field.name}
            field={field}
            onClick={() => onFieldClick(field.name, field)}
          />
        ))}
      </div>
    </div>
  );
}

function FieldCard({ field, onClick }) {
  const confidenceLevel = getConfidenceLevel(field.confidence);
  const confidenceColor = getConfidenceColor(field.confidence);
  const hasConflicts = field.conflicts?.length > 0;
  const unresolvedConflicts = field.conflicts?.filter(c => !c.resolved) || [];

  return (
    <button
      className={`field-card ${hasConflicts ? 'has-conflicts' : ''}`}
      onClick={onClick}
    >
      <div className="field-card-header">
        <span className="field-name">{field.name.replace(/_/g, ' ')}</span>
        <div className="field-badges">
          {field.source === 'inferred' && (
            <span className="badge badge-inferred" title="Inferred field">INFERRED</span>
          )}
          {hasConflicts && unresolvedConflicts.length > 0 && (
            <span className="badge badge-conflict" title="Has unresolved conflicts">
              {unresolvedConflicts.length} CONFLICT{unresolvedConflicts.length > 1 ? 'S' : ''}
            </span>
          )}
          <span className={`badge badge-confidence badge-${confidenceColor}`} title={`Confidence: ${field.confidence}%`}>
            {field.confidence}%
          </span>
        </div>
      </div>

      <div className="field-card-value">
        {formatValue(field.value)}
      </div>

      <div className="field-card-footer">
        <span className="field-source-doc" title={field.source_doc}>
          📄 {field.source_doc}
        </span>
        <span className="field-click-hint">
          Click to trace →
        </span>
      </div>
    </button>
  );
}

export default ProductRecord;
