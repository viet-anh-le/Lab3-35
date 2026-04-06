import os
import time
import google.generativeai as genai
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        # In Gemini, system instruction is passed during model initialization or as a prefix
        # For simplicity in this lab, we'll prepend it if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.model.generate_content(full_prompt)

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Try to extract text robustly. Some Gemini responses may not populate response.text
        content = ""
        try:
            if hasattr(response, "text") and response.text:
                content = response.text
            else:
                # Try candidates (first candidate preferred)
                candidates = getattr(response, "candidates", None)
                if candidates:
                    cand = candidates[0]
                    # candidate may have text, content, or parts
                    if hasattr(cand, "text") and cand.text:
                        content = cand.text
                    elif hasattr(cand, "content") and cand.content:
                        cont = cand.content
                        if isinstance(cont, str):
                            content = cont
                        else:
                            # join parts
                            try:
                                content = "".join([getattr(p, "text", str(p)) for p in cont])
                            except Exception:
                                content = str(cont)
                # fallback to response.output if present
                if not content and hasattr(response, "output") and response.output:
                    try:
                        first = response.output[0]
                        if hasattr(first, "content") and first.content:
                            cont = first.content
                            if isinstance(cont, str):
                                content = cont
                            else:
                                content = "".join([getattr(p, "text", str(p)) for p in cont])
                    except Exception:
                        pass
        except Exception:
            try:
                content = str(response)
            except Exception:
                content = ""

        # Extract usage metadata safely
        usage = {}
        try:
            um = getattr(response, "usage_metadata", None)
            if um is not None:
                usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", None),
                    "completion_tokens": getattr(um, "candidates_token_count", None),
                    "total_tokens": getattr(um, "total_token_count", None),
                }
        except Exception:
            usage = {}

        return {"content": content, "usage": usage, "latency_ms": latency_ms, "provider": "google"}

    def stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            yield chunk.text
