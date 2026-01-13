import pytest
import os
from unittest.mock import patch, MagicMock
from auth import get_genai_client, validate_credentials

def test_get_client_api_key():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}, clear=True):
        with patch("auth.genai.Client") as mock_client:
            client = get_genai_client()
            mock_client.assert_called_with(api_key="fake_key")

def test_validate_credentials_success():
    with patch("auth.get_genai_client") as mock_get:
        mock_get.return_value = MagicMock()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake"}, clear=True):
            result = validate_credentials()
            assert result["valid"] is True
            assert result["method"] == "api_key"

def test_validate_credentials_failure():
    with patch.dict(os.environ, {}, clear=True):
        result = validate_credentials()
        assert result["valid"] is False
