import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import os

# Set environment variables for testing
os.environ['ADD_URL_ENDPOINT'] = 'http://test-addition:5000'
os.environ['DIVIDE_URL_ENDPOINT'] = 'http://test-division:5000'
os.environ['MULTI_URL_ENDPOINT'] = 'http://test-multiplication:5000'
os.environ['SUB_URL_ENDPOINT'] = 'http://test-subtraction:5000'

from app import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    with patch('requests.get') as mock_get:
        # Mock all service health checks
        mock_get.return_value.status_code = 200
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "useless-calculator"
        assert "dependencies" in data

def test_index_page():
    """Test the index page renders correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Useless Calculator" in response.content or b"calculator" in response.content.lower()

def test_addition_page_get():
    """Test the addition page GET request."""
    response = client.get("/add")
    assert response.status_code == 200

def test_addition_operation_success():
    """Test successful addition operation."""
    with patch('requests.get') as mock_get:
        # Mock the addition service response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": 8.0}
        mock_get.return_value = mock_response
        
        response = client.post("/add", data={"First_Number": "5", "Second_Number": "3"})
        assert response.status_code == 200
        assert b"8" in response.content

def test_addition_missing_numbers():
    """Test addition with missing numbers."""
    response = client.post("/add", data={})
    assert response.status_code == 200
    assert b"Please enter both numbers" in response.content or b"show" in response.content

def test_division_by_zero_handling():
    """Test division by zero error handling."""
    with patch('requests.get') as mock_get:
        # Mock the division service error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Cannot divide by zero"}
        mock_get.return_value = mock_response
        
        response = client.post("/divide", data={"First_Number": "10", "Second_Number": "0"})
        assert response.status_code == 200
        assert b"Cannot divide by zero" in response.content

def test_service_timeout_handling():
    """Test service timeout handling."""
    with patch('requests.get') as mock_get:
        # Mock a timeout exception
        mock_get.side_effect = requests.exceptions.Timeout()
        
        response = client.post("/multi", data={"First_Number": "5", "Second_Number": "3"})
        assert response.status_code == 200
        assert b"Service timeout" in response.content or b"try again" in response.content

def test_subtraction_page_get():
    """Test the subtraction page GET request."""
    response = client.get("/sub")
    assert response.status_code == 200

def test_multiplication_page_get():
    """Test the multiplication page GET request."""
    response = client.get("/multi")
    assert response.status_code == 200

def test_division_page_get():
    """Test the division page GET request."""
    response = client.get("/divide")
    assert response.status_code == 200

# Import requests for the timeout test
import requests