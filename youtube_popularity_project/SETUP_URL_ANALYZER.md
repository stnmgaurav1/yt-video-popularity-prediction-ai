# YouTube URL Analyzer setup (Windows PowerShell)

1. Open VS Code in this folder (the folder containing `app.py`).
2. Check `py --version`. If missing, install Python from python.org, restart VS Code.
3. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. In Google Cloud Console, create/select a project, enable **YouTube Data API v3**, create an API key under Credentials, and restrict it appropriately. API quota and restrictions apply.
5. Create `.streamlit/secrets.toml` with:

```toml
YOUTUBE_API_KEY = "AIzaSyDh_ZB6RHs2DuPkpozUzJ67_ibRcoxbjec"
```

6. Run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

7. Paste a public YouTube watch/Shorts URL and click Analyze video.

**Important:** Never commit `.streamlit/secrets.toml` or your API key to GitHub. The bundled trained model uses synthetic data; its accuracy on real videos is unknown. Some public videos have hidden or unavailable like counts. Repeated/trending video observations need careful grouping for honest model evaluation.
