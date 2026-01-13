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
    tone_instructions: Optional[str] = None  # For custom personas or overrides
    model: GeminiModel = GeminiModel.FLASH

# ... GenerateResponse stays same ...

class BatchRequest(BaseModel):
    voices: List[str]
    text: str
    persona_id: Optional[str] = None
    tone_instructions: Optional[str] = None
    model: GeminiModel = GeminiModel.FLASH
