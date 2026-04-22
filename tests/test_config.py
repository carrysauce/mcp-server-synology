"""Configuration module tests."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch


def reload_config_module():
    """Reload the config module to get fresh state."""
    for module_name in list(sys.modules):
        if module_name == "config":
            del sys.modules[module_name]


def load_config(env=None, settings_data=None, tmp_path=None, permissions=0o600):
    """Load a fresh SynologyConfig with optional env vars and settings.json."""
    reload_config_module()
    env = env or {}

    with patch.dict(os.environ, env, clear=True):
        import config as config_module

        settings_file = Path("/nonexistent/settings.json")
        if settings_data is not None:
            if tmp_path is None:
                raise ValueError("tmp_path is required when settings_data is provided")
            settings_file = tmp_path / "settings.json"
            settings_file.write_text(json.dumps(settings_data))
            os.chmod(settings_file, permissions)

        with patch.object(config_module, "SETTINGS_FILE", settings_file):
            return config_module.SynologyConfig()


class TestSynologyConfig:
    """Test Synology configuration loading and validation."""

    def test_env_fallback(self):
        """Test that .env values are used as fallback."""
        cfg = load_config(
            {
                "SYNOLOGY_URL": "http://test.local:5000",
                "SYNOLOGY_USERNAME": "testuser",
                "SYNOLOGY_PASSWORD": "testpass",
            }
        )

        assert cfg.synology_url == "http://test.local:5000"
        assert cfg.synology_username == "testuser"
        assert cfg.synology_password == "testpass"

    def test_default_values(self):
        """Test default configuration values."""
        cfg = load_config()

        assert cfg.server_name == "synology-mcp-server"
        assert cfg.server_version == "1.0.0"
        assert cfg.default_session_timeout == 3600
        assert cfg.auto_login is True
        assert cfg.verify_ssl is False
        assert cfg.transport == "stdio"
        assert cfg.http_host == "0.0.0.0"
        assert cfg.http_port == 8765
        assert cfg.http_path == "/mcp"
        assert cfg.http_query_token is None

    def test_http_env_values(self):
        """Test HTTP transport env vars are loaded and normalized."""
        cfg = load_config(
            {
                "TRANSPORT": "HTTP",
                "HTTP_HOST": "127.0.0.1",
                "HTTP_PORT": "9999",
                "HTTP_PATH": "synology/",
                "HTTP_QUERY_TOKEN": "secret-token",
            }
        )

        assert cfg.transport == "http"
        assert cfg.http_host == "127.0.0.1"
        assert cfg.http_port == 9999
        assert cfg.http_path == "/synology"
        assert cfg.http_query_token == "secret-token"

    def test_has_credentials_with_settings(self, tmp_path):
        """Test credential detection with settings.json."""
        cfg = load_config(
            settings_data={
                "synology": {
                    "test_nas": {
                        "host": "192.168.1.100",
                        "port": 5000,
                        "username": "admin",
                        "password": "pass123",
                    }
                }
            },
            tmp_path=tmp_path,
        )

        assert cfg.has_synology_credentials() is True
        assert "test_nas" in cfg.nas_configs
        assert cfg.nas_configs["test_nas"]["base_url"] == "http://192.168.1.100:5000"

    def test_get_nas_names(self, tmp_path):
        """Test getting NAS names from settings.json."""
        cfg = load_config(
            settings_data={
                "synology": {
                    "nas1": {"host": "192.168.1.1", "port": 5000, "username": "a", "password": "b"},
                    "nas2": {"host": "192.168.1.2", "port": 5001, "username": "c", "password": "d"},
                }
            },
            tmp_path=tmp_path,
        )

        names = cfg.get_nas_names()
        assert len(names) == 2
        assert "nas1" in names
        assert "nas2" in names

    def test_get_synology_config_with_nas_name(self, tmp_path):
        """Test getting config for specific NAS."""
        cfg = load_config(
            settings_data={
                "synology": {
                    "primary": {
                        "host": "192.168.1.100",
                        "port": 5001,
                        "username": "admin",
                        "password": "secret",
                    }
                }
            },
            tmp_path=tmp_path,
        )

        specific = cfg.get_synology_config("primary")
        assert specific["base_url"] == "https://192.168.1.100:5001"
        assert specific["username"] == "admin"

    def test_validate_config_no_credentials(self):
        """Test validation fails with no credentials."""
        cfg = load_config()
        errors = cfg.validate_config()

        assert len(errors) > 0
        assert "No Synology credentials" in errors[0]

    def test_validate_config_timeout_too_low(self):
        """Test validation fails with low timeout."""
        cfg = load_config(
            {
                "SYNOLOGY_URL": "http://test.local:5000",
                "SYNOLOGY_USERNAME": "user",
                "SYNOLOGY_PASSWORD": "pass",
                "SESSION_TIMEOUT": "30",
            }
        )

        errors = cfg.validate_config()
        assert any("SESSION_TIMEOUT" in error_msg for error_msg in errors)

    def test_validate_config_invalid_transport(self):
        """Test validation fails with an invalid transport value."""
        cfg = load_config(
            {
                "SYNOLOGY_URL": "http://test.local:5000",
                "SYNOLOGY_USERNAME": "user",
                "SYNOLOGY_PASSWORD": "pass",
                "TRANSPORT": "websocket",
            }
        )

        errors = cfg.validate_config()
        assert any("TRANSPORT" in error_msg for error_msg in errors)

    def test_validate_config_invalid_http_port(self):
        """Test validation fails with an out-of-range HTTP port."""
        cfg = load_config(
            {
                "SYNOLOGY_URL": "http://test.local:5000",
                "SYNOLOGY_USERNAME": "user",
                "SYNOLOGY_PASSWORD": "pass",
                "HTTP_PORT": "70000",
            }
        )

        errors = cfg.validate_config()
        assert any("HTTP_PORT" in error_msg for error_msg in errors)

    def test_missing_required_fields_in_settings(self, tmp_path):
        """Test handling of missing required fields in settings."""
        cfg = load_config(
            settings_data={"synology": {"incomplete_nas": {"host": "192.168.1.100"}}},
            tmp_path=tmp_path,
        )

        assert "incomplete_nas" not in cfg.nas_configs

    def test_invalid_json_in_settings(self, tmp_path):
        """Test handling of invalid JSON in settings file."""
        reload_config_module()

        with patch.dict(os.environ, {}, clear=True):
            import config as config_module

            settings_file = tmp_path / "settings.json"
            settings_file.write_text("{ invalid json }")
            os.chmod(settings_file, 0o600)

            with patch.object(config_module, "SETTINGS_FILE", settings_file):
                cfg = config_module.SynologyConfig()

        assert cfg.nas_configs == {}

    def test_resolve_base_url(self, tmp_path):
        """Test resolving base URL from NAS name."""
        cfg = load_config(
            settings_data={
                "synology": {
                    "office_nas": {
                        "host": "office.example.com",
                        "port": 5000,
                        "username": "admin",
                        "password": "pass",
                    }
                }
            },
            tmp_path=tmp_path,
        )

        assert cfg.resolve_base_url("office_nas") == "http://office.example.com:5000"
        assert cfg.resolve_base_url("nonexistent") is None


class TestFilePermissions:
    """Test file permission checking."""

    def test_permission_warning_for_open_permissions(self, tmp_path, caplog):
        """Test that warning is logged for overly open permissions."""
        cfg = load_config(
            settings_data={"synology": {}},
            tmp_path=tmp_path,
            permissions=0o644,
        )

        assert cfg.nas_configs == {}
        assert any(record.levelname == "WARNING" for record in caplog.records)
        assert "overly permissive permissions" in caplog.text


def test_config_str_representation():
    """Test string representation of config."""
    cfg = load_config(
        {
            "SYNOLOGY_URL": "http://test.local:5000",
            "SYNOLOGY_USERNAME": "user",
            "SYNOLOGY_PASSWORD": "pass",
        }
    )

    cfg_str = str(cfg)
    assert "SynologyConfig" in cfg_str
    assert "auto_login" in cfg_str
    assert "transport" in cfg_str
