# AI Business Copilot — Professional Animated Version

A web dashboard for business analytics with a built-in **AI assistant**. It loads the Sample Superstore sales data into a database, shows the key numbers on a dashboard, and lets you ask questions about them in plain language. It is a semester project for the Data Science Tools course (8th semester).

## What it does

- **Accounts:** sign up and log in (passwords hashed with bcrypt, a signed JWT in the session).
- **Dashboard:** KPI cards (revenue, quantity sold, unique customers, average profit margin, average order value), growth against the previous month, best and lowest month, a simple next-month revenue forecast, and animated monthly revenue bars.
- **AI Business Copilot:** a chat panel on the right side of the dashboard. Your chat history is saved per user.
- **Insights:** automatic written insights built from the figures (best and lowest month, growth, margin advice).
- **PDF report:** downloads a business-intelligence report of the current figures.
- **Pages:** home, services, about, contact and settings, in a glass-style animated design.

## How the assistant answers

- **Without an API key** it uses built-in rules: it recognises topics such as revenue, sales, customers, profit and margin, forecast and marketing, and answers from the current database figures.
- **With `OPENAI_API_KEY` in `.env`** it sends your question, the last 10 messages and a summary of the dashboard figures to an OpenAI model (`gpt-4o-mini` by default, change it with `OPENAI_MODEL`) for fuller answers. If the call fails it falls back to the built-in rules.

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

Default login:

```text
admin@example.com
change-me-password
```

## Where is the AI Business Copilot?

Login and open `/dashboard`. The AI Business Copilot is shown on the right side of the dashboard. It also works through the `/api/ask` endpoint.

## Main endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/`, `/about`, `/services`, `/contact` | Public pages |
| GET / POST | `/login`, `/signup`, GET `/logout` | Accounts |
| GET | `/dashboard`, `/settings` | Pages for signed-in users |
| GET | `/api/metrics`, `/api/insights` | Dashboard figures and written insights (JSON) |
| POST | `/api/ask` | Ask the assistant a question |
| GET | `/api/chats` | Your saved chat history |
| GET | `/report/pdf` | Download the PDF report |

## Tech stack

Python, FastAPI, Jinja2 templates, SQLAlchemy with SQLite, passlib (bcrypt) and python-jose (JWT), OpenAI SDK (optional), ReportLab for the PDF, plain CSS and JavaScript for the interface.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | FastAPI routes, dashboard figures, PDF report |
| `ai_service.py` | The assistant: built-in answers, insights and the OpenAI call |
| `auth.py` | Password hashing and login tokens |
| `database.py`, `models.py` | Database setup and tables (users, monthly metrics, Superstore orders) |
| `seed.py` | Resets the database and imports `Sample-Superstore.csv` |
| `templates/`, `static/` | Pages, styles and scripts |
| `.env.example` | The settings you can put in `.env` |

## Status and limitations

- The data is the public Sample Superstore dataset, so the figures describe that dataset, not a real company.
- The forecast is a simple continuation of the latest growth; it is directional only.
- `python seed.py` resets the dashboard data (it keeps the existing login user).
- Set a long random `SECRET_KEY` in `.env` and change the default login before putting this on a server.
- The built-in assistant is rule-based; real conversational answers need an OpenAI key.
