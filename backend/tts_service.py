import os
import struct
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
from google.genai import types
from auth import get_genai_client
from data_manager import load_personas
from models import GenerateRequest, GenerateResponse, GeminiModel

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


async def generate_speech(request: GenerateRequest) -> GenerateResponse:
    """Generate speech using Gemini TTS."""
    try:
        client = get_genai_client()
        personas = load_personas()
        
        # Build prompt with persona instructions
        prompt = request.text
        persona_name = "default"
        if request.persona_id and request.persona_id in personas:
            persona = personas[request.persona_id]
            persona_name = persona["name"]
            prompt = f"Read aloud in {persona['tone_instructions']}\n\n{request.text}"
        
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
        
        # Save audio file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        safe_persona_name = persona_name.replace(" ", "_")
        base_name = f"{timestamp}_{request.voice}_{safe_persona_name}"
        audio_path = OUTPUT_DIR / f"{base_name}.wav"
        metadata_path = OUTPUT_DIR / f"{base_name}.txt"
        
        with open(audio_path, "wb") as f:
            f.write(wav_data)
        
        # Save metadata
        metadata = {
            "voice": request.voice,
            "persona": persona_name,
            "model": request.model.value,
            "text": request.text,
            "generated_at": timestamp,
        }
        if request.persona_id and request.persona_id in personas:
            metadata["tone_instructions"] = personas[request.persona_id]["tone_instructions"]
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            for k, v in metadata.items():
                f.write(f"{k}: {v}\n")
        
        return GenerateResponse(
            success=True,
            file_path=f"{base_name}.wav",
            metadata_path=f"{base_name}.txt"
        )
        
    except Exception as e:
        return GenerateResponse(success=False, error=str(e))


async def generate_batch(
    voices: List[str],
    text: str,
    persona_id: str | None,
    model: GeminiModel,
    concurrency: int = 5
) -> List[GenerateResponse]:
    """Generate speech for multiple voices in parallel."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def generate_with_limit(voice: str):
        async with semaphore:
            request = GenerateRequest(
                voice=voice,
                text=text,
                persona_id=persona_id,
                model=model
            )
            return await generate_speech(request)
    
    tasks = [generate_with_limit(v) for v in voices]
    return await asyncio.gather(*tasks)
