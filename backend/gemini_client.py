from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyDAkKSlkPXRva8ywSZKOUt0zpxReHKTweo")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)