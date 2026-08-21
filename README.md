# SAHAYAK AI
## Setup
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Create `.env` by copying `.env.example`.
4. Add `OPENAI_API_KEY`.
5. For OCR, create a Google Cloud service account, enable Cloud Vision API, download its JSON key and set `GOOGLE_APPLICATION_CREDENTIALS` to the full path.
6. In VS Code terminal:
   `python -m venv .venv`
   Windows: `.venv\Scripts\activate`
   `pip install -r requirements.txt`
   `python app.py`
7. Open `http://127.0.0.1:5000`

Profiles and reminders are stored locally in JSON files for the hackathon demo. Do not use this local storage approach for production personal data.
