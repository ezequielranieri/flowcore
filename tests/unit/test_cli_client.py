# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
import httpx
from unittest.mock import patch, MagicMock
from flowcore.cli.client import FlowcoreClient

@pytest.fixture
def client():
    return FlowcoreClient(base_url="http://testserver", tenant_id="test-tenant")

def test_run_workflow_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"execution_id": 123, "status": "PENDING"}
    
    with patch("httpx.post", return_value=mock_response):
        result = client.run_workflow("test-wf", {"key": "value"})
        
    assert result["execution_id"] == 123
    assert result["status"] == "PENDING"

def test_run_workflow_connection_error(client):
    with patch("httpx.post", side_effect=httpx.ConnectError("Connection failed")):
        result = client.run_workflow("test-wf", {})
        
    assert "error" in result
    assert "Could not connect" in result["error"]

def test_get_status_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "status": "COMPLETED"}
    
    with patch("httpx.get", return_value=mock_response):
        result = client.get_status(1)
        
    assert result["id"] == 1
    assert result["status"] == "COMPLETED"

def test_get_status_not_found(client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    
    # httpx.HTTPStatusError needs response and request
    mock_request = MagicMock()
    error = httpx.HTTPStatusError("404 Not Found", request=mock_request, response=mock_response)
    
    with patch("httpx.get", side_effect=error):
        result = client.get_status(999)
        
    assert "error" in result
    assert "Execution 999 not found" in result["error"]

def test_list_executions_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1}, {"id": 2}]
    
    with patch("httpx.get", return_value=mock_response):
        result = client.list_executions(limit=2)
        
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
