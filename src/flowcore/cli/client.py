# Author: Ezequiel Ranieri <ez.ranieri@gmail.com>

import httpx
from typing import List, Dict, Any, Optional

class FlowcoreClient:
    def __init__(self, base_url: str = "http://localhost:8000", tenant_id: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.headers = {"X-Tenant-ID": tenant_id}

    def run_workflow(self, name: str, context: Dict[str, Any], version: Optional[str] = None) -> Dict[str, Any]:
        try:
            params = {}
            if version:
                params["version"] = version
            response = httpx.post(
                f"{self.base_url}/workflows/{name}", 
                json=context, 
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": f"Could not connect to Flowcore API at {self.base_url}. Is the server running?"}
        except httpx.HTTPStatusError as e:
            return {"error": f"API Error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def get_status(self, execution_id: int) -> Dict[str, Any]:
        try:
            response = httpx.get(
                f"{self.base_url}/workflows/executions/{execution_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": f"Could not connect to Flowcore API at {self.base_url}"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"error": f"Execution {execution_id} not found or access denied."}
            return {"error": f"API Error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def list_executions(self, limit: int = 20) -> Any:
        try:
            response = httpx.get(
                f"{self.base_url}/workflows/executions/", 
                params={"limit": limit}, 
                headers=self.headers,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": f"Could not connect to Flowcore API at {self.base_url}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

    def list_workflows(self) -> Any:
        try:
            response = httpx.get(
                f"{self.base_url}/workflows/", 
                headers=self.headers,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return {"error": f"Could not connect to Flowcore API at {self.base_url}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
