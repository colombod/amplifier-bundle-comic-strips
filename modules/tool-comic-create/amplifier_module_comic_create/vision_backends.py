"""Vision provider backends for comic_create review_asset.

Each backend wraps one SDK client and exposes a single async ``review()``
method that takes base64-encoded image parts and a prompt string and returns
the raw text response from the model.

The ``VisionBackend`` Protocol defines the interface; concrete backends
(``AnthropicVisionBackend``, ``OpenAIVisionBackend``, ``GeminiVisionBackend``)
implement it.  Tests can use ``TestVisionBackend`` from conftest — a real class
that returns canned responses without any SDK calls.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VisionBackend(Protocol):
    """Protocol for vision review backends."""

    async def review(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str: ...


class AnthropicVisionBackend:
    """Vision backend that calls the Anthropic messages API."""

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    async def review(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str:
        content: list[dict[str, Any]] = []
        for img in image_parts:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img["media_type"],
                        "data": img["data"],
                    },
                }
            )
        content.append({"type": "text", "text": prompt})
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )
        return str(response.content[0].text)


class OpenAIVisionBackend:
    """Vision backend that calls the OpenAI chat completions API."""

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    async def review(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str:
        msg_content: list[dict[str, Any]] = []
        for img in image_parts:
            data_uri = f"data:{img['media_type']};base64,{img['data']}"
            msg_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_uri},
                }
            )
        msg_content.append({"type": "text", "text": prompt})
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": msg_content}],
        )
        return str(response.choices[0].message.content)


class GeminiVisionBackend:
    """Vision backend that calls the Google Gemini generate_content API."""

    def __init__(self, client: Any, model: str) -> None:
        self._client = client
        self._model = model

    async def review(
        self, image_parts: list[dict[str, str]], prompt: str
    ) -> str:
        import base64 as _b64

        from google.genai import types  # type: ignore[import-untyped]

        parts: list[Any] = []
        for img in image_parts:
            img_bytes = _b64.b64decode(img["data"])
            parts.append(
                types.Part.from_bytes(data=img_bytes, mime_type=img["media_type"])
            )
        parts.append(types.Part.from_text(text=prompt))
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=parts,
        )
        return str(response.text)
