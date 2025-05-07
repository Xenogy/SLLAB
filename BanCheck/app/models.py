from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CheckRequestBase(BaseModel):
    """
    Base model for check requests.

    Note: This model is kept for backward compatibility but is no longer used directly.
    The API endpoints now use Form parameters instead.
    """
    steam_ids: Optional[List[str]] = Field(None, description="List of SteamIDs to check.")
    proxy_list_str: Optional[str] = Field(None, description="Multiline string of proxies, one per line (e.g., http://user:pass@host:port).")

    # Concurrency and Retry Parameters (with defaults from ScriptConfig)
    logical_batch_size: int = Field(20, ge=1, description="URLs per processing unit/task.")
    max_concurrent_batches: int = Field(3, ge=1, description="How many batch tasks run in parallel.")
    max_workers_per_batch: int = Field(3, ge=1, description="Threads for URLs within one batch (using the same proxy).")
    inter_request_submit_delay: float = Field(0.1, ge=0, description="Delay (s) submitting requests to inner pool within a batch.")
    max_retries_per_url: int = Field(2, ge=0, description="Retries per URL on failure.")
    retry_delay_seconds: float = Field(5.0, ge=0, description="Delay (s) between retries for a URL.")

class CheckSteamIDsRequest(CheckRequestBase):
    """
    Request model for checking Steam IDs.

    Note: This model is kept for backward compatibility but is no longer used directly.
    The API endpoints now use Form parameters instead.
    """
    steam_ids: List[str] = Field(..., min_items=1, description="List of SteamIDs to check.")

class TaskStatus(BaseModel):
    task_id: str
    status: str # e.g., "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    message: Optional[str] = None
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    results: Optional[List[Dict[str, Any]]] = None # Store the final results here
    proxy_stats: Optional[Dict[str, Any]] = None # Store proxy usage statistics

class ResultItem(BaseModel):
    steam_id: str
    status_summary: str
    details: str
    proxy_used: str
    batch_id: Any # Could be int or str