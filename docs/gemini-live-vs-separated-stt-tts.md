# Gemini Live vs Separated STT/TTS Architecture

> **Purpose:** Document architectural considerations for the AI Training Suite voice processing.

---

## Overview

When building conversational AI systems, there are two main approaches for handling speech:

1. **Bidirectional (Gemini Live)** - Single API handles STT + LLM + TTS in one stream
2. **Separated Components** - Individual services for STT, LLM, and TTS

---

## Comparison

| Aspect | Gemini Live (Bidirectional) | Separated STT/TTS |
|--------|----------------------------|-------------------|
| **Latency** | Lower (single round-trip) | Higher (3 round-trips) |
| **Voice Control** | Limited to stream config | Full control per utterance |
| **Debugging** | Harder (black box) | Easier (inspect each step) |
| **Cost** | Single API call | Multiple API calls |
| **Flexibility** | Less (coupled) | More (mix & match) |
| **Persona Switching** | Mid-stream complex | Easy per-request |

---

## Gemini Live (Current Approach)

```
┌─────────────────────────────────────────────────────────┐
│                    Gemini Live API                      │
│                                                         │
│  Trainee Audio ──► STT ──► LLM ──► TTS ──► AI Audio    │
│                    (All in one bidirectional stream)    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Pros:**
- Lowest latency for natural conversation
- Single WebSocket connection
- Native audio I/O support
- Simpler infrastructure

**Cons:**
- Voice configured at session start (harder to switch mid-conversation)
- Less visibility into intermediate steps
- Debugging conversation flow is harder
- Coupled to Gemini ecosystem

**Best for:**
- Real-time conversation simulations
- When latency is critical
- When using Gemini for all components

---

## Separated Architecture (Alternative)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  STT        │     │  LLM        │     │  TTS        │
│  Service    │────►│  Service    │────►│  Service    │
│             │     │             │     │             │
│ Audio→Text  │     │ Text→Text   │     │ Text→Audio  │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Pros:**
- Full control over each component
- Can mix providers (Google STT, OpenAI LLM, Gemini TTS)
- Easy to debug and log intermediate steps
- Voice/persona can change per response
- Easier A/B testing of components

**Cons:**
- Higher latency (3 API calls vs 1)
- More infrastructure to manage
- More complex error handling
- Higher cost (3 billable calls)

**Best for:**
- When specific voice control is needed
- When debugging conversation quality
- When mixing different AI providers
- For batch processing or analysis

---

## Recommendation for Training Suite

### Current Decision: **Gemini Live** (Bidirectional)

The AI Training Suite uses Gemini Live because:
1. Real-time conversation is the primary use case
2. Latency matters for realistic training simulations
3. Single API simplifies deployment

### Voice Selection Tool (This Project)

The **Taiwan Voice Generator** is a **standalone selection tool** that:
1. Helps clients audition and choose voices
2. Outputs a voice configuration JSON
3. This config is then applied to Gemini Live session initialization

```python
# Example: Using selected voice in Gemini Live
config = {
    "voice": "Zephyr",      # From voice generator
    "persona": "busy_boss",  # From voice generator
    "model": "gemini-2.5-flash"
}

# Apply to Gemini Live session
session = gemini_live.create_session(
    speech_config=SpeechConfig(
        voice_config=VoiceConfig(
            prebuilt_voice_config=PrebuiltVoiceConfig(
                voice_name=config["voice"]
            )
        )
    ),
    system_instruction=personas[config["persona"]]["tone_instructions"]
)
```

---

## Future Considerations

If the Training Suite needs:
- **Mid-conversation voice changes** → Consider separated TTS
- **Detailed conversation analytics** → Consider separated STT for transcript access
- **Multiple AI provider comparison** → Consider separated architecture

For now, Gemini Live remains the recommended approach with voice pre-selection via this tool.

---

## Related Files

- [Taiwan Voice Generator Plan](./2026-01-14-taiwan-voice-generator.md)
- Training Suite Gemini Live Implementation (existing project)
