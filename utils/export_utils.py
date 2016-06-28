import pandas as pd
import os
from datetime import datetime
import logging
from models.database import db, Facility, Commodity, StockBalance, Prediction, Alert, StockMovement

logger = logging.getLogger(__name__)

class ExportUtils:
    """Utility class for exporting data and generating sample files"""
    
    def __init__(self):
        self.export_dir = 'exports'
        self.sample_dir = 'sample_data'
        
        # Create directories if they don't exist
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.sample_dir, exist_ok=True)
    
    def export_predictions(self):
        """Export predictions to CSV"""
        try:
            predictions = db.session.query(Prediction, Facility, Commodity).join(
                Facility, Prediction.facility_id == Facility.id
            ).join(
                Commodity, Prediction.commodity_id == Commodity.id
            ).all()
            
            data = []
            for pred, facility, commodity in predictions:
                data.append({
                    'facility_code': facility.facility_code,
                    'facility_name': facility.facility_name,
                    'commodity_code': commodity.commodity_code,
                    'commodity_name': commodity.commodity_name,
                    'prediction_date': pred.prediction_date,
                    'predicted_stock_out_date': pred.predicted_stock_out_date,
                    'confidence_score': pred.confidence_score,
                    'risk_level': pred.risk_level,
                    'model_used': pred.model_used,
                    'created_at': pred.created_at
                })
            
            df = pd.DataFrame(data)
            filename = f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_dir, filename)
            df.to_csv(filepath, index=False)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting predictions: {e}")
            raise
    
    def export_alerts(self):
        """Export alerts to CSV"""
        try:
            alerts = db.session.query(Alert, Facility, Commodity).join(
                Facility, Alert.facility_id == Facility.id
            ).join(
                Commodity, Alert.commodity_id == Commodity.id
            ).all()
            
            data = []
            for alert, facility, commodity in alerts:
                data.append({
                    'facility_code': facility.facility_code,
                    'facility_name': facility.facility_name,
                    'commodity_code': commodity.commodity_code,
                    'commodity_name': commodity.commodity_name,
                    'alert_type': alert.alert_type,
                    'alert_level': alert.alert_level,
                    'message': alert.message,
                    'is_resolved': alert.is_resolved,
                    'created_at': alert.created_at,
                    'resolved_at': alert.resolved_at
                })
            
            df = pd.DataFrame(data)
            filename = f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_dir, filename)
            df.to_csv(filepath, index=False)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting alerts: {e}")
            raise
    
    def export_stock_balances(self):
        """Export stock balances to CSV"""
        try:
            balances = db.session.query(StockBalance, Facility, Commodity).join(
                Facility, StockBalance.facility_id == Facility.id
            ).join(
                Commodity, StockBalance.commodity_id == Commodity.id
            ).all()
            
            data = []
            for balance, facility, commodity in balances:
                data.append({
                    'facility_code': facility.facility_code,
                    'facility_name': facility.facility_name,
                    'commodity_code': commodity.commodity_code,
                    'commodity_name': commodity.commodity_name,
                    'current_stock': balance.current_stock,
                    'reorder_level': balance.reorder_level,
                    'maximum_stock': balance.maximum_stock,
                    'last_updated': balance.last_updated
                })
            
            df = pd.DataFrame(data)
            filename = f"stock_balances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_dir, filename)
            df.to_csv(filepath, index=False)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting stock balances: {e}")
            raise
    
    def generate_sample_data(self, data_type):
        """Generate sample data files for download"""
        try:
            if data_type == 'facilities':
                return self._generate_sample_facilities()
            elif data_type == 'commodities':
                return self._generate_sample_commodities()
            elif data_type == 'stock_movements':
                return self._generate_sample_stock_movements()
            elif data_type == 'stock_balances':
                return self._generate_sample_stock_balances()
            elif data_type == 'service_volumes':
                return self._generate_sample_service_volumes()
            elif data_type == 'lead_times':
                return self._generate_sample_lead_times()
            else:
                raise ValueError(f"Unknown data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            raise
    
    def _generate_sample_facilities(self):
        """Generate sample facilities data"""
        data = [
            {
                'facility_code': 'HC001',
                'facility_name': 'Kampala Central Health Center',
                'district': 'Kampala',
                'region': 'Central',
                'facility_type': 'Health Center'
            },
            {
                'facility_code': 'HC002',
                'facility_name': 'Jinja Regional Hospital',
                'district': 'Jinja',
                'region': 'Eastern',
                'facility_type': 'Hospital'
            },
            {
                'facility_code': 'HC003',
                'facility_name': 'Mbarara Referral Hospital',
                'district': 'Mbarara',
                'region': 'Western',
                'facility_type': 'Referral Hospital'
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_facilities.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_sample_commodities(self):
        """Generate sample commodities data"""
        data = [
            {
                'commodity_code': 'ARV001',
                'commodity_name': 'Tenofovir/Lamivudine/Dolutegravir (TLD)',
                'commodity_type': 'ARV',
                'unit_of_measure': 'Tablets'
            },
            {
                'commodity_code': 'ARV002',
                'commodity_name': 'Efavirenz 600mg',
                'commodity_type': 'ARV',
                'unit_of_measure': 'Tablets'
            },
            {
                'commodity_code': 'VAC001',
                'commodity_name': 'BCG Vaccine',
                'commodity_type': 'Vaccine',
                'unit_of_measure': 'Vials'
            },
            {
                'commodity_code': 'VAC002',
                'commodity_name': 'DPT-HepB-Hib',
                'commodity_type': 'Vaccine',
                'unit_of_measure': 'Vials'
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_commodities.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_sample_stock_movements(self):
        """Generate sample stock movements data"""
        data = [
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV001',
                'movement_type': 'RECEIPT',
                'quantity': 5000,
                'unit_cost': 0.50,
                'movement_date': '2024-01-15',
                'reference_number': 'PO-2024-001'
            },
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV001',
                'movement_type': 'ISSUE',
                'quantity': 100,
                'unit_cost': 0.50,
                'movement_date': '2024-01-16',
                'reference_number': 'IS-2024-001'
            },
            {
                'facility_code': 'HC002',
                'commodity_code': 'VAC001',
                'movement_type': 'RECEIPT',
                'quantity': 200,
                'unit_cost': 2.00,
                'movement_date': '2024-01-15',
                'reference_number': 'PO-2024-002'
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_stock_movements.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_sample_stock_balances(self):
        """Generate sample stock balances data"""
        data = [
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV001',
                'current_stock': 4500,
                'reorder_level': 1000,
                'maximum_stock': 10000
            },
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV002',
                'current_stock': 800,
                'reorder_level': 500,
                'maximum_stock': 2000
            },
            {
                'facility_code': 'HC002',
                'commodity_code': 'VAC001',
                'current_stock': 150,
                'reorder_level': 50,
                'maximum_stock': 500
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_stock_balances.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_sample_service_volumes(self):
        """Generate sample service volumes data"""
        data = [
            {
                'facility_code': 'HC001',
                'service_type': 'HIV',
                'volume_count': 150,
                'reporting_period': '2024-01-01'
            },
            {
                'facility_code': 'HC001',
                'service_type': 'Immunization',
                'volume_count': 300,
                'reporting_period': '2024-01-01'
            },
            {
                'facility_code': 'HC002',
                'service_type': 'HIV',
                'volume_count': 200,
                'reporting_period': '2024-01-01'
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_service_volumes.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath
    
    def _generate_sample_lead_times(self):
        """Generate sample lead times data"""
        data = [
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV001',
                'supplier': 'National Medical Stores',
                'average_lead_time_days': 30
            },
            {
                'facility_code': 'HC001',
                'commodity_code': 'ARV002',
                'supplier': 'National Medical Stores',
                'average_lead_time_days': 25
            },
            {
                'facility_code': 'HC002',
                'commodity_code': 'VAC001',
                'supplier': 'UNICEF',
                'average_lead_time_days': 45
            }
        ]
        
        df = pd.DataFrame(data)
        filename = "sample_lead_times.csv"
        filepath = os.path.join(self.sample_dir, filename)
        df.to_csv(filepath, index=False)
        
        return filepath

