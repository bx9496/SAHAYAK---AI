# SAHAYAK AI Integrated Prototype

A single Flask website integrating Login + KYC, Dark/Light theme, AI Government Life Manager, OCR + ReCorrect, Scheme Eligibility, profile storage and reminders.

## Run
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python app.py

Open http://127.0.0.1:5000

## Render
Build: pip install -r requirements.txt
Start: gunicorn app:app

Set OPENAI_API_KEY, OPENAI_MODEL, FLASK_SECRET_KEY.

OCR uses Tesseract.js in the browser, so no Google Vision credentials are required for the demo.
SQLite is used for the hackathon prototype. Use managed PostgreSQL for production.


## Multilingual + database update
SQLite now stores users, KYC metadata, profiles, reminders, OCR scans and emergency contacts. OCR supports English (`eng`), Hindi (`hin`) and Odia (`ori`). Extracted OCR can be translated to English, Hindi or Odia using the OpenAI API when configured. OCR text and translations are saved per logged-in user. Emergency contact and optional medical notes are stored per user. For real deployment, use managed PostgreSQL, HTTPS, encryption, access controls and an authorized KYC provider.
