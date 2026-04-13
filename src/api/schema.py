
from __future__ import annotations
from pydantic import BaseModel
from typing import List


class DashboardItem(BaseModel):
    Selected_Dashboard: str
    Reason: str

class DashboardResponse(BaseModel):
    dashboards: List[DashboardItem]


class ComparisonResult(BaseModel):
    missing_in_prod: List[str]
    missing_in_dev: List[str]
    counts: dict

class WorkspaceComparison(BaseModel):
    status: ComparisonResult

class HealthResponse(BaseModel):
    status: str

class DeleteResponse(BaseModel):
    status: str
    message: str
    resource_id: str
    Dashboard_name: str

class ExportResponse(BaseModel):
    dataset_id: str
    report_id: str
    status: str

