from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Facility(db.Model):
    __tablename__ = 'facilities'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_code = db.Column(db.String(50), unique=True, nullable=False)
    facility_name = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    facility_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_balances = db.relationship('StockBalance', backref='facility', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='facility', lazy=True)
    service_volumes = db.relationship('ServiceVolume', backref='facility', lazy=True)
    lead_times = db.relationship('LeadTime', backref='facility', lazy=True)
    predictions = db.relationship('Prediction', backref='facility', lazy=True)
    alerts = db.relationship('Alert', backref='facility', lazy=True)

class Commodity(db.Model):
    __tablename__ = 'commodities'
    
    id = db.Column(db.Integer, primary_key=True)
    commodity_code = db.Column(db.String(50), unique=True, nullable=False)
    commodity_name = db.Column(db.String(255), nullable=False)
    commodity_type = db.Column(db.String(50), nullable=False)  # ARV, Vaccine, etc.
    unit_of_measure = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_balances = db.relationship('StockBalance', backref='commodity', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='commodity', lazy=True)
    lead_times = db.relationship('LeadTime', backref='commodity', lazy=True)
    predictions = db.relationship('Prediction', backref='commodity', lazy=True)
    alerts = db.relationship('Alert', backref='commodity', lazy=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # ISSUE, RECEIPT, ADJUSTMENT
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    movement_date = db.Column(db.Date, nullable=False)
    reference_number = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StockBalance(db.Model):
    __tablename__ = 'stock_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities.id'), nullable=False)
    current_stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    reorder_level = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    maximum_stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('facility_id', 'commodity_id'),)

class ServiceVolume(db.Model):
    __tablename__ = 'service_volumes'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # HIV, Immunization, etc.
    volume_count = db.Column(db.Integer, nullable=False)
    reporting_period = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeadTime(db.Model):
    __tablename__ = 'lead_times'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities.id'), nullable=False)
    supplier = db.Column(db.String(100), nullable=False)
    average_lead_time_days = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities.id'), nullable=False)
    prediction_date = db.Column(db.Date, nullable=False)
    predicted_stock_out_date = db.Column(db.Date)
    confidence_score = db.Column(db.Numeric(5, 2))
    risk_level = db.Column(db.String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    model_used = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    commodity_id = db.Column(db.Integer, db.ForeignKey('commodities.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # STOCK_OUT, LOW_STOCK, REORDER
    alert_level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, CRITICAL
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

