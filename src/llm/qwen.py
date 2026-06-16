import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import LLM_MODEL, MAX_NEW_TOKENS


class QwenLLM:

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        self.model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

    def generate(self, prompt: str) -> str:
        # Use chat template with thinking disabled for faster RAG inference
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)

        with torch.inference_mode():
            outputs = self.model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)

        # Decode only the newly generated tokens, not the echoed input
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)
