import { useState, useCallback } from 'react';
import './App.css';
import { API_BASE_URL, USE_MOCK_DATA, MOCK_DATA_PATHS } from './config';
import UploadScreen from './components/UploadScreen';
import ProductRecord from './components/ProductRecord';
import FieldProvenance from './components/FieldProvenance';

function App() {
  const [view, setView] = useState('upload'); // 'upload' | 'record'
  const [productData, setProductData] = useState(null);
  const [selectedField, setSelectedField] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = useCallback(async (files) => {
    setIsLoading(true);
    setError(null);

    try {
      if (USE_MOCK_DATA) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 800));

        // Load a random mock product
        const randomIndex = Math.floor(Math.random() * MOCK_DATA_PATHS.length);
        const response = await fetch(MOCK_DATA_PATHS[randomIndex]);
        const data = await response.json();
        setProductData(data);
        setView('record');
      } else {
        // Real API call
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));

        const response = await fetch(`${API_BASE_URL}/products/extract`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        setProductData(data);
        setView('record');
      }
    } catch (err) {
      setError(err.message || 'Failed to process upload');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleFieldClick = useCallback((fieldName, fieldData) => {
    setSelectedField({ name: fieldName, ...fieldData });
  }, []);

  const handleCloseProvenance = useCallback(() => {
    setSelectedField(null);
  }, []);

  const handleBackToUpload = useCallback(() => {
    setView('upload');
    setProductData(null);
    setSelectedField(null);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <h1 className="app-title">
            <span className="app-title-icon">🔍</span>
            Product Intelligence
          </h1>
          <p className="app-subtitle">Structured Product Data Pipeline</p>
        </div>
        {view === 'record' && (
          <button className="btn-back" onClick={handleBackToUpload}>
            ← New Upload
          </button>
        )}
      </header>

      <main className="app-main">
        {view === 'upload' && (
          <UploadScreen
            onUpload={handleUpload}
            isLoading={isLoading}
            error={error}
          />
        )}

        {view === 'record' && productData && (
          <ProductRecord
            data={productData}
            onFieldClick={handleFieldClick}
          />
        )}
      </main>

      {selectedField && (
        <FieldProvenance
          field={selectedField}
          onClose={handleCloseProvenance}
        />
      )}
    </div>
  );
}

export default App;
