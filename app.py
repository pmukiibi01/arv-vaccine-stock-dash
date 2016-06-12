import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from models.database import db, Facility, Commodity, StockMovement, StockBalance, ServiceVolume, LeadTime, Prediction, Alert
from models.predictor import StockOutPredictor
from utils.data_processor import DataProcessor
from utils.export_utils import ExportUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///stockout.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize utilities
    data_processor = DataProcessor()
    predictor = StockOutPredictor()
    export_utils = ExportUtils()
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('index.html')
    
    @app.route('/api/dashboard/stats')
    def dashboard_stats():
        """Get dashboard statistics"""
        try:
            total_facilities = Facility.query.count()
            total_commodities = Commodity.query.count()
            active_alerts = Alert.query.filter_by(is_resolved=False).count()
            
            # Get recent predictions
            recent_predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all()
            
            stats = {
                'total_facilities': total_facilities,
                'total_commodities': total_commodities,
                'active_alerts': active_alerts,
                'recent_predictions': [
                    {
                        'facility_name': pred.facility.facility_name,
                        'commodity_name': pred.commodity.commodity_name,
                        'predicted_date': pred.predicted_stock_out_date.isoformat() if pred.predicted_stock_out_date else None,
                        'risk_level': pred.risk_level,
                        'confidence': float(pred.confidence_score) if pred.confidence_score else None
                    }
                    for pred in recent_predictions
                ]
            }
            
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/facilities')
    def get_facilities():
        """Get all facilities"""
        try:
            facilities = Facility.query.all()
            return jsonify([{
                'id': f.id,
                'facility_code': f.facility_code,
                'facility_name': f.facility_name,
                'district': f.district,
                'region': f.region,
                'facility_type': f.facility_type
            } for f in facilities])
        except Exception as e:
            logger.error(f"Error getting facilities: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/commodities')
    def get_commodities():
        """Get all commodities"""
        try:
            commodities = Commodity.query.all()
            return jsonify([{
                'id': c.id,
                'commodity_code': c.commodity_code,
                'commodity_name': c.commodity_name,
                'commodity_type': c.commodity_type,
                'unit_of_measure': c.unit_of_measure
            } for c in commodities])
        except Exception as e:
            logger.error(f"Error getting commodities: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/stock-balances')
    def get_stock_balances():
        """Get current stock balances"""
        try:
            balances = db.session.query(StockBalance, Facility, Commodity).join(
                Facility, StockBalance.facility_id == Facility.id
            ).join(
                Commodity, StockBalance.commodity_id == Commodity.id
            ).all()
            
            return jsonify([{
                'facility_name': f.facility_name,
                'commodity_name': c.commodity_name,
                'current_stock': float(b.current_stock),
                'reorder_level': float(b.reorder_level),
                'maximum_stock': float(b.maximum_stock),
                'stock_status': 'LOW' if b.current_stock <= b.reorder_level else 'OK'
            } for b, f, c in balances])
        except Exception as e:
            logger.error(f"Error getting stock balances: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/predictions', methods=['GET', 'POST'])
    def predictions():
        """Get or generate predictions"""
        if request.method == 'GET':
            try:
                facility_id = request.args.get('facility_id', type=int)
                commodity_id = request.args.get('commodity_id', type=int)
                
                query = Prediction.query
                if facility_id:
                    query = query.filter_by(facility_id=facility_id)
                if commodity_id:
                    query = query.filter_by(commodity_id=commodity_id)
                
                predictions = query.order_by(Prediction.created_at.desc()).limit(100).all()
                
                return jsonify([{
                    'id': p.id,
                    'facility_name': p.facility.facility_name,
                    'commodity_name': p.commodity.commodity_name,
                    'prediction_date': p.prediction_date.isoformat(),
                    'predicted_stock_out_date': p.predicted_stock_out_date.isoformat() if p.predicted_stock_out_date else None,
                    'confidence_score': float(p.confidence_score) if p.confidence_score else None,
                    'risk_level': p.risk_level,
                    'model_used': p.model_used,
                    'created_at': p.created_at.isoformat()
                } for p in predictions])
            except Exception as e:
                logger.error(f"Error getting predictions: {e}")
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                facility_id = data.get('facility_id')
                commodity_id = data.get('commodity_id')
                
                if not facility_id or not commodity_id:
                    return jsonify({'error': 'facility_id and commodity_id are required'}), 400
                
                # Generate prediction
                prediction_result = predictor.predict_stock_out(facility_id, commodity_id)
                
                # Save prediction to database
                prediction = Prediction(
                    facility_id=facility_id,
                    commodity_id=commodity_id,
                    prediction_date=datetime.now().date(),
                    predicted_stock_out_date=prediction_result.get('predicted_date'),
                    confidence_score=prediction_result.get('confidence'),
                    risk_level=prediction_result.get('risk_level'),
                    model_used=prediction_result.get('model')
                )
                
                db.session.add(prediction)
                db.session.commit()
                
                return jsonify(prediction_result)
            except Exception as e:
                logger.error(f"Error generating prediction: {e}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/alerts')
    def get_alerts():
        """Get all alerts"""
        try:
            alerts = db.session.query(Alert, Facility, Commodity).join(
                Facility, Alert.facility_id == Facility.id
            ).join(
                Commodity, Alert.commodity_id == Commodity.id
            ).order_by(Alert.created_at.desc()).all()
            
            return jsonify([{
                'id': a.id,
                'facility_name': f.facility_name,
                'commodity_name': c.commodity_name,
                'alert_type': a.alert_type,
                'alert_level': a.alert_level,
                'message': a.message,
                'is_resolved': a.is_resolved,
                'created_at': a.created_at.isoformat(),
                'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None
            } for a, f, c in alerts])
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/upload', methods=['POST'])
    def upload_data():
        """Upload and process data files"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Process the uploaded file
            result = data_processor.process_uploaded_file(file)
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/<export_type>')
    def export_data(export_type):
        """Export data in various formats"""
        try:
            if export_type == 'predictions':
                file_path = export_utils.export_predictions()
            elif export_type == 'alerts':
                file_path = export_utils.export_alerts()
            elif export_type == 'stock_balances':
                file_path = export_utils.export_stock_balances()
            else:
                return jsonify({'error': 'Invalid export type'}), 400
            
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/sample-data/<data_type>')
    def download_sample_data(data_type):
        """Download sample data files"""
        try:
            file_path = export_utils.generate_sample_data(data_type)
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
