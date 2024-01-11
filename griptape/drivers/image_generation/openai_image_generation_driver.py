from __future__ import annotations

import base64
from typing import Literal

import openai
from attr import field, Factory, define

from griptape.artifacts import ImageArtifact
from griptape.drivers import BaseImageGenerationDriver


@define
class OpenAiImageGenerationDriver(BaseImageGenerationDriver):
    """Driver for the OpenAI image generation API.

    Attributes:
        model: OpenAI model, for example 'dall-e-2' or 'dall-e-3'.
        api_type: OpenAI API type, for example 'open_ai' or 'azure'.
        api_version: API version.
        base_url: API URL.
        api_key: OpenAI API key.
        organization: OpenAI organization ID.
        style: Optional and only supported for dall-e-3, can be either 'vivid' or 'natural'.
        quality: Optional and only supported for dall-e-3. Accepts 'standard', 'hd'.
        image_size: Size of the generated image. Must be one of the following, depending on the requested model:
            dall-e-2: [256x256, 512x512, 1024x1024]
            dall-e-3: [1024x1024, 1024x1792, 1792x1024]
        response_format: The response format. Currently only supports 'b64_json' which will return
            a base64 encoded image in a JSON object.
    """

    api_type: str = field(default=openai.api_type, kw_only=True)
    api_version: Optional[str] = field(default=openai.api_version, kw_only=True)
    base_url: str = field(default=None, kw_only=True)
    api_key: Optional[str] = field(default=None, kw_only=True)
    organization: Optional[str] = field(default=openai.organization, kw_only=True)
    client: openai.OpenAI = field(
        default=Factory(
            lambda self: openai.OpenAI(api_key=self.api_key, base_url=self.base_url, organization=self.organization),
            takes_self=True,
        )
    )
    style: Optional[str] = field(default=None, kw_only=True)
    quality: Literal["standard"] | Literal["hd"] = field(default="standard", kw_only=True)
    image_size: (
        Literal["256x256"] | Literal["512x512"] | Literal["1024x1024"] | Literal["1024x1792"] | Literal["1792x1024"]
    ) = field(default="1024x1024", kw_only=True)
    response_format: Literal["b64_json"] = field(default="b64_json", kw_only=True)

    def try_text_to_image(self, prompts: list[str], negative_prompts: Optional[list[str]] = None) -> ImageArtifact:
        prompt = ", ".join(prompts)

        additional_params = {}

        if self.style:
            additional_params["style"] = self.style

        if self.quality:
            additional_params["quality"] = self.quality

        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=self.image_size,
            response_format=self.response_format,
            n=1,
            **additional_params,
        )

        if not response.data[0] or not response.data[0].b64_json:
            raise Exception("Failed to generate image")

        image_data = base64.b64decode(response.data[0].b64_json)
        image_dimensions = self._image_size_to_ints(self.image_size)

        return ImageArtifact(
            value=image_data,
            mime_type="image/png",
            width=image_dimensions[0],
            height=image_dimensions[1],
            model=self.model,
            prompt=prompt,
        )

    def try_image_variation(
        self, prompts: list[str], image: ImageArtifact, negative_prompts: Optional[list[str]] = None
    ) -> ImageArtifact:
        raise NotImplementedError(f"{self.__class__.__name__} does not support variation")

    def try_image_inpainting(
        self, prompts: list[str], image: ImageArtifact, mask: ImageArtifact, negative_prompts: Optional[list[str]] = None
    ) -> ImageArtifact:
        raise NotImplementedError(f"{self.__class__.__name__} does not support inpainting")

    def try_image_outpainting(
        self, prompts: list[str], image: ImageArtifact, mask: ImageArtifact, negative_prompts: Optional[list[str]] = None
    ) -> ImageArtifact:
        raise NotImplementedError(f"{self.__class__.__name__} does not support outpainting")

    def _image_size_to_ints(self, image_size: str) -> list[int]:
        return [int(x) for x in image_size.split("x")]
