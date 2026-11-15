# TubeScope — YouTube Video Analytics and Likes Estimator

A complete Streamlit application built from the original YouTube Video Popularity Prediction coursework project.

## Features
- YouTube URL / Shorts / live / youtu.be parsing
- YouTube Data API v3: title, thumbnail, channel, publish date, views, likes, comments, duration, tags
- Random Forest likes estimate using views, duration (seconds), and tag count
- Actual vs estimated likes chart, error, ratios, CSV export
- Manual prediction, saved model evaluation dashboard, feature importance
- Friendly API errors and API key security

## Requirements
Python 3.10+ and an internet connection for YouTube API lookup. Tested with Python 3.11-compatible dependencies.

## Windows setup (PowerShell)
Open the project folder (the one containing `app.py`) in VS Code.

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If `py` is missing, install Python from https://www.python.org/downloads/ and restart VS Code. You may use `python` in place of `py` if available.

## Set up the YouTube API
1. Go to https://console.cloud.google.com/ and create/select a Google Cloud project.
2. Enable **YouTube Data API v3** in APIs & Services → Library.
3. Create an API key under APIs & Services → Credentials. Restrict the key to YouTube Data API v3 and configure suitable application restrictions.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder with your key. Keep the file private.
5. Restart Streamlit and open the **Video analyzer** tab.

Alternatively, set the `YOUTUBE_API_KEY` environment variable.

## Retrain the bundled demonstration model

```powershell
.\.venv\Scripts\python.exe train.py --data data/youtube_sample.csv
```

**Important:** The bundled model and saved evaluation were trained on synthetic sample data. Do not claim these metrics represent real-world YouTube accuracy. The provided `IN_youtube_trending_data.csv` does not contain duration, so it cannot be passed directly to the existing training pipeline. For a meaningful production model, collect real video durations and use time-based or video-grouped holdout testing.

## Project layout

```
app.py                       Streamlit dashboard
 youtube_api.py              YouTube Data API client + URL parser
 src/pipeline.py             Feature preparation, training and prediction
 train.py                    Model training entry point
 models/random_forest.joblib Bundled educational model
 data/                       Original datasets
 outputs/                    Saved evaluation results and figures
 .streamlit/secrets.toml.example API key template
 tests/test_core.py          Standard-library unit tests
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Deployment
Deploy to Streamlit Community Cloud from a GitHub repository. Select `app.py` as the entry point, and add `YOUTUBE_API_KEY = "..."` in the Streamlit Cloud Secrets settings. Never upload `secrets.toml`.

## Privacy and limitations
The app calls the official YouTube Data API only when you submit a URL. The model predicts likes using already-observed view counts; it is not a pre-upload virality forecast. Actual like counts and comments may be unavailable. YouTube API usage is subject to Google quotas and terms.
