import pytest
from core.config import Settings, AppEnvironment


def test_settings_default_values():
    s = Settings(
        data_dir="data",
        manifest_path="data/manifest.json",
        knowledge_dir="data/lck_airport"
    )
    assert s.app_name == "LCK Airport's AI Assistant"
    assert s.api_v1_prefix == "/api/v1"
    assert s.guardrail_enabled is True
    assert s.auth_enabled is True

