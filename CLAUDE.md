# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SPIS-ML** (Seismic Performance Intelligent System) is an interactive Dash dashboard for seismic data analysis and machine learning modeling. It provides real-time USGS earthquake monitoring, geographic visualization, statistical modeling (Gutenberg-Richter, log regression), LSTM predictions, model comparison, density analysis, and PDF/CSV report generation.

## Tech Stack

- **Framework**: Dash (Plotly) - interactive web dashboard
- **Backend**: Python 3.8+
- **Data**: Pandas, NumPy, Scikit-learn, Plotly
- **ML**: TensorFlow/Keras (LSTM models)
- **Reports**: FPDF2, Plotly Kaleido
- **Server**: Gunicorn + Flask
- **Data Format**: Parquet (optimized binary) internally, CSV input

## Architecture

```
dashboard/
├── app.py                          # Dash app entry point, routing (Landing → Dashboard)
├── preprocessor.py                 # CSV → Parquet converter, memory optimization
├── modules/
│   ├── data_handler.py            # Global state: stores preprocessed DataFrame
│   ├── home_module.py             # Landing page, file upload, USGS integration
│   ├── exploration_module.py      # Interactive maps, geographic filtering
│   ├── model_Gutenberg_Richter_module.py  # a-b parameter calculation
│   ├── model_log_regression_module.py     # Magnitude prediction model
│   ├── model_lstm_prediction_module.py    # LSTM sequence prediction (TensorFlow)
│   ├── model_comparison_module.py         # Multi-algorithm performance eval
│   ├── density_module.py          # Heat maps, spatial clustering
│   └── reports_module.py          # PDF/CSV export, summary stats
├── assets/                         # CSS/static resources
└── data/                          # Runtime: uploaded CSVs, parquet files
```

### Data Flow

1. **User uploads CSV** → `app.py` extracts base64 → saves to `data/` folder
2. **Preprocessor** (`preprocessor.py`):
   - Reads CSV, normalizes column names (lowercase, mag vs magnitude)
   - Converts timestamps to UTC (handles mixed timezone errors)
   - Downsamples floats to float32 (50% memory savings)
   - Writes to `sismos_optimizado.parquet` using Snappy compression
3. **Global state** (`data_handler.py`):
   - Single module-level `_data` variable holds the preprocessed DataFrame
   - `get_data()` called by each module to retrieve it
4. **Module rendering**:
   - Each analysis module is a callback that reads `data_handler.get_data()` and returns a Dash component tree
   - Callbacks in `home_module.py` register USGS real-time updates (60s polling)

### Module Details

- **home_module.py** (22KB): Landing page UI, file upload handler, USGS API calls, glossary modal, citation generator
- **exploration_module.py**: Interactive Mapbox scatter, magnitude/depth/time filters
- **model_*_module.py**: Each fits a distinct algorithm (GR, log-reg, LSTM, comparison) and returns plots + metrics
- **reports_module.py**: PDF generation with charts, CSV export of filtered data
- **density_module.py**: Heatmaps using Plotly density_contour, cluster detection

### Key Design Patterns

- **Single global DataFrame**: `data_handler._data` persists across requests. Set via `data_handler.set_data(df)` in preprocessor callback.
- **No async/threading**: Dash callbacks are synchronous; long-running tasks block. USGS updates are 60s interval (acceptable latency).
- **Callback routing**: App phase state (0=Landing, 1=Dashboard) controls which view renders. Tab switches trigger tab-content callbacks.
- **Parquet over CSV**: CSV bloat (600MB+) solved by downsampling to float32 and compressing to Parquet (~100MB).

## Development

### Setup

```bash
cd dashboard
python3 -m venv sismos_dashboard
source sismos_dashboard/bin/activate
pip install -r requirements.txt
```

### Run Dev Server

```bash
python app.py
```

Server runs on `http://127.0.0.1:8050/` with hot-reload enabled.

### Test a Module Independently

Each module exports a render function:
```python
from modules.exploration_module import render_exploration_view
view = render_exploration_view()  # Returns dbc.Container(...)
```

To debug a specific callback, add print statements in the callback function and check terminal output.

### Input Data Format

CSV must contain these columns (case-insensitive):
```
time, latitude, longitude, depth, mag  [, date, place, ...]
```

Example:
```csv
time,latitude,longitude,depth,mag
2024-01-15T10:30:00.000Z,-33.4489,70.6693,25.5,4.2
2024-01-15T15:45:30.000Z,-36.8485,73.0544,15.2,3.8
```

Preprocessor handles mixed `date`+`time` columns and missing values.

## Common Tasks

### Add a New Analysis Module

1. Create `modules/model_my_analysis_module.py`
2. Export a `render_my_analysis_view()` function that takes a DataFrame and returns a `dbc.Container(...)`
3. In `app.py`, add a new tab and callback case:
   ```python
   dbc.Tab(label="My Analysis", tab_id="tab-myanalysis"),
   # In render_tab_content():
   elif active_tab == "tab-myanalysis": return render_my_analysis_view()
   ```

### Modify the Landing Page

Edit `home_module.py`. The `render_home_module()` function returns the UI tree. Register callbacks with `register_home_callbacks(app)` in the module.

### Update USGS Integration

`home_module.py` fetches earthquakes from `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson`. Modify the `update_usgs_feed()` callback to change polling interval or data source.

### Deploy to Production

The `server` variable in `app.py` is the Flask app:
```bash
gunicorn -w 4 -b 0.0.0.0:8050 app:server
```

Render/Heroku auto-detects and uses `Procfile` if present. Set env vars for custom ports.

## Testing

Unit tests are referenced in README but not yet implemented. Use pytest when available:
```bash
pytest tests/
```

Manual testing: upload a sample CSV, verify each tab renders, check console for errors.

## Known Constraints

- **No authentication**: Public-facing for USGS data. Add Flask-Login for multi-user support.
- **Single process**: Dash runs single-threaded. Heavy ML training blocks the UI. Consider Celery for async jobs.
- **In-memory state**: Refreshing the page resets `data_handler._data`. Use browser session storage or database for persistence.
- **LSTM training**: TensorFlow loads entire dataset into memory. Float32 downsampling is critical for large catalogs.

## Debugging Tips

- Check `data_handler.get_data()` shape in a callback to confirm data loaded correctly.
- Use Dash `dcc.Loading()` wrapper (already in place) to show status while rendering slow tabs.
- USGS feed fails silently if network is down; home_module fallback returns cached data.
- Parquet read errors often come from column mismatches; check preprocessor.py stdout.
