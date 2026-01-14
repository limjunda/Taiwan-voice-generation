import os
import struct
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from google.genai import types
from auth import get_genai_client
from data_manager import load_personas, load_custom_personas
from models import GenerateRequest, GenerateResponse, GeminiModel
from session_service import (
    get_active_session_id, 
    get_session_folder, 
    add_file_to_session,
    SESSIONS_DIR
)

# Legacy output for backward compatibility
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_audio_mime_type(mime_type: str) -> dict:
    """Parse bits per sample and rate from audio MIME type string."""
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Convert raw audio data to WAV format."""
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data


def get_all_personas() -> dict:
    """Get both built-in and custom personas."""
    personas = load_personas()
    try:
        custom = load_custom_personas()
        personas.update(custom)
    except:
        pass
    return personas


def get_output_folder(session_id: Optional[str] = None) -> Path:
    """Get the output folder for the current or specified session."""
    if session_id:
        return get_session_folder(session_id)
    
    active_session_id = get_active_session_id()
    if active_session_id:
        return get_session_folder(active_session_id)
    
    # Fallback to legacy output folder
    return OUTPUT_DIR


async def generate_speech(request: GenerateRequest, session_id: Optional[str] = None) -> GenerateResponse:
    """Generate speech using Gemini TTS."""
    try:
        client = get_genai_client()
        personas = get_all_personas()
        
        # Build prompt with persona instructions
        prompt = request.text
        persona_data = None
        persona_name = "default"
        
        if request.persona_id and request.persona_id in personas:
            persona_data = personas[request.persona_id]
            persona_name = persona_data.get("name", request.persona_id)
            tone = persona_data.get("tone_instructions", "")
            if tone:
                prompt = f"Read aloud in {tone}\n\n{request.text}"
        
        # Build content using types
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        # Build config with speech settings
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=request.voice
                    )
                ),
            ),
        )
        
        # Generate audio using streaming
        audio_chunks = []
        mime_type = None
        
        for chunk in client.models.generate_content_stream(
            model=request.model.value,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            part = chunk.candidates[0].content.parts[0]
            if part.inline_data and part.inline_data.data:
                audio_chunks.append(part.inline_data.data)
                if mime_type is None:
                    mime_type = part.inline_data.mime_type
        
        if not audio_chunks:
            return GenerateResponse(success=False, error="No audio data received")
        
        # Combine all audio chunks
        audio_data = b"".join(audio_chunks)
        
        # Convert to WAV
        wav_data = convert_to_wav(audio_data, mime_type or "audio/L16;rate=24000")
        
        # Get output folder (session folder or legacy)
        output_folder = get_output_folder(session_id)
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_persona_name = persona_name.replace(" ", "_")
        base_name = f"{timestamp}_{request.voice}_{safe_persona_name}"
        audio_path = output_folder / f"{base_name}.wav"
        metadata_path = output_folder / f"{base_name}.txt"
        
        with open(audio_path, "wb") as f:
            f.write(wav_data)
        
        # Save comprehensive metadata
        metadata_lines = [
            f"voice: {request.voice}",
            f"persona_id: {request.persona_id or 'none'}",
            f"persona_name: {persona_name}",
        ]
        
        # Add full persona settings if available
        if persona_data:
            metadata_lines.extend([
                f"local_name: {persona_data.get('local_name', '')}",
                f"archetype: {persona_data.get('archetype', '')}",
                f"traits: {persona_data.get('traits', '')}",
                f"tone_instructions: {persona_data.get('tone_instructions', '')}",
                f"recommended_voice: {persona_data.get('recommended_voice', '')}",
                f"is_custom: {persona_data.get('is_custom', False)}",
            ])
        
        metadata_lines.extend([
            f"model: {request.model.value}",
            f"text: {request.text}",
            f"generated_at: {timestamp}",
        ])
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("\n".join(metadata_lines))
        
        # Update session if active
        active_session = session_id or get_active_session_id()
        if active_session:
            add_file_to_session(active_session, f"{base_name}.wav", request.voice)
        
        return GenerateResponse(
            success=True,
            file_path=f"{base_name}.wav",
            metadata_path=f"{base_name}.txt",
            session_id=active_session
        )
        
    except Exception as e:
        return GenerateResponse(success=False, error=str(e))


async def generate_batch(
    voices: List[str],
    text: str,
    persona_id: str | None = None,
    model: str = "gemini-2.5-flash-preview-tts",
    session_id: Optional[str] = None
) -> List[GenerateResponse]:
    """Generate batch of audio files for multiple voices."""
    semaphore = asyncio.Semaphore(5)
    
    async def generate_one(voice: str) -> GenerateResponse:
        async with semaphore:
            request = GenerateRequest(
                voice=voice,
                text=text,
                persona_id=persona_id,
                model=GeminiModel(model)
            )
            return await generate_speech(request, session_id)
    
    tasks = [generate_one(v) for v in voices]
    return await asyncio.gather(*tasks)
