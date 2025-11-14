import time
from ollama import AsyncClient

class LLMService:
    def __init__(self, model="qwen3:30b"):
        self.model = model
    
    async def generate(self, prompt):
        """Генерация ответа с использованием qwen3:30b"""
        start = time.time()
        try:
            client = AsyncClient()
            response = await client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': 0.3, 
                    'top_p': 0.9,
                    'num_ctx': 4096
                }
            )
            elapsed = time.time() - start
            print(f"LLM response generated in {elapsed:.2f} seconds")
            return response['response']
        except Exception as e:
            print(f"LLM error: {e}")
            return "Извините, произошла ошибка при обработке запроса."