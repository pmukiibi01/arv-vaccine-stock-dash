import pytest
import json
from datetime import datetime, date
from app import create_app
from models.database import db, Facility, Commodity, StockBalance, StockMovement, Prediction

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

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
        
        # Create stock movement
        movement = StockMovement(
            facility_id=facility.id,
            commodity_id=commodity.id,
            movement_type='ISSUE',
            quantity=50,
            movement_date=date.today()
        )
        db.session.add(movement)
        
        db.session.commit()
        
        return {
            'facility': facility,
            'commodity': commodity,
            'balance': balance,
            'movement': movement
        }

def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'ARV and Vaccine Stock-Out Prediction System' in response.data

def test_dashboard_stats(client, sample_data):
    """Test dashboard stats API endpoint."""
    response = client.get('/api/dashboard/stats')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'total_facilities' in data
    assert 'total_commodities' in data
    assert 'active_alerts' in data
    assert 'recent_predictions' in data

def test_get_facilities(client, sample_data):
    """Test facilities API endpoint."""
    response = client.get('/api/facilities')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['facility_code'] == 'TEST001'
    assert data[0]['facility_name'] == 'Test Health Center'

def test_get_commodities(client, sample_data):
    """Test commodities API endpoint."""
    response = client.get('/api/commodities')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['commodity_code'] == 'TEST_ARV'
    assert data[0]['commodity_name'] == 'Test ARV'

def test_get_stock_balances(client, sample_data):
    """Test stock balances API endpoint."""
    response = client.get('/api/stock-balances')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['current_stock'] == 1000
    assert data[0]['reorder_level'] == 200

def test_get_predictions(client, sample_data):
    """Test predictions API endpoint."""
    response = client.get('/api/predictions')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_generate_prediction(client, sample_data):
    """Test prediction generation."""
    response = client.post('/api/predictions', 
                          json={
                              'facility_id': sample_data['facility'].id,
                              'commodity_id': sample_data['commodity'].id
                          })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'predicted_date' in data
    assert 'risk_level' in data
    assert 'confidence' in data

def test_get_alerts(client, sample_data):
    """Test alerts API endpoint."""
    response = client.get('/api/alerts')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_upload_data_missing_file(client):
    """Test upload endpoint with missing file."""
    response = client.post('/api/upload')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data

def test_export_predictions(client, sample_data):
    """Test predictions export."""
    response = client.get('/api/export/predictions')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_export_alerts(client, sample_data):
    """Test alerts export."""
    response = client.get('/api/export/alerts')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_export_stock_balances(client, sample_data):
    """Test stock balances export."""
    response = client.get('/api/export/stock_balances')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_facilities(client):
    """Test sample facilities download."""
    response = client.get('/api/sample-data/facilities')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_commodities(client):
    """Test sample commodities download."""
    response = client.get('/api/sample-data/commodities')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_stock_movements(client):
    """Test sample stock movements download."""
    response = client.get('/api/sample-data/stock_movements')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_stock_balances(client):
    """Test sample stock balances download."""
    response = client.get('/api/sample-data/stock_balances')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_service_volumes(client):
    """Test sample service volumes download."""
    response = client.get('/api/sample-data/service_volumes')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_download_sample_lead_times(client):
    """Test sample lead times download."""
    response = client.get('/api/sample-data/lead_times')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'

def test_invalid_export_type(client):
    """Test invalid export type."""
    response = client.get('/api/export/invalid_type')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data

def test_invalid_sample_data_type(client):
    """Test invalid sample data type."""
    response = client.get('/api/sample-data/invalid_type')
    assert response.status_code == 500
    
    data = json.loads(response.data)
    assert 'error' in data

