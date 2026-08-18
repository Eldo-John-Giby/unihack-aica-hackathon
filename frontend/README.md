# Product Intelligence Frontend

A React-based UI for the Product Intelligence Pipeline that displays structured product data with full provenance tracking.

## Features

- **Upload Screen**: Drag-and-drop or click-to-browse file upload interface
- **Product Record View**: Clean card layout showing all product fields with confidence badges
- **Field Provenance Panel**: Click any field to see detailed source information:
  - Source document & location
  - Confidence score with visual bar
  - Reasoning for extraction/inference
  - Conflict resolution status
- **Confidence Badges**: Color-coded indicators (green >85%, yellow 60-85%, red <60%)
- **Inferred Field Tags**: Clear visual distinction between extracted and inferred data

## Quick Start

### Prerequisites
- Node.js 18+ (recommended: 20+)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

This starts the Vite dev server at `http://localhost:5173` with hot reload.

### Production Build

```bash
npm run build
npm run preview
```

Build output is in `dist/` folder. Preview serves the production build locally.

## Project Structure

```
/frontend
├── mock_data/              # Mock product records (matches /shared/schema.json)
│   ├── product_001.json   # High-confidence consumer electronics
│   ├── product_002.json   # Mixed confidence with conflicts
│   └── product_003.json   # Tech product with multiple conflicts
├── src/
│   ├── components/
│   │   ├── UploadScreen.jsx      # File upload with drag-and-drop
│   │   ├── UploadScreen.css
│   │   ├── ProductRecord.jsx     # Product field cards with badges
│   │   ├── ProductRecord.css
│   │   ├── FieldProvenance.jsx   # Provenance side panel
│   │   └── FieldProvenance.css
│   ├── config.js          # ⚡ API_BASE_URL constant here
│   ├── App.jsx            # Main app with state management
│   ├── App.css
│   ├── main.jsx           # React entry point
│   └── index.css          # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## API Integration

### The One-Line Change

Open `src/config.js` and update the `API_BASE_URL`:

```javascript
// Change this:
export const API_BASE_URL = 'http://localhost:3001/api';

// And set USE_MOCK_DATA to false:
export const USE_MOCK_DATA = false;
```

That's it. The app will now make real API calls instead of loading mock data.

### Expected API Endpoints

When `USE_MOCK_DATA = false`, the app expects:

**POST `/api/products/extract`**
- Request: `multipart/form-data` with files
- Response: Product record JSON matching `/shared/schema.json`

Example response:
```json
{
  "product_id": "PROD-001",
  "fields": {
    "product_name": {
      "value": "Product Name",
      "source": "extracted",
      "source_doc": "document.pdf",
      "source_location": "Page 1, Header",
      "confidence": 95,
      "reasoning": "Extracted from document header",
      "conflicts": []
    }
  }
}
```

### Mock Data

In demo mode (`USE_MOCK_DATA = true`), the app loads from `/mock_data/` folder.
These files follow the exact same schema as the real API response.

To test with different mock data, edit or add files in `mock_data/` folder.
Update `MOCK_DATA_PATHS` array in `config.js` to include new files.

## Mock Data Files

| File | Description |
|------|-------------|
| `product_001.json` | Sony headphones - high confidence, 1 conflict |
| `product_002.json` | Matcha tea - mixed confidence, multiple conflicts |
| `product_003.json` | 4K monitor - various confidence levels, 3 conflicts |

All mock data matches `/shared/schema.json` exactly.

## UI Interactions

### Upload Flow
1. Drag files onto the dropzone OR click to browse
2. Selected files appear in the dropzone
3. Click "Analyze Documents" to process
4. OR click "View Demo Product" to load random mock data

### Product Record View
- **Fields Grid**: All product fields shown as cards
- **Confidence Badge**: Top-right of each card (green/yellow/red)
- **Inferred Tag**: Purple badge for inferred fields
- **Conflict Badge**: Yellow badge showing number of conflicts
- **Hover Effect**: Cards lift on hover, "Click to trace →" appears

### Field Provenance Panel
- **Click any field card** → Side panel slides in from right
- **Value Display**: Large, clear value with source/confidence badges
- **Confidence Bar**: Visual progress bar showing confidence level
- **Source Document**: Filename with document icon
- **Location**: Page/section where value was found
- **Reasoning**: Explanation of extraction or inference logic
- **Conflicts**: 
  - Resolved conflicts shown in green with "Accepted" status
  - Unresolved conflicts shown in yellow with "Rejected" status
- **Close**: Click ✕ button, press Escape, or click outside panel

## Technical Notes

### State Management
- React useState for simplicity (no Redux needed for this scope)
- App component manages: current view, product data, selected field
- Components receive data via props, emit events via callbacks

### Styling
- CSS custom properties (variables) for theming
- BEM-like class naming
- Responsive grid layout (adapts to screen size)
- Smooth animations (fade-in, slide-in, hover transitions)

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ features
- CSS Grid and Flexbox

## Development

### Adding New Fields
Mock data files in `mock_data/` follow the schema. To add fields:

1. Edit the JSON file directly
2. Or use the existing structure as template
3. Ensure all required fields are present per schema

### Customizing Confidence Thresholds
Edit `getConfidenceColor()` function in:
- `ProductRecord.jsx` (for card badges)
- `FieldProvenance.jsx` (for panel display)

Default thresholds:
- Green: > 85%
- Yellow: 60-85%
- Red: < 60%

### Adding New Views
1. Create component in `src/components/`
2. Add route/state in `App.jsx`
3. Import and render conditionally based on view state

## Troubleshooting

### "Cannot find module" errors
```bash
rm -rf node_modules
npm install
```

### Port already in use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### Mock data not loading
- Ensure `mock_data/` folder exists with JSON files
- Check browser console for fetch errors
- Verify file paths in `config.js` match actual file locations

### Build fails
```bash
# Clear cache and rebuild
rm -rf dist node_modules/.vite
npm run build
```

## Future Enhancements

- [ ] Real-time upload progress indicator
- [ ] Batch upload support with queue
- [ ] Field editing and manual override
- [ ] Export to CSV/Excel
- [ ] Search/filter fields
- [ ] Keyboard navigation
- [ ] Dark/light theme toggle
- [ ] Unit tests with Vitest

## License

Internal use only - Product Intelligence Pipeline
