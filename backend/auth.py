import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_genai_client() -> genai.Client:
    """Get Gemini client using API key or service account."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        return genai.Client(api_key=api_key)
    
    # Fall back to service account
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("GCP_PROJECT_ID")
    
    if credentials_path and project_id:
        return genai.Client(
            vertexai=True,
            project=project_id,
            location="us-central1"
        )
    
    raise ValueError("No valid credentials found. Set GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS")

def validate_credentials() -> dict:
    """Validate credentials on startup."""
    try:
        client = get_genai_client()
        return {"valid": True, "method": "api_key" if os.getenv("GEMINI_API_KEY") else "service_account"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
