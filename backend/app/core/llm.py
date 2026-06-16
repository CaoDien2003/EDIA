from functools import lru_cache
from app.config import settings

Messages = list[dict]


class _LLM:
    def generate(self, messages: Messages) -> str:
        raise NotImplementedError


class _QwenLLM(_LLM):
    def __init__(self) -> None:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM

        self._tok = AutoTokenizer.from_pretrained(settings.llm_model)
        self._model = AutoModelForCausalLM.from_pretrained(
            settings.llm_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self._model.eval()

    def generate(self, messages: Messages) -> str:
        import torch

        text = self._tok.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,  # disable chain-of-thought to avoid <think> artifacts
        )
        inputs = self._tok(text, return_tensors="pt").to(self._model.device)
        with torch.inference_mode():
            out = self._model.generate(
                **inputs,
                max_new_tokens=settings.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.1,  # prevent "A A A A..." repetition loops
            )
        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        return self._tok.decode(new_tokens, skip_special_tokens=True).strip()


class _GroqLLM(_LLM):
    def __init__(self) -> None:
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key)

    def generate(self, messages: Messages) -> str:
        resp = self._client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
        )
        return resp.choices[0].message.content


@lru_cache(maxsize=1)
def get_llm() -> _LLM:
    if settings.llm_backend == "groq":
        return _GroqLLM()
    return _QwenLLM()
