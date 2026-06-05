# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import pytest
from typer.testing import CliRunner
from flowcore.cli.main import app
from flowcore.cli.client import FlowcoreClient

runner = CliRunner()

def test_cli_run_command_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Start a new workflow execution" in result.stdout

def test_cli_status_command_help():
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "Get the status of a specific workflow execution" in result.stdout

def test_flowcore_client_handles_connection_error(monkeypatch):
    client = FlowcoreClient("http://nonexistent-host")
    result = client.list_workflows()
    assert "error" in result
    assert "Could not connect" in result["error"]

def test_get_status_color():
    from flowcore.cli.main import get_status_color
    assert get_status_color("COMPLETED") == "green"
    assert get_status_color("FAILED") == "red"
    assert get_status_color("UNKNOWN") == "white"
