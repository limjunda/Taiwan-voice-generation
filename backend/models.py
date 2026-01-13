from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class GeminiModel(str, Enum):
    FLASH = "gemini-2.5-flash-preview-tts"
    PRO = "gemini-2.5-pro-preview-tts"

class GenerateRequest(BaseModel):
    voice: str
    text: str
    persona_id: Optional[str] = None
    model: GeminiModel = GeminiModel.FLASH

class GenerateResponse(BaseModel):
    success: bool
    file_path: Optional[str] = None
    metadata_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None

class BatchRequest(BaseModel):
    voices: List[str]
    text: str
    persona_id: Optional[str] = None
    model: GeminiModel = GeminiModel.FLASH
