import pytest
import pandas as pd
from datetime import datetime, date, timedelta
from models.predictor import StockOutPredictor
from models.database import db, Facility, Commodity, StockBalance, StockMovement, ServiceVolume, LeadTime

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def sample_data(app):
    """Create sample data for testing."""
    with app.app_context():
        # Create sample facility
        facility = Facility(
            facility_code='TEST001',
            facility_name='Test Health Center',
            district='Test District',
            region='Test Region',
            facility_type='Health Center'
        )
        db.session.add(facility)
        
        # Create sample commodity
        commodity = Commodity(
            commodity_code='TEST_ARV',
            commodity_name='Test ARV',
            commodity_type='ARV',
            unit_of_measure='Tablets'
        )
        db.session.add(commodity)
        
        db.session.commit()
        
        # Create stock balance
        balance = StockBalance(
            facility_id=facility.id,
            commodity_id=commodity.id,
            current_stock=1000,
            reorder_level=200,
            maximum_stock=5000
        )
        db.session.add(balance)
        
        # Create stock movements
        for i in range(30):
            movement = StockMovement(
                facility_id=facility.id,
                commodity_id=commodity.id,
                movement_type='ISSUE',
                quantity=50,
                movement_date=date.today() - timedelta(days=i)
            )
            db.session.add(movement)
        
        # Create service volume
        service_volume = ServiceVolume(
            facility_id=facility.id,
            service_type='HIV',
            volume_count=100,
            reporting_period=date.today()
        )
        db.session.add(service_volume)
        
        # Create lead time
        lead_time = LeadTime(
            facility_id=facility.id,
            commodity_id=commodity.id,
            supplier='Test Supplier',
            average_lead_time_days=30
        )
        db.session.add(lead_time)
        
        db.session.commit()
        
        return {
            'facility': facility,
            'commodity': commodity,
            'balance': balance,
            'service_volume': service_volume,
            'lead_time': lead_time
        }

def test_predictor_initialization():
    """Test StockOutPredictor initialization."""
    predictor = StockOutPredictor()
    assert predictor.models == {
        'xgboost': None,
        'prophet': None,
        'random_forest': None
    }
    assert predictor.feature_importance == {}

def test_prepare_features(app, sample_data):
    """Test feature preparation."""
    with app.app_context():
        predictor = StockOutPredictor()
        features, df = predictor.prepare_features(
            sample_data['facility'].id,
            sample_data['commodity'].id
        )
        
        assert features is not None
        assert df is not None
        assert 'current_stock' in features
        assert 'avg_daily_consumption' in features
        assert 'avg_lead_time' in features

def test_prepare_features_insufficient_data(app):
    """Test feature preparation with insufficient data."""
    with app.app_context():
        predictor = StockOutPredictor()
        features, df = predictor.prepare_features(999, 999)
        
        assert features is None
        assert df is None

def test_calculate_trend():
    """Test trend calculation."""
    predictor = StockOutPredictor()
    
    # Test with increasing trend
    series = pd.Series([1, 2, 3, 4, 5])
    trend = predictor._calculate_trend(series)
    assert trend > 0
    
    # Test with decreasing trend
    series = pd.Series([5, 4, 3, 2, 1])
    trend = predictor._calculate_trend(series)
    assert trend < 0
    
    # Test with insufficient data
    series = pd.Series([1])
    trend = predictor._calculate_trend(series)
    assert trend == 0

def test_predict_stock_out(app, sample_data):
    """Test stock-out prediction."""
    with app.app_context():
        predictor = StockOutPredictor()
        result = predictor.predict_stock_out(
            sample_data['facility'].id,
            sample_data['commodity'].id
        )
        
        assert 'predicted_date' in result
        assert 'confidence' in result
        assert 'risk_level' in result
        assert 'model' in result
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0 <= result['confidence'] <= 1

def test_predict_stock_out_insufficient_data(app):
    """Test stock-out prediction with insufficient data."""
    with app.app_context():
        predictor = StockOutPredictor()
        result = predictor.predict_stock_out(999, 999)
        
        assert 'error' in result
        assert result['predicted_date'] is None
        assert result['confidence'] == 0
        assert result['risk_level'] == 'UNKNOWN'

def test_batch_predict(app, sample_data):
    """Test batch prediction."""
    with app.app_context():
        predictor = StockOutPredictor()
        pairs = [
            (sample_data['facility'].id, sample_data['commodity'].id)
        ]
        
        results = predictor.batch_predict(pairs)
        
        assert len(results) == 1
        assert 'facility_id' in results[0]
        assert 'commodity_id' in results[0]
        assert 'predicted_date' in results[0]

def test_get_feature_importance():
    """Test feature importance retrieval."""
    predictor = StockOutPredictor()
    
    # Test with no model trained
    importance = predictor.get_feature_importance()
    assert importance == {}
    
    # Test with non-existent model
    importance = predictor.get_feature_importance('non_existent')
    assert importance == {}

def test_evaluate_model():
    """Test model evaluation."""
    predictor = StockOutPredictor()
    
    # Test with no model
    result = predictor.evaluate_model('xgboost', None, None)
    assert result is None

def test_create_features():
    """Test feature creation."""
    predictor = StockOutPredictor()
    
    # Create sample DataFrame
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'quantity': [50] * 30,
        'movement_type': ['ISSUE'] * 30,
        'unit_cost': [0.5] * 30
    })
    
    # Mock balance and other data
    class MockBalance:
        current_stock = 1000
        reorder_level = 200
        maximum_stock = 5000
    
    class MockServiceVolume:
        volume_count = 100
    
    class MockLeadTime:
        average_lead_time_days = 30
    
    features = predictor._create_features(
        df, MockBalance(), [MockServiceVolume()], MockLeadTime()
    )
    
    assert 'current_stock' in features
    assert 'avg_daily_consumption' in features
    assert 'consumption_std' in features
    assert 'receipt_frequency' in features
    assert 'stock_ratio' in features
    assert 'avg_service_volume' in features
    assert 'avg_lead_time' in features
    assert 'day_of_week' in features
    assert 'month' in features
    assert 'days_until_stockout' in features

def test_create_features_empty_dataframe():
    """Test feature creation with empty DataFrame."""
    predictor = StockOutPredictor()
    
    # Create empty DataFrame
    df = pd.DataFrame()
    
    # Mock balance and other data
    class MockBalance:
        current_stock = 1000
        reorder_level = 200
        maximum_stock = 5000
    
    features = predictor._create_features(df, MockBalance(), [], None)
    
    # Should still create basic features
    assert 'current_stock' in features
    assert 'reorder_level' in features
    assert 'max_stock' in features
    assert 'stock_ratio' in features
