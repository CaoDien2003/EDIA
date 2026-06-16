from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


class GroqLLM:

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
