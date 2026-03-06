from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .repositories import AlertRepository, BundleRepository
from .run_weekly import run_analysis, run_weekly


@dataclass
class AnalysisService:
    def run_weekly_analysis(
        self,
        *,
        run_date: Optional[str],
        skip_synthesis: bool,
        skip_post: bool,
    ) -> Dict[str, Any]:
        return run_weekly(run_date=run_date, skip_synthesis=skip_synthesis, skip_post=skip_post)

    def run_targeted_analysis(
        self,
        *,
        tickers: Optional[List[str]],
        skip_synthesis: bool,
        skip_post: bool,
    ) -> Dict[str, Any]:
        return run_analysis(tickers=tickers, skip_synthesis=skip_synthesis, skip_post=skip_post)


@dataclass
class PersonalizationService:
    bundle_repository: BundleRepository

    def get_user_dashboard(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.bundle_repository.load_latest_user_bundle(user_id)

    def get_user_personalized_signals(self, user_id: str) -> Optional[Dict[str, Any]]:
        bundle = self.bundle_repository.load_latest_user_bundle(user_id)
        if bundle is None:
            return None
        return {
            "watchlist_signals": bundle.get("watchlist_signals", []),
            "discovery_signals": bundle.get("discovery_signals", []),
        }


@dataclass
class NotificationService:
    alert_repository: AlertRepository

    def list_user_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        return self.alert_repository.list_user_alerts(user_id)
