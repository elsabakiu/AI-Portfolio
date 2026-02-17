from openai import OpenAI
import os

class LLMIntegration:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        print("✅ LLM initialized")
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate content using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # You can also use "gpt-4" if you have access
                messages=[
                    {"role": "system", "content": "You are an expert content creator focused on producing unique, authentic content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""