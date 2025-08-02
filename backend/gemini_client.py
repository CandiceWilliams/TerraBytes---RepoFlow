# import google.generativeai as genai
# from .config import settings

# genai.configure(api_key=settings.gemini_api_key)

# class GeminiClient:
#     def __init__(self):
#         self.model = genai.GenerativeModel('gemini-pro')
    
#     async def generate_content(self, prompt: str):
#         response = self.model.generate_content(prompt)
#         return response.text

# gemini_client = GeminiClient()

from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)