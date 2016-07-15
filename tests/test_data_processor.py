import pytest
import pandas as pd
from datetime import datetime, date
from io import StringIO
from models.database import db, Facility, Commodity, StockBalance, StockMovement, ServiceVolume, LeadTime, Alert
from utils.data_processor import DataProcessor

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
        
        return {
            'facility': facility,
            'commodity': commodity
        }

def test_data_processor_initialization():
    """Test DataProcessor initialization."""
    processor = DataProcessor()
    assert 'facilities' in processor.required_columns
    assert 'commodities' in processor.required_columns
    assert 'stock_movements' in processor.required_columns

def test_identify_file_type():
    """Test file type identification."""
    processor = DataProcessor()
    
    # Test facilities file
    facilities_cols = ['facility_code', 'facility_name', 'district', 'region', 'facility_type']
    assert processor._identify_file_type(facilities_cols) == 'facilities'
    
    # Test commodities file
    commodities_cols = ['commodity_code', 'commodity_name', 'commodity_type', 'unit_of_measure']
    assert processor._identify_file_type(commodities_cols) == 'commodities'
    
    # Test unknown file type
    unknown_cols = ['unknown_col1', 'unknown_col2']
    assert processor._identify_file_type(unknown_cols) is None

def test_validate_columns():
    """Test column validation."""
    processor = DataProcessor()
    
    # Test valid columns
    df = pd.DataFrame(columns=['facility_code', 'facility_name', 'district', 'region', 'facility_type'])
    missing = processor._validate_columns(df, 'facilities')
    assert missing == []
    
    # Test missing columns
    df = pd.DataFrame(columns=['facility_code', 'facility_name'])
    missing = processor._validate_columns(df, 'facilities')
    assert 'district' in missing
    assert 'region' in missing
    assert 'facility_type' in missing

def test_process_facilities(app, sample_data):
    """Test facilities data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """facility_code,facility_name,district,region,facility_type
HC002,New Health Center,New District,New Region,Hospital"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        # Mock file object
        class MockFile:
            def __init__(self, data):
                self.data = data
            
            def read(self, size=-1):
                return self.data.encode()
        
        mock_file = MockFile(csv_data)
        mock_file.filename = 'facilities.csv'
        
        result = processor._process_facilities(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if facility was created
        facility = Facility.query.filter_by(facility_code='HC002').first()
        assert facility is not None
        assert facility.facility_name == 'New Health Center'

def test_process_commodities(app, sample_data):
    """Test commodities data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """commodity_code,commodity_name,commodity_type,unit_of_measure
VAC001,New Vaccine,Vaccine,Vials"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_commodities(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if commodity was created
        commodity = Commodity.query.filter_by(commodity_code='VAC001').first()
        assert commodity is not None
        assert commodity.commodity_name == 'New Vaccine'

def test_process_stock_movements(app, sample_data):
    """Test stock movements data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """facility_code,commodity_code,movement_type,quantity,movement_date,unit_cost,reference_number
TEST001,TEST_ARV,ISSUE,100,2024-01-15,0.5,IS-001"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_stock_movements(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if movement was created
        movement = StockMovement.query.first()
        assert movement is not None
        assert movement.quantity == 100
        assert movement.movement_type == 'ISSUE'

def test_process_stock_balances(app, sample_data):
    """Test stock balances data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """facility_code,commodity_code,current_stock,reorder_level,maximum_stock
TEST001,TEST_ARV,1500,300,6000"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_stock_balances(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if balance was created/updated
        balance = StockBalance.query.first()
        assert balance is not None
        assert balance.current_stock == 1500
        assert balance.reorder_level == 300

def test_process_service_volumes(app, sample_data):
    """Test service volumes data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """facility_code,service_type,volume_count,reporting_period
TEST001,HIV,150,2024-01-01"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_service_volumes(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if service volume was created
        volume = ServiceVolume.query.first()
        assert volume is not None
        assert volume.volume_count == 150
        assert volume.service_type == 'HIV'

def test_process_lead_times(app, sample_data):
    """Test lead times data processing."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data
        csv_data = """facility_code,commodity_code,supplier,average_lead_time_days
TEST001,TEST_ARV,Test Supplier,25"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_lead_times(df)
        
        assert result['success'] is True
        assert result['processed'] == 1
        assert len(result['errors']) == 0
        
        # Check if lead time was created
        lead_time = LeadTime.query.first()
        assert lead_time is not None
        assert lead_time.average_lead_time_days == 25
        assert lead_time.supplier == 'Test Supplier'

def test_process_stock_movements_invalid_facility(app, sample_data):
    """Test stock movements processing with invalid facility."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data with invalid facility
        csv_data = """facility_code,commodity_code,movement_type,quantity,movement_date
INVALID,TEST_ARV,ISSUE,100,2024-01-15"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_stock_movements(df)
        
        assert result['success'] is True
        assert result['processed'] == 0
        assert len(result['errors']) == 1
        assert 'Facility INVALID not found' in result['errors'][0]

def test_process_stock_movements_invalid_commodity(app, sample_data):
    """Test stock movements processing with invalid commodity."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create CSV data with invalid commodity
        csv_data = """facility_code,commodity_code,movement_type,quantity,movement_date
TEST001,INVALID,ISSUE,100,2024-01-15"""
        
        df = pd.read_csv(StringIO(csv_data))
        
        result = processor._process_stock_movements(df)
        
        assert result['success'] is True
        assert result['processed'] == 0
        assert len(result['errors']) == 1
        assert 'Commodity INVALID not found' in result['errors'][0]

def test_generate_alerts(app, sample_data):
    """Test alert generation."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create low stock balance
        balance = StockBalance(
            facility_id=sample_data['facility'].id,
            commodity_id=sample_data['commodity'].id,
            current_stock=100,  # Below reorder level
            reorder_level=200,
            maximum_stock=5000
        )
        db.session.add(balance)
        db.session.commit()
        
        result = processor.generate_alerts()
        
        assert result['success'] is True
        assert result['alerts_created'] == 1
        
        # Check if alert was created
        alert = Alert.query.first()
        assert alert is not None
        assert alert.alert_type == 'LOW_STOCK'
        assert alert.alert_level == 'WARNING'

def test_generate_alerts_no_low_stock(app, sample_data):
    """Test alert generation with no low stock."""
    with app.app_context():
        processor = DataProcessor()
        
        # Create normal stock balance
        balance = StockBalance(
            facility_id=sample_data['facility'].id,
            commodity_id=sample_data['commodity'].id,
            current_stock=1000,  # Above reorder level
            reorder_level=200,
            maximum_stock=5000
        )
        db.session.add(balance)
        db.session.commit()
        
        result = processor.generate_alerts()
        
        assert result['success'] is True
        assert result['alerts_created'] == 0

def test_process_uploaded_file_unknown_type():
    """Test processing uploaded file with unknown type."""
    processor = DataProcessor()
    
    # Create CSV data with unknown columns
    csv_data = """unknown_col1,unknown_col2
value1,value2"""
    
    df = pd.read_csv(StringIO(csv_data))
    
    # Mock file object
    class MockFile:
        def __init__(self, data):
            self.data = data
        
        def read(self, size=-1):
            return self.data.encode()
    
    mock_file = MockFile(csv_data)
    mock_file.filename = 'unknown.csv'
    
    result = processor.process_uploaded_file(mock_file)
    
    assert 'error' in result
    assert 'Unknown file format' in result['error']

def test_process_uploaded_file_missing_columns():
    """Test processing uploaded file with missing columns."""
    processor = DataProcessor()
    
    # Create CSV data with missing required columns
    csv_data = """facility_code,facility_name
HC001,Test Center"""
    
    df = pd.read_csv(StringIO(csv_data))
    
    # Mock file object
    class MockFile:
        def __init__(self, data):
            self.data = data
        
        def read(self, size=-1):
            return self.data.encode()
    
    mock_file = MockFile(csv_data)
    mock_file.filename = 'facilities.csv'
    
    result = processor.process_uploaded_file(mock_file)
    
    assert 'error' in result
    assert 'Missing required columns' in result['error']
