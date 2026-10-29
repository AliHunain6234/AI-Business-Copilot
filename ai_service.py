import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

SYSTEM_PROMPT = """
You are AI Business Copilot, a polished ChatGPT-like assistant embedded in a business intelligence dashboard.
Answer normal questions helpfully. When dashboard or Superstore data is relevant, use the exact figures supplied in the dashboard context.
For this project, revenue means Superstore Sales, sales means Quantity sold, customers means unique customers, and conversion is used as profit margin percentage for compatibility with the existing dashboard.
Never claim live internet access unless the application provides live data. Keep answers clear, practical, executive-friendly, and action-oriented.
""".strip()


def money(value) -> str:
    return f"${float(value or 0):,.0f}"


def _context_summary(context: Dict) -> str:
    months = context.get('months', []) or []
    return (
        f"Total Superstore revenue/sales amount: {money(context.get('revenue', 0))}; "
        f"total quantity sold: {context.get('sales', 0):,}; "
        f"latest-month unique customers: {context.get('customers', 0):,}; "
        f"average profit margin: {context.get('conversion', 0)}%; "
        f"latest revenue growth: {context.get('growth', 0)}%; "
        f"quantity growth: {context.get('sales_growth', 0)}%; "
        f"customer growth: {context.get('customer_growth', 0)}%; "
        f"average order value: {money(context.get('average_order_value', 0))}; "
        f"best month: {context.get('best_month')}; "
        f"lowest month: {context.get('lowest_month')}; "
        f"next month revenue forecast: {money(context.get('forecast_next_revenue', 0))}; "
        f"monthly rows: {months}"
    )


def generate_business_insights(context: Dict) -> List[str]:
    months = context.get('months', []) or []
    if not months:
        return ['No Superstore metric rows are available yet. Run seed.py to import the CSV dataset.']
    best = context.get('best_month') or {}
    lowest = context.get('lowest_month') or {}
    growth = float(context.get('growth') or 0)
    profit_margin = float(context.get('conversion') or 0)
    aov = float(context.get('average_order_value') or 0)
    forecast = float(context.get('forecast_next_revenue') or 0)
    insights = [
        f"Best revenue month is {best.get('month')} at {money(best.get('revenue', 0))}; use its category, region, and discount pattern as the benchmark.",
        f"Lowest revenue month is {lowest.get('month')} at {money(lowest.get('revenue', 0))}; review product mix, regional demand, and discounting.",
        f"Latest revenue growth is {growth}%, based on the last two available Superstore months.",
        f"Average order value is {money(aov)}; improving bundles and high-margin product mix can lift revenue.",
        f"Next-month revenue forecast is approximately {money(forecast)} if the latest growth trend continues."
    ]
    if profit_margin < 5:
        insights.append(f"Average profit margin is {profit_margin}%; reduce unnecessary discounts and prioritize profitable categories.")
    else:
        insights.append(f"Average profit margin is {profit_margin}%; maintain margin discipline and test premium bundles.")
    return insights


def local_business_answer(question: str, context: Dict) -> str:
    q = (question or '').lower()
    insights = generate_business_insights(context)
    months = context.get('months', []) or []

    if any(word in q for word in ['dashboard', 'analytics', 'analysis', 'business performance', 'kpi', 'summary', 'overview']):
        return (
            f"Here is the current Superstore performance from the database:\n"
            f"• Total revenue/Sales amount: {money(context.get('revenue'))}\n"
            f"• Total quantity sold: {context.get('sales', 0):,}\n"
            f"• Latest-month unique customers: {context.get('customers', 0):,}\n"
            f"• Average profit margin: {context.get('conversion', 0)}%\n"
            f"• Latest revenue growth: {context.get('growth', 0)}%\n"
            f"• Average order value: {money(context.get('average_order_value'))}\n\n"
            + "\n".join(f"• {item}" for item in insights)
        )
    if any(word in q for word in ['revenue', 'income', 'earning', 'turnover', 'sales amount']):
        return f"Total Superstore revenue/Sales amount is {money(context.get('revenue'))}. Latest revenue growth is {context.get('growth', 0)}%. {insights[0]}"
    if any(word in q for word in ['sales', 'quantity', 'sell', 'pipeline']):
        return f"Total quantity sold is {context.get('sales', 0):,}. Latest quantity growth is {context.get('sales_growth', 0)}%. Month-wise metrics: {months}."
    if any(word in q for word in ['customer', 'client', 'retention']):
        return f"Latest-month unique customers are {context.get('customers', 0):,}. Customer growth is {context.get('customer_growth', 0)}%. Recommended action: segment customers, identify inactive accounts, and launch retention offers."
    if any(word in q for word in ['profit', 'margin', 'discount']):
        return f"Average profit margin is {context.get('conversion', 0)}%. Improve it through discount control, better category mix, and region-wise margin tracking."
    if any(word in q for word in ['forecast', 'predict', 'future', 'next month', 'next quarter']):
        return f"The next-month revenue forecast is {money(context.get('forecast_next_revenue'))}, assuming the latest revenue growth trend continues. Treat this as directional, not guaranteed."
    if any(word in q for word in ['marketing', 'campaign', 'advertising']):
        return "Marketing plan: segment customers, focus on high-margin categories and regions, use retargeting, collect testimonials, build email automation, and report ROI weekly against revenue and profit margin."
    if any(word in q for word in ['hello', 'hi', 'salam', 'assalam']):
        return "Hello. I am your AI Business Copilot. I can answer Superstore dashboard, strategy, marketing, analytics, writing, coding, and operational questions."

    return (
        "Here is a practical answer: define the objective, review the available Superstore data, identify constraints, compare options, "
        "choose the highest-impact action, assign ownership, and track the result with clear KPIs. For dashboard questions, "
        f"I can use current figures: revenue {money(context.get('revenue'))}, quantity sold {context.get('sales', 0):,}, "
        f"customers {context.get('customers', 0):,}, and profit margin {context.get('conversion', 0)}%. "
        "For full ChatGPT-grade answers to every topic, add OPENAI_API_KEY in the .env file."
    )


def ask_ai(question: str, context: Dict, history: Optional[List[Dict[str, str]]] = None) -> str:
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        return local_business_answer(question, context)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'system', 'content': f'Dashboard context from the application database: {_context_summary(context)}'},
        ]
        for item in (history or [])[-10:]:
            role = item.get('role')
            content = item.get('content')
            if role in {'user', 'assistant'} and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': question})
        res = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=messages,
            temperature=0.45,
            max_tokens=1200,
        )
        return res.choices[0].message.content.strip()
    except Exception as exc:
        fallback = local_business_answer(question, context)
        return f"AI service error: {exc}.\n\nFallback answer: {fallback}"
