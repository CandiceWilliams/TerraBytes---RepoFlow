import google.generativeai as genai
from .config import settings

genai.configure(api_key=settings.gemini_api_key)

class GeminiClient:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_content(self, prompt: str):
        response = self.model.generate_content(prompt)
        return response.text

gemini_client = GeminiClient()