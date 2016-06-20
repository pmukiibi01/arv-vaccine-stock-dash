import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
from prophet import Prophet
import logging
from models.database import db, StockMovement, StockBalance, ServiceVolume, LeadTime

logger = logging.getLogger(__name__)

class StockOutPredictor:
    """Stock-out prediction using multiple ML models"""
    
    def __init__(self):
        self.models = {
            'xgboost': None,
            'prophet': None,
            'random_forest': None
        }
        self.feature_importance = {}
    
    def prepare_features(self, facility_id, commodity_id, lookback_days=90):
        """Prepare features for prediction"""
        try:
            # Get stock movements for the last lookback_days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=lookback_days)
            
            movements = StockMovement.query.filter(
                StockMovement.facility_id == facility_id,
                StockMovement.commodity_id == commodity_id,
                StockMovement.movement_date >= start_date,
                StockMovement.movement_date <= end_date
            ).order_by(StockMovement.movement_date).all()
            
            if not movements:
                return None, None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': m.movement_date,
                'quantity': float(m.quantity),
                'movement_type': m.movement_type,
                'unit_cost': float(m.unit_cost) if m.unit_cost else 0
            } for m in movements])
            
            # Get current stock balance
            balance = StockBalance.query.filter_by(
                facility_id=facility_id,
                commodity_id=commodity_id
            ).first()
            
            if not balance:
                return None, None
            
            # Get service volumes
            service_volumes = ServiceVolume.query.filter(
                ServiceVolume.facility_id == facility_id,
                ServiceVolume.reporting_period >= start_date
            ).all()
            
            # Get lead times
            lead_time = LeadTime.query.filter_by(
                facility_id=facility_id,
                commodity_id=commodity_id
            ).first()
            
            # Create features
            features = self._create_features(df, balance, service_volumes, lead_time)
            
            return features, df
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None, None
    
    def _create_features(self, df, balance, service_volumes, lead_time):
        """Create feature matrix"""
        features = {}
        
        # Always create basic stock level features
        features['current_stock'] = float(balance.current_stock)
        features['reorder_level'] = float(balance.reorder_level)
        features['max_stock'] = float(balance.maximum_stock)
        features['stock_ratio'] = features['current_stock'] / features['max_stock'] if features['max_stock'] > 0 else 0
        
        # Stock movement features
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Daily consumption (issues)
            issues = df[df['movement_type'] == 'ISSUE']['quantity']
            receipts = df[df['movement_type'] == 'RECEIPT']['quantity']
            
            # Calculate consumption patterns
            features['avg_daily_consumption'] = issues.mean() if not issues.empty else 0
            features['consumption_std'] = issues.std() if not issues.empty else 0
            features['consumption_trend'] = self._calculate_trend(issues)
            features['receipt_frequency'] = len(receipts) / 90  # receipts per day
            
            # Stock level features (already created above)
            
            # Service volume features
            if service_volumes:
                total_volume = sum(sv.volume_count for sv in service_volumes)
                features['avg_service_volume'] = total_volume / len(service_volumes)
            else:
                features['avg_service_volume'] = 0
            
            # Lead time features
            if lead_time:
                features['avg_lead_time'] = lead_time.average_lead_time_days
            else:
                features['avg_lead_time'] = 30  # default
            
            # Time-based features
            features['day_of_week'] = datetime.now().weekday()
            features['month'] = datetime.now().month
            
            # Calculate days until stock-out
            if features['avg_daily_consumption'] > 0:
                features['days_until_stockout'] = features['current_stock'] / features['avg_daily_consumption']
            else:
                features['days_until_stockout'] = 365  # large number if no consumption
        else:
            # Default values when no movement data
            features['avg_daily_consumption'] = 0
            features['consumption_std'] = 0
            features['consumption_trend'] = 0
            features['receipt_frequency'] = 0
            features['avg_service_volume'] = 0
            features['avg_lead_time'] = 30
            features['day_of_week'] = datetime.now().weekday()
            features['month'] = datetime.now().month
            features['days_until_stockout'] = 365
        
        return features
    
    def _calculate_trend(self, series):
        """Calculate trend in consumption"""
        if len(series) < 2:
            return 0
        
        x = np.arange(len(series))
        y = series.values
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def train_xgboost_model(self, X, y):
        """Train XGBoost model"""
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            
            logger.info(f"XGBoost MAE: {mae:.2f}, MSE: {mse:.2f}")
            
            self.models['xgboost'] = model
            self.feature_importance['xgboost'] = dict(zip(X.columns, model.feature_importances_))
            
            return model
            
        except Exception as e:
            logger.error(f"Error training XGBoost model: {e}")
            return None
    
    def train_prophet_model(self, df):
        """Train Prophet model for time series forecasting"""
        try:
            if df.empty:
                return None
            
            # Prepare data for Prophet
            prophet_df = df.reset_index()
            prophet_df = prophet_df.rename(columns={'date': 'ds', 'quantity': 'y'})
            
            # Filter for issues only
            prophet_df = prophet_df[prophet_df['movement_type'] == 'ISSUE']
            
            if len(prophet_df) < 10:
                return None
            
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )
            
            model.fit(prophet_df)
            self.models['prophet'] = model
            
            return model
            
        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return None
    
    def predict_stock_out(self, facility_id, commodity_id):
        """Predict stock-out date for a facility-commodity combination"""
        try:
            features, df = self.prepare_features(facility_id, commodity_id)
            
            if features is None:
                return {
                    'error': 'Insufficient data for prediction',
                    'predicted_date': None,
                    'confidence': 0,
                    'risk_level': 'UNKNOWN',
                    'model': 'none'
                }
            
            # Use rule-based prediction as fallback
            days_until_stockout = features.get('days_until_stockout', 365)
            avg_lead_time = features.get('avg_lead_time', 30)
            
            # Calculate risk level
            if days_until_stockout <= avg_lead_time:
                risk_level = 'CRITICAL'
                confidence = 0.9
            elif days_until_stockout <= avg_lead_time * 1.5:
                risk_level = 'HIGH'
                confidence = 0.8
            elif days_until_stockout <= avg_lead_time * 2:
                risk_level = 'MEDIUM'
                confidence = 0.7
            else:
                risk_level = 'LOW'
                confidence = 0.6
            
            # Predict stock-out date
            predicted_date = datetime.now().date() + timedelta(days=int(days_until_stockout))
            
            return {
                'predicted_date': predicted_date.isoformat(),
                'confidence': confidence,
                'risk_level': risk_level,
                'model': 'rule_based',
                'days_until_stockout': int(days_until_stockout),
                'current_stock': features.get('current_stock', 0),
                'avg_daily_consumption': features.get('avg_daily_consumption', 0),
                'avg_lead_time': avg_lead_time
            }
            
        except Exception as e:
            logger.error(f"Error predicting stock-out: {e}")
            return {
                'error': str(e),
                'predicted_date': None,
                'confidence': 0,
                'risk_level': 'UNKNOWN',
                'model': 'error'
            }
    
    def batch_predict(self, facility_commodity_pairs):
        """Predict stock-outs for multiple facility-commodity pairs"""
        results = []
        
        for facility_id, commodity_id in facility_commodity_pairs:
            result = self.predict_stock_out(facility_id, commodity_id)
            result['facility_id'] = facility_id
            result['commodity_id'] = commodity_id
            results.append(result)
        
        return results
    
    def get_feature_importance(self, model_name='xgboost'):
        """Get feature importance for a specific model"""
        return self.feature_importance.get(model_name, {})
    
    def evaluate_model(self, model_name, X_test, y_test):
        """Evaluate model performance"""
        model = self.models.get(model_name)
        if model is None:
            return None
        
        try:
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            
            return {
                'mae': mae,
                'mse': mse,
                'rmse': rmse,
                'model': model_name
            }
        except Exception as e:
            logger.error(f"Error evaluating model {model_name}: {e}")
            return None
