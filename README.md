# Minu's Jobfit Resume

Streamlit app that tailors a user's resume to a specific job description, highlights changes, and optionally generates a cover letter.

## Files in this repo
- `app.py` - Streamlit app
- `requirements.txt` - Python dependencies
- `.gitignore`
- `.streamlit/secrets.toml` - example local secrets (DO NOT commit real keys)

## Quick local setup
1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate       # Windows (PowerShell)
pip install -r requirements.txt
```

2. Add your OpenAI key locally for testing:
Create a file `.streamlit/secrets.toml` with:
```
OPENAI_API_KEY = "sk-REPLACE_WITH_YOUR_KEY"
```

3. Run the app:
```bash
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io and create a new app, selecting this repository and `app.py`.
3. In the Streamlit Cloud app settings, add a secret named `OPENAI_API_KEY` with your key.
4. Deploy. The app will read the key from `st.secrets` automatically.

## Security note
- Never commit real secrets to the repo. Use Streamlit's Secrets Manager for deployment.
- This app does text processing: avoid uploading sensitive documents to public deployments unless you understand the privacy implications.