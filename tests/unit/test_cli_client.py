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

def test_run_workflow_with_version(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    
    with patch("httpx.post", return_value=mock_response) as mock_post:
        result = client.run_workflow("test-wf", {}, version="2.0.0")
        
    assert result == {"status": "ok"}
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["params"] == {"version": "2.0.0"}

def test_run_workflow_http_status_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Error"
    mock_request = MagicMock()
    error = httpx.HTTPStatusError("500 Internal Error", request=mock_request, response=mock_response)
    
    with patch("httpx.post", side_effect=error):
        result = client.run_workflow("test-wf", {})
        
    assert "error" in result
    assert "API Error: 500" in result["error"]
    assert "Internal Error" in result["error"]

def test_run_workflow_unexpected_error(client):
    with patch("httpx.post", side_effect=Exception("boom")):
        result = client.run_workflow("test-wf", {})
        
    assert result["error"] == "Unexpected error: boom"

def test_get_status_connection_error(client):
    with patch("httpx.get", side_effect=httpx.ConnectError("fail")):
        result = client.get_status(1)
        
    assert "Could not connect" in result["error"]

def test_get_status_http_status_error_non_404(client):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_request = MagicMock()
    error = httpx.HTTPStatusError("500", request=mock_request, response=mock_response)
    
    with patch("httpx.get", side_effect=error):
        result = client.get_status(1)
        
    assert result["error"] == "API Error: 500"

def test_get_status_unexpected_error(client):
    with patch("httpx.get", side_effect=Exception("boom")):
        result = client.get_status(1)
        
    assert result["error"] == "Unexpected error: boom"

def test_list_executions_connection_error(client):
    with patch("httpx.get", side_effect=httpx.ConnectError("fail")):
        result = client.list_executions()
        
    assert "Could not connect" in result["error"]

def test_list_executions_unexpected_error(client):
    with patch("httpx.get", side_effect=Exception("boom")):
        result = client.list_executions()
        
    assert result["error"] == "Unexpected error: boom"

def test_list_workflows_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"name": "wf1"}]
    
    with patch("httpx.get", return_value=mock_response):
        result = client.list_workflows()
        
    assert result == [{"name": "wf1"}]

def test_list_workflows_connection_error(client):
    with patch("httpx.get", side_effect=httpx.ConnectError("fail")):
        result = client.list_workflows()
        
    assert "Could not connect" in result["error"]

def test_list_workflows_unexpected_error(client):
    with patch("httpx.get", side_effect=Exception("boom")):
        result = client.list_workflows()
        
    assert result["error"] == "Unexpected error: boom"
