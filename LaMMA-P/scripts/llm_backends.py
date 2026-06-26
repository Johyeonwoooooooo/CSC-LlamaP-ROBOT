"""LLM 백엔드 라우팅.

모델명(gpt_version 문자열)에 따라 호출 대상을 자동 분기한다.
  - "gpt"  포함  →  OpenAI 클라우드 (기존 동작, openai.api_key 사용)
  - 그 외(llama 등) →  OpenAI 호환 로컬 엔드포인트 (기본: Ollama localhost:11434/v1)

Ollama 는 OpenAI 호환 /v1/chat/completions 를 제공하므로,
GPT/Llama 모두 chat.completions 한 경로로 통일해서 호출한다.
(구식 completions 엔드포인트는 Ollama 가 제대로 지원하지 않으므로 쓰지 않는다.)

환경변수로 조정 가능:
  LLAMA_BASE_URL  (기본 http://localhost:11434/v1)
  LLAMA_API_KEY   (기본 "ollama" — Ollama 는 아무 값이나 받음)
  LLAMA_MODEL     (기본 "llama3.1:8b" — friendly 이름을 줬을 때 실제 서빙 태그)
"""
import os

import openai
from openai import OpenAI

_clients = {}


def is_local(model_version: str) -> bool:
    """gpt 계열이 아니면 로컬(OpenAI 호환) 엔드포인트로 본다."""
    return "gpt" not in model_version.lower()


def resolve_model(model_version: str) -> str:
    """사용자가 준 모델명을 실제 서빙 모델명(Ollama 태그)으로 변환."""
    if not is_local(model_version):
        return model_version
    if ":" in model_version:
        # 이미 ollama 태그 형식 (예: "llama3.1:8b", "llama2:13b")
        return model_version
    # friendly 이름(예: "llama-3.1-8b") → 기본 태그
    return os.environ.get("LLAMA_MODEL", "llama3.1:8b")


def get_client(model_version: str) -> OpenAI:
    """모델 계열에 맞는 OpenAI 클라이언트를 (캐시해서) 돌려준다."""
    if is_local(model_version):
        base_url = os.environ.get("LLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = os.environ.get("LLAMA_API_KEY", "ollama")
        cache_key = ("local", base_url)
    else:
        base_url = None
        api_key = openai.api_key or os.environ.get("OPENAI_API_KEY", "")
        cache_key = ("openai", base_url)
    if cache_key not in _clients:
        _clients[cache_key] = OpenAI(api_key=api_key, base_url=base_url)
    return _clients[cache_key]


def chat(prompt, model_version, max_tokens=1300, temperature=0,
         frequency_penalty=0, stop=None):
    """문자열/메시지 리스트 둘 다 받아 chat.completions 로 호출.

    반환값은 기존 query_model 과 동일한 (response_obj, text) 튜플.
    """
    client = get_client(model_version)
    served = resolve_model(model_version)
    messages = prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]
    resp = client.chat.completions.create(
        model=served,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        stop=stop,
    )
    return resp, resp.choices[0].message.content.strip()
