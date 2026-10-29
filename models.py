from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

class Metric(Base):
    __tablename__ = 'metrics'
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String(20), nullable=False)
    revenue = Column(Float, default=0)       # Superstore Sales
    sales = Column(Integer, default=0)       # Superstore Quantity
    customers = Column(Integer, default=0)   # Unique customers in month
    conversion = Column(Float, default=0)    # Profit margin % for compatibility with existing dashboard

class SuperstoreOrder(Base):
    __tablename__ = 'superstore_orders'
    id = Column(Integer, primary_key=True, index=True)
    row_id = Column(Integer, index=True)
    order_id = Column(String(50), index=True)
    order_date = Column(DateTime, index=True)
    ship_date = Column(DateTime)
    ship_mode = Column(String(80))
    customer_id = Column(String(50), index=True)
    customer_name = Column(String(160))
    segment = Column(String(80), index=True)
    country = Column(String(100))
    city = Column(String(100))
    state = Column(String(100), index=True)
    postal_code = Column(String(30))
    region = Column(String(80), index=True)
    product_id = Column(String(80), index=True)
    category = Column(String(100), index=True)
    sub_category = Column(String(100), index=True)
    product_name = Column(Text)
    sales_amount = Column(Float, default=0)
    quantity = Column(Integer, default=0)
    discount = Column(Float, default=0)
    profit = Column(Float, default=0)

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
