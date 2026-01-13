import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tts_service import generate_speech, generate_batch
from models import GenerateRequest, GenerateResponse, GeminiModel

@pytest.mark.asyncio
async def test_generate_speech_success(tmp_path):
    with patch("tts_service.get_genai_client") as mock_get_client:
        # Mock response structure
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].inline_data.data = b"fake_audio_data"
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        with patch("tts_service.OUTPUT_DIR", tmp_path):
            with patch("tts_service.load_personas", return_value={}):
                req = GenerateRequest(voice="Zephyr", text="Hello")
                res = await generate_speech(req)
                
                assert res.success is True
                assert res.file_path is not None
                # Check file was created
                files = list(tmp_path.glob("*.wav"))
                assert len(files) == 1

@pytest.mark.asyncio
async def test_generate_speech_with_persona(tmp_path):
    with patch("tts_service.get_genai_client") as mock_get_client:
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].inline_data.data = b"fake_audio"
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        mock_personas = {
            "busy_boss": {
                "name": "Busy Boss",
                "tone_instructions": "Fast pace, annoyed tone."
            }
        }
        
        with patch("tts_service.OUTPUT_DIR", tmp_path):
            with patch("tts_service.load_personas", return_value=mock_personas):
                req = GenerateRequest(voice="Fenrir", text="Hi", persona_id="busy_boss")
                res = await generate_speech(req)
                
                assert res.success is True
                # Check metadata file was created
                txt_files = list(tmp_path.glob("*.txt"))
                assert len(txt_files) == 1

@pytest.mark.asyncio
async def test_batch_generate():
    with patch("tts_service.generate_speech") as mock_single:
        mock_single.return_value = GenerateResponse(success=True, file_path="test.wav")
        
        voices = ["V1", "V2", "V3"]
        results = await generate_batch(voices, "text", None, GeminiModel.FLASH)
        
        assert len(results) == 3
        assert mock_single.call_count == 3
        assert all(r.success for r in results)
