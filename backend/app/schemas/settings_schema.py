from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: str
    timezone: str
    date_format: str
    theme: str
    notif_budget_alerts: bool
    notif_anomaly_alerts: bool
    notif_monthly_reports: bool
    notif_financial_insights: bool
    notif_product_updates: bool
    privacy_show_balances: bool
    privacy_show_amounts: bool
    privacy_mask_values: bool
    privacy_mode: bool


class SettingsUpdate(BaseModel):
    currency: Optional[str] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    theme: Optional[str] = None
    notif_budget_alerts: Optional[bool] = None
    notif_anomaly_alerts: Optional[bool] = None
    notif_monthly_reports: Optional[bool] = None
    notif_financial_insights: Optional[bool] = None
    notif_product_updates: Optional[bool] = None
    privacy_show_balances: Optional[bool] = None
    privacy_show_amounts: Optional[bool] = None
    privacy_mask_values: Optional[bool] = None
    privacy_mode: Optional[bool] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    is_active: bool
    created_at: str
    last_used: str
    is_current: bool = False


class ExportRequest(BaseModel):
    format: str = "csv"  # csv | json


class DeleteAccountRequest(BaseModel):
    password: str
