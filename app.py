from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from database import Base, engine, get_db
from models import User, Metric, ChatLog
from auth import verify_password, create_token, decode_token, hash_password, normalize_email
from ai_service import ask_ai, generate_business_insights

BASE_DIR = Path(__file__).resolve().parent
Base.metadata.create_all(bind=engine)

app = FastAPI(title='AI Business Copilot', version='3.0.0')
app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))


def current_user(request: Request, db: Session):
    token = request.cookies.get('access_token')
    if not token:
        return None
    data = decode_token(token)
    if not data or not data.get('sub'):
        return None
    return db.query(User).filter(User.email == normalize_email(data.get('sub'))).first()


def pct_change(current, previous):
    if not previous:
        return 0
    return round(((current - previous) / previous) * 100, 1)


def dashboard_context(db: Session):
    rows = db.query(Metric).order_by(Metric.id.asc()).all()
    months = [
        {'month': r.month, 'revenue': float(r.revenue or 0), 'sales': int(r.sales or 0),
         'customers': int(r.customers or 0), 'conversion': float(r.conversion or 0)}
        for r in rows
    ]
    latest = months[-1] if months else {'revenue': 0, 'sales': 0, 'customers': 0, 'conversion': 0}
    previous = months[-2] if len(months) >= 2 else {'revenue': 0, 'sales': 0, 'customers': 0, 'conversion': 0}
    total_revenue = sum(m['revenue'] for m in months)
    total_sales = sum(m['sales'] for m in months)
    avg_conversion = round(sum(m['conversion'] for m in months) / len(months), 2) if months else 0
    best_month = max(months, key=lambda x: x['revenue'], default=None)
    lowest_month = min(months, key=lambda x: x['revenue'], default=None)
    average_order_value = round(total_revenue / total_sales, 2) if total_sales else 0
    revenue_growth = pct_change(latest['revenue'], previous['revenue'])
    sales_growth = pct_change(latest['sales'], previous['sales'])
    customer_growth = pct_change(latest['customers'], previous['customers'])
    next_revenue_forecast = round(latest['revenue'] * (1 + revenue_growth / 100), 2) if latest else 0

    return {
        'revenue': total_revenue,
        'sales': total_sales,
        'customers': latest['customers'],
        'conversion': avg_conversion,
        'growth': revenue_growth,
        'sales_growth': sales_growth,
        'customer_growth': customer_growth,
        'average_order_value': average_order_value,
        'best_month': best_month,
        'lowest_month': lowest_month,
        'forecast_next_revenue': next_revenue_forecast,
        'months': months,
    }


def render(request: Request, db: Session, template: str, **context):
    context.setdefault('user', current_user(request, db))
    context['request'] = request
    return templates.TemplateResponse(template, context)


@app.get('/', response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'home.html')

@app.get('/about', response_class=HTMLResponse)
def about(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'about.html')

@app.get('/services', response_class=HTMLResponse)
def services(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'services.html')

@app.get('/contact', response_class=HTMLResponse)
def contact(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'contact.html')

@app.get('/settings', response_class=HTMLResponse)
def settings(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse('/login', status_code=303)
    return render(request, db, 'settings.html', user=user)

@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'login.html', message=None)

@app.post('/login', response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    email = normalize_email(email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse('login.html', {
            'request': request, 'message': 'Invalid email or password.', 'user': None, 'email': email
        }, status_code=401)
    response = RedirectResponse('/dashboard', status_code=303)
    response.set_cookie('access_token', create_token({'sub': user.email}), httponly=True, samesite='lax', max_age=60*60*24)
    return response

@app.get('/signup', response_class=HTMLResponse)
def signup_page(request: Request, db: Session = Depends(get_db)):
    return render(request, db, 'signup.html', message=None)

@app.post('/signup', response_class=HTMLResponse)
def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    name = (name or '').strip()
    email = normalize_email(email)
    if len(name) < 2:
        return templates.TemplateResponse('signup.html', {'request': request, 'message': 'Please enter your full name.', 'user': None, 'name': name, 'email': email}, status_code=400)
    if len(password) < 6:
        return templates.TemplateResponse('signup.html', {'request': request, 'message': 'Password must be at least 6 characters.', 'user': None, 'name': name, 'email': email}, status_code=400)
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse('signup.html', {'request': request, 'message': 'An account already exists with this email. Please login.', 'user': None, 'email': email}, status_code=409)
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    response = RedirectResponse('/dashboard', status_code=303)
    response.set_cookie('access_token', create_token({'sub': user.email}), httponly=True, samesite='lax', max_age=60*60*24)
    return response

@app.get('/logout')
def logout():
    response = RedirectResponse('/', status_code=303)
    response.delete_cookie('access_token')
    return response

@app.get('/dashboard', response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse('/login', status_code=303)
    context = dashboard_context(db)
    insights = generate_business_insights(context)
    return render(request, db, 'dashboard.html', user=user, data=context, insights=insights)

@app.get('/api/metrics')
def api_metrics(db: Session = Depends(get_db)):
    return dashboard_context(db)

@app.get('/api/insights')
def api_insights(db: Session = Depends(get_db)):
    return {'insights': generate_business_insights(dashboard_context(db))}

@app.post('/api/ask')
async def api_ask(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    question = (body.get('question') or '').strip()
    history = body.get('history') or []
    if not question:
        raise HTTPException(status_code=400, detail='Question is required')

    user = current_user(request, db)
    context = dashboard_context(db)
    answer = ask_ai(question, context, history=history)
    db.add(ChatLog(user_id=user.id if user else None, question=question, answer=answer))
    db.commit()
    return {'answer': answer}

@app.get('/api/chats')
def api_chats(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail='Login required')
    logs = db.query(ChatLog).order_by(ChatLog.created_at.desc()).limit(20).all()
    return [{'question': l.question, 'answer': l.answer, 'created_at': l.created_at.isoformat()} for l in logs]

@app.get('/report/pdf')
def pdf_report(request: Request, db: Session = Depends(get_db)):
    if not current_user(request, db):
        return RedirectResponse('/login', status_code=303)
    context = dashboard_context(db)
    insights = generate_business_insights(context)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle('AI Business Copilot Report')
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(50, 750, 'AI Business Copilot - Business Intelligence Report')
    pdf.setFont('Helvetica', 12)
    y = 710
    lines = [
        f"Total Revenue: ${context['revenue']:,.0f}",
        f"Total Sales: {context['sales']:,}",
        f"Current Customers: {context['customers']:,}",
        f"Average Profit Margin: {context['conversion']}%",
        f"Latest Revenue Growth: {context['growth']}%",
        f"Average Order Value: ${context['average_order_value']:,.2f}",
        f"Next Month Revenue Forecast: ${context['forecast_next_revenue']:,.0f}",
        '', 'Live Data Insights:'
    ] + [f"- {item}" for item in insights]
    for line in lines:
        if y < 60:
            pdf.showPage(); y = 750; pdf.setFont('Helvetica', 12)
        pdf.drawString(50, y, line[:105])
        y -= 22
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename=ai_business_report.pdf'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
