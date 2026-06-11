# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from flowcore.cli.main import app

runner = CliRunner()

def test_cli_run_success():
    with patch("flowcore.cli.main.FlowcoreClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.run_workflow.return_value = {"execution_id": 1, "status": "PENDING"}
        
        result = runner.invoke(app, ["run", "test-wf", "--context", '{"a": 1}'])
        
    assert result.exit_code == 0
    assert "Workflow Started: test-wf" in result.stdout
    assert "Execution ID" in result.stdout

def test_cli_run_invalid_json():
    result = runner.invoke(app, ["run", "test-wf", "--context", "invalid"])
    assert result.exit_code == 1
    assert "Error: Context must be a valid JSON string" in result.stdout

def test_cli_status_success():
    with patch("flowcore.cli.main.FlowcoreClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_status.return_value = {
            "workflow_name": "test-wf",
            "status": "COMPLETED",
            "started_at": "now",
            "completed_at": "then"
        }
        
        result = runner.invoke(app, ["status", "1"])
        
    assert result.exit_code == 0
    assert "Execution Status: 1" in result.stdout
    assert "COMPLETED" in result.stdout

def test_cli_list_success():
    with patch("flowcore.cli.main.FlowcoreClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.list_executions.return_value = [
            {"id": 1, "workflow_name": "wf1", "status": "COMPLETED", "started_at": "now"}
        ]
        
        result = runner.invoke(app, ["list"])
        
    assert result.exit_code == 0
    assert "Recent Executions" in result.stdout
    assert "COMPLETED" in result.stdout

def test_cli_workflows_success():
    with patch("flowcore.cli.main.FlowcoreClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.list_workflows.return_value = [
            {"name": "wf1", "version": "1.0.0", "description": "desc"}
        ]
        
        result = runner.invoke(app, ["workflows"])
        
    assert result.exit_code == 0
    assert "Registered Workflows" in result.stdout
    assert "wf1" in result.stdout
