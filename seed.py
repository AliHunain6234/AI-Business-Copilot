from pathlib import Path
import csv
import os
import secrets
from datetime import datetime
from collections import defaultdict

from database import Base, engine, SessionLocal
from models import User, Metric, SuperstoreOrder
from auth import hash_password, normalize_email

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / 'Sample-Superstore.csv'


def parse_date(value):
    if not value:
        return None
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f'Unsupported date format: {value}')


def to_float(value):
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def to_int(value):
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Keep login user, but delete old dashboard/sample data.
    email = normalize_email('admin@aibusiness.com')
    user = db.query(User).filter(User.email == email).first()
    # The admin password is never stored in the code: ADMIN_PASSWORD from .env, else a random one shown once below.
    admin_password = os.getenv('ADMIN_PASSWORD', '').strip()
    password_generated = not admin_password
    if password_generated:
        admin_password = secrets.token_urlsafe(9)
    created_admin = user is None
    if not user:
        db.add(User(name='Business Admin', email=email, password_hash=hash_password(admin_password)))
    else:
        user.name = user.name or 'Business Admin'

    db.query(Metric).delete()
    db.query(SuperstoreOrder).delete()
    db.commit()

    if not CSV_PATH.exists():
        raise FileNotFoundError(f'Missing dataset: {CSV_PATH}')

    monthly = defaultdict(lambda: {'sales_amount': 0.0, 'quantity': 0, 'profit': 0.0, 'customers': set()})
    count = 0

    with CSV_PATH.open('r', encoding='latin-1', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            order_date = parse_date(row.get('Order Date'))
            ship_date = parse_date(row.get('Ship Date'))
            sales_amount = to_float(row.get('Sales'))
            quantity = to_int(row.get('Quantity'))
            profit = to_float(row.get('Profit'))
            customer_id = row.get('Customer ID', '').strip()

            db.add(SuperstoreOrder(
                row_id=to_int(row.get('Row ID')),
                order_id=row.get('Order ID', '').strip(),
                order_date=order_date,
                ship_date=ship_date,
                ship_mode=row.get('Ship Mode', '').strip(),
                customer_id=customer_id,
                customer_name=row.get('Customer Name', '').strip(),
                segment=row.get('Segment', '').strip(),
                country=row.get('Country', '').strip(),
                city=row.get('City', '').strip(),
                state=row.get('State', '').strip(),
                postal_code=str(row.get('Postal Code', '')).strip(),
                region=row.get('Region', '').strip(),
                product_id=row.get('Product ID', '').strip(),
                category=row.get('Category', '').strip(),
                sub_category=row.get('Sub-Category', '').strip(),
                product_name=row.get('Product Name', '').strip(),
                sales_amount=sales_amount,
                quantity=quantity,
                discount=to_float(row.get('Discount')),
                profit=profit,
            ))

            key = order_date.strftime('%Y-%m')
            monthly[key]['sales_amount'] += sales_amount
            monthly[key]['quantity'] += quantity
            monthly[key]['profit'] += profit
            if customer_id:
                monthly[key]['customers'].add(customer_id)
            count += 1

            if count % 1000 == 0:
                db.commit()

    for month in sorted(monthly):
        item = monthly[month]
        revenue = round(item['sales_amount'], 2)
        margin = round((item['profit'] / revenue) * 100, 2) if revenue else 0
        db.add(Metric(
            month=month,
            revenue=revenue,
            sales=item['quantity'],
            customers=len(item['customers']),
            conversion=margin,
        ))

    db.commit()
    print(f'Database reset successfully. Loaded {count:,} Superstore order rows and {len(monthly):,} monthly metric rows.')
    if created_admin and password_generated:
        print(f'Admin login created: admin@aibusiness.com / {admin_password}   (shown once: save it, or set ADMIN_PASSWORD in .env and seed again)')
    elif created_admin:
        print('Admin login created: admin@aibusiness.com with the password from ADMIN_PASSWORD in .env')
    else:
        print('Existing admin login kept: admin@aibusiness.com (password unchanged)')
finally:
    db.close()
