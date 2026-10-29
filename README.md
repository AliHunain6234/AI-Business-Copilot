# AI Business Copilot — Professional Animated Version

This package includes the AI Business Copilot inside the `/dashboard` page as a visible right-side AI panel. The web UI has been upgraded with a professional glass design, animated hero section, responsive navigation, KPI cards, animated revenue bars, AI chat panel, and PDF report link.

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed.py
python app.py
```

Open `http://127.0.0.1:8000`

Login: `admin@aibusiness.com`. No password is stored in the code. Set `ADMIN_PASSWORD` in `.env` before `python seed.py`, or use the random one `seed.py` prints (shown once). Also set a long random `SECRET_KEY` in `.env`; without it a random key is used and everyone is logged out on restart.

## Where is the AI Business Copilot?

Login and open `/dashboard`. The AI Business Copilot is shown on the right side of the dashboard. It also works through the `/api/ask` endpoint.
