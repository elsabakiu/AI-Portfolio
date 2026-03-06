from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .event_store import (
    create_alert,
    delete_alert,
    get_active_alerts,
    get_alerts,
    load_latest_bundle,
    load_recent_runs,
    load_run,
    load_user_profile_json,
    mark_alert_triggered,
    persist_run,
    save_bundle,
    save_user_profile,
    update_alert,
)
from .models import AnalysisSnapshot, UserReportBundle


@dataclass
class RunRepository:
    def save_snapshot(self, snapshot: AnalysisSnapshot) -> None:
        persist_run(snapshot)

    def get_run(self, run_id: str) -> Optional[AnalysisSnapshot]:
        return load_run(run_id)

    def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        return load_recent_runs(limit=limit)


@dataclass
class ProfileRepository:
    def save_profile_json(self, user_id: str, profile_json: Dict[str, Any]) -> None:
        save_user_profile(user_id, profile_json)

    def load_profile_json(self, user_id: str) -> Optional[Dict[str, Any]]:
        return load_user_profile_json(user_id)


@dataclass
class BundleRepository:
    def save_user_bundle(self, bundle: UserReportBundle) -> None:
        save_bundle(bundle)

    def load_latest_user_bundle(self, user_id: str) -> Optional[Dict[str, Any]]:
        return load_latest_bundle(user_id)


@dataclass
class AlertRepository:
    def list_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        return get_alerts(user_id)

    def create_user_alert(self, user_id: str, ticker: str, condition: str, value: float) -> Dict[str, Any]:
        return create_alert(user_id, ticker, condition, value)

    def update_user_alert(
        self,
        alert_id: str,
        *,
        status: Optional[str] = None,
        ticker: Optional[str] = None,
        condition: Optional[str] = None,
        value: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        return update_alert(
            alert_id,
            status=status,
            ticker=ticker,
            condition=condition,
            value=value,
        )

    def delete_user_alert(self, alert_id: str) -> bool:
        return delete_alert(alert_id)

    def list_active_alerts(self) -> List[Dict[str, Any]]:
        return get_active_alerts()

    def mark_triggered(self, alert_id: str) -> None:
        mark_alert_triggered(alert_id)
