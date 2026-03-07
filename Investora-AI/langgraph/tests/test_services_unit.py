from __future__ import annotations

from app.services import NotificationService, PersonalizationService


class _BundleRepoStub:
    def __init__(self, bundle=None):
        self._bundle = bundle

    def load_latest_user_bundle(self, user_id: str):
        return self._bundle


class _AlertRepoStub:
    def list_user_alerts(self, user_id: str):
        return [{"id": "a1", "user_id": user_id}]


def test_personalization_service_returns_dashboard_and_signals():
    bundle = {
        "user_id": "u1",
        "watchlist_signals": [{"ticker": "AAPL"}],
        "discovery_signals": [{"ticker": "NVDA"}],
    }
    svc = PersonalizationService(bundle_repository=_BundleRepoStub(bundle))

    assert svc.get_user_dashboard("u1") == bundle
    assert svc.get_user_personalized_signals("u1") == {
        "watchlist_signals": [{"ticker": "AAPL"}],
        "discovery_signals": [{"ticker": "NVDA"}],
    }


def test_notification_service_lists_alerts():
    svc = NotificationService(alert_repository=_AlertRepoStub())
    out = svc.list_user_alerts("u1")
    assert out == [{"id": "a1", "user_id": "u1"}]
