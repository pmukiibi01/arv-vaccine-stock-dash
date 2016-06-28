import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from models.database import db, Facility, Commodity, StockMovement, StockBalance, ServiceVolume, LeadTime, Alert

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and validate uploaded data files"""
    
    def __init__(self):
        self.required_columns = {
            'facilities': ['facility_code', 'facility_name', 'district', 'region', 'facility_type'],
            'commodities': ['commodity_code', 'commodity_name', 'commodity_type', 'unit_of_measure'],
            'stock_movements': ['facility_code', 'commodity_code', 'movement_type', 'quantity', 'movement_date'],
            'stock_balances': ['facility_code', 'commodity_code', 'current_stock', 'reorder_level', 'maximum_stock'],
            'service_volumes': ['facility_code', 'service_type', 'volume_count', 'reporting_period'],
            'lead_times': ['facility_code', 'commodity_code', 'supplier', 'average_lead_time_days']
        }
    
    def process_uploaded_file(self, file):
        """Process uploaded CSV file"""
        try:
            # Read the file
            df = pd.read_csv(file)
            
            # Determine file type based on columns
            file_type = self._identify_file_type(df.columns)
            
            if not file_type:
                return {'error': 'Unknown file format. Please check column headers.'}
            
            # Validate required columns
            missing_columns = self._validate_columns(df, file_type)
            if missing_columns:
                return {'error': f'Missing required columns: {missing_columns}'}
            
            # Process based on file type
            if file_type == 'facilities':
                result = self._process_facilities(df)
            elif file_type == 'commodities':
                result = self._process_commodities(df)
            elif file_type == 'stock_movements':
                result = self._process_stock_movements(df)
            elif file_type == 'stock_balances':
                result = self._process_stock_balances(df)
            elif file_type == 'service_volumes':
                result = self._process_service_volumes(df)
            elif file_type == 'lead_times':
                result = self._process_lead_times(df)
            else:
                return {'error': 'Unsupported file type'}
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            return {'error': str(e)}
    
    def _identify_file_type(self, columns):
        """Identify file type based on columns"""
        for file_type, required_cols in self.required_columns.items():
            if all(col in columns for col in required_cols):
                return file_type
        return None
    
    def _validate_columns(self, df, file_type):
        """Validate required columns are present"""
        required_cols = self.required_columns.get(file_type, [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        return missing_cols
    
    def _process_facilities(self, df):
        """Process facilities data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Check if facility already exists
                    existing = Facility.query.filter_by(facility_code=row['facility_code']).first()
                    
                    if existing:
                        # Update existing facility
                        existing.facility_name = row['facility_name']
                        existing.district = row['district']
                        existing.region = row['region']
                        existing.facility_type = row['facility_type']
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new facility
                        facility = Facility(
                            facility_code=row['facility_code'],
                            facility_name=row['facility_name'],
                            district=row['district'],
                            region=row['region'],
                            facility_type=row['facility_type']
                        )
                        db.session.add(facility)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} facilities'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing facilities: {e}")
            return {'error': str(e)}
    
    def _process_commodities(self, df):
        """Process commodities data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Check if commodity already exists
                    existing = Commodity.query.filter_by(commodity_code=row['commodity_code']).first()
                    
                    if existing:
                        # Update existing commodity
                        existing.commodity_name = row['commodity_name']
                        existing.commodity_type = row['commodity_type']
                        existing.unit_of_measure = row['unit_of_measure']
                        existing.updated_at = datetime.utcnow()
                    else:
                        # Create new commodity
                        commodity = Commodity(
                            commodity_code=row['commodity_code'],
                            commodity_name=row['commodity_name'],
                            commodity_type=row['commodity_type'],
                            unit_of_measure=row['unit_of_measure']
                        )
                        db.session.add(commodity)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} commodities'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing commodities: {e}")
            return {'error': str(e)}
    
    def _process_stock_movements(self, df):
        """Process stock movements data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Get facility and commodity IDs
                    facility = Facility.query.filter_by(facility_code=row['facility_code']).first()
                    commodity = Commodity.query.filter_by(commodity_code=row['commodity_code']).first()
                    
                    if not facility:
                        errors.append(f"Row {len(errors) + 1}: Facility {row['facility_code']} not found")
                        continue
                    
                    if not commodity:
                        errors.append(f"Row {len(errors) + 1}: Commodity {row['commodity_code']} not found")
                        continue
                    
                    # Parse movement date
                    movement_date = pd.to_datetime(row['movement_date']).date()
                    
                    # Create stock movement
                    movement = StockMovement(
                        facility_id=facility.id,
                        commodity_id=commodity.id,
                        movement_type=row['movement_type'],
                        quantity=row['quantity'],
                        unit_cost=row.get('unit_cost', 0),
                        movement_date=movement_date,
                        reference_number=row.get('reference_number', '')
                    )
                    db.session.add(movement)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} stock movements'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing stock movements: {e}")
            return {'error': str(e)}
    
    def _process_stock_balances(self, df):
        """Process stock balances data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Get facility and commodity IDs
                    facility = Facility.query.filter_by(facility_code=row['facility_code']).first()
                    commodity = Commodity.query.filter_by(commodity_code=row['commodity_code']).first()
                    
                    if not facility:
                        errors.append(f"Row {len(errors) + 1}: Facility {row['facility_code']} not found")
                        continue
                    
                    if not commodity:
                        errors.append(f"Row {len(errors) + 1}: Commodity {row['commodity_code']} not found")
                        continue
                    
                    # Check if balance already exists
                    existing = StockBalance.query.filter_by(
                        facility_id=facility.id,
                        commodity_id=commodity.id
                    ).first()
                    
                    if existing:
                        # Update existing balance
                        existing.current_stock = row['current_stock']
                        existing.reorder_level = row['reorder_level']
                        existing.maximum_stock = row['maximum_stock']
                        existing.last_updated = datetime.utcnow()
                    else:
                        # Create new balance
                        balance = StockBalance(
                            facility_id=facility.id,
                            commodity_id=commodity.id,
                            current_stock=row['current_stock'],
                            reorder_level=row['reorder_level'],
                            maximum_stock=row['maximum_stock']
                        )
                        db.session.add(balance)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} stock balances'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing stock balances: {e}")
            return {'error': str(e)}
    
    def _process_service_volumes(self, df):
        """Process service volumes data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Get facility ID
                    facility = Facility.query.filter_by(facility_code=row['facility_code']).first()
                    
                    if not facility:
                        errors.append(f"Row {len(errors) + 1}: Facility {row['facility_code']} not found")
                        continue
                    
                    # Parse reporting period
                    reporting_period = pd.to_datetime(row['reporting_period']).date()
                    
                    # Create service volume
                    volume = ServiceVolume(
                        facility_id=facility.id,
                        service_type=row['service_type'],
                        volume_count=row['volume_count'],
                        reporting_period=reporting_period
                    )
                    db.session.add(volume)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} service volumes'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing service volumes: {e}")
            return {'error': str(e)}
    
    def _process_lead_times(self, df):
        """Process lead times data"""
        try:
            processed = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    # Get facility and commodity IDs
                    facility = Facility.query.filter_by(facility_code=row['facility_code']).first()
                    commodity = Commodity.query.filter_by(commodity_code=row['commodity_code']).first()
                    
                    if not facility:
                        errors.append(f"Row {len(errors) + 1}: Facility {row['facility_code']} not found")
                        continue
                    
                    if not commodity:
                        errors.append(f"Row {len(errors) + 1}: Commodity {row['commodity_code']} not found")
                        continue
                    
                    # Check if lead time already exists
                    existing = LeadTime.query.filter_by(
                        facility_id=facility.id,
                        commodity_id=commodity.id,
                        supplier=row['supplier']
                    ).first()
                    
                    if existing:
                        # Update existing lead time
                        existing.average_lead_time_days = row['average_lead_time_days']
                        existing.last_updated = datetime.utcnow()
                    else:
                        # Create new lead time
                        lead_time = LeadTime(
                            facility_id=facility.id,
                            commodity_id=commodity.id,
                            supplier=row['supplier'],
                            average_lead_time_days=row['average_lead_time_days']
                        )
                        db.session.add(lead_time)
                    
                    processed += 1
                    
                except Exception as e:
                    errors.append(f"Row {len(errors) + 1}: {str(e)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors,
                'message': f'Successfully processed {processed} lead times'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing lead times: {e}")
            return {'error': str(e)}
    
    def generate_alerts(self):
        """Generate alerts based on current stock levels"""
        try:
            alerts_created = 0
            
            # Get all stock balances
            balances = StockBalance.query.all()
            
            for balance in balances:
                # Check if stock is below reorder level
                if balance.current_stock <= balance.reorder_level:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter_by(
                        facility_id=balance.facility_id,
                        commodity_id=balance.commodity_id,
                        alert_type='LOW_STOCK',
                        is_resolved=False
                    ).first()
                    
                    if not existing_alert:
                        # Create new alert
                        alert = Alert(
                            facility_id=balance.facility_id,
                            commodity_id=balance.commodity_id,
                            alert_type='LOW_STOCK',
                            alert_level='WARNING' if balance.current_stock > 0 else 'CRITICAL',
                            message=f"Stock level ({balance.current_stock}) is below reorder level ({balance.reorder_level})"
                        )
                        db.session.add(alert)
                        alerts_created += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'alerts_created': alerts_created,
                'message': f'Generated {alerts_created} new alerts'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error generating alerts: {e}")
            return {'error': str(e)}

