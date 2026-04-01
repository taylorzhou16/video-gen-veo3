#!/usr/bin/env python3
"""
Vico Tools Veo3 - Video Creation API CLI Tools (Veo 3.1 Fast version)

Uses Compass API (Google Gen AI SDK) to call Veo 3.1 Fast

Usage:
  python video_gen_tools.py video --prompt <text> --duration <seconds>
  python video_gen_tools.py video --image <path> --prompt <text>
  python video_gen_tools.py image --prompt <text> --aspect-ratio <ratio>
  python video_gen_tools.py music --prompt <text> --style <style>
  python video_gen_tools.py tts --text <text> --voice <voice_type>
  python video_gen_tools.py check
"""

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Configuration Management ==============

CONFIG_FILE = Path.home() / ".claude" / "skills" / "video-gen-veo3" / "config.json"

# Compass API Base URL
COMPASS_BASE_URL = "https://compass.llm.shopee.io/compass-api/v1"


def load_config() -> Dict[str, str]:
    """Load API keys from config file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


class Config:
    """Load config from file and environment variables (file takes priority)"""

    _cached_config = None

    @classmethod
    def _get_config(cls) -> Dict[str, str]:
        if cls._cached_config is None:
            cls._cached_config = load_config()
        return cls._cached_config

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Get from config file first, then environment variable"""
        config = cls._get_config()
        return config.get(key, os.getenv(key, default))

    # Compass API (Veo 3)
    @property
    def COMPASS_API_KEY(self) -> str:
        return self.get("COMPASS_API_KEY", "")

    # Veo 3.1 Fast configuration
    VEO3_MODEL: str = "veo-3.1-fast-generate-001"

    # Suno API
    @property
    def SUNO_API_KEY(self) -> str:
        return self.get("SUNO_API_KEY", "")

    SUNO_API_URL: str = "https://api.sunoapi.org/api/v1"

    # Volcengine TTS
    @property
    def VOLCENGINE_TTS_APP_ID(self) -> str:
        return self.get("VOLCENGINE_TTS_APP_ID", "")

    @property
    def VOLCENGINE_TTS_TOKEN(self) -> str:
        return self.get("VOLCENGINE_TTS_ACCESS_TOKEN", "")


Config = Config()


# ============== Image Size Validation and Processing ==============

def validate_and_resize_image(
    image_path: str,
    output_path: str = None,
    min_size: int = 720,
    max_size: int = 2048,
    target_size: int = 1280
) -> Dict[str, Any]:
    """
    Validate and adjust image size

    Args:
        image_path: Image path
        output_path: Output path (auto-generated if None)
        min_size: Minimum dimension limit (will scale up if smaller)
        max_size: Maximum dimension limit (will scale down if larger)
        target_size: Target size (used when scaling up)

    Returns:
        {
            "success": True,
            "original_size": (w, h),
            "new_size": (w, h),
            "resized": True/False,
            "output_path": "..."
        }
    """
    try:
        from PIL import Image
    except ImportError:
        logger.warning("⚠️ PIL not installed, skipping image size check")
        return {
            "success": True,
            "original_size": None,
            "new_size": None,
            "resized": False,
            "output_path": image_path
        }

    try:
        img = Image.open(image_path)
        w, h = img.size

        min_dim = min(w, h)
        max_dim = max(w, h)

        need_resize = False
        scale = 1.0

        if min_dim < min_size:
            scale = target_size / min_dim
            need_resize = True
            logger.info(f"📐 Image size too small {w}x{h}, need to scale up to at least {min_size}px")
        elif max_dim > max_size:
            scale = max_size / max_dim
            need_resize = True
            logger.info(f"📐 Image size too large {w}x{h}, need to scale down to at most {max_size}px")

        if need_resize:
            new_w = int(w * scale)
            new_h = int(h * scale)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_resized{ext}"

            img_resized.save(output_path, quality=95)
            logger.info(f"📐 Image size adjusted: {w}x{h} → {new_w}x{new_h}")

            return {
                "success": True,
                "original_size": (w, h),
                "new_size": (new_w, new_h),
                "resized": True,
                "output_path": output_path
            }

        return {
            "success": True,
            "original_size": (w, h),
            "new_size": (w, h),
            "resized": False,
            "output_path": image_path
        }

    except Exception as e:
        logger.error(f"❌ Image size processing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "output_path": image_path
        }


# ============== Storyboard / Creative Reading Tools ==============

def get_aspect_from_storyboard(storyboard_path: str) -> Optional[str]:
    """Read aspect_ratio from storyboard.json"""
    try:
        with open(storyboard_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("aspect_ratio")
    except Exception:
        return None


def get_music_config_from_creative(creative_path: str) -> Optional[Dict[str, Any]]:
    """Read music config from creative.json"""
    try:
        with open(creative_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            music = data.get("music", {})
            return {
                "need_bgm": music.get("need_bgm", True),
                "style": music.get("style"),
                "prompt": music.get("prompt")  # optional detailed description
            }
    except Exception:
        return None


# ============== Veo 3 Video Generation (using Google Gen AI SDK) ==============

class Veo3Client:
    """
    Veo 3.1 Fast Video Generation Client (using Google Gen AI SDK)

    Features:
    - Text-to-video + audio
    - Image-to-video + audio (image as first frame)
    - Supported resolutions: 720p, 1080p, 4k
    - Automatic audio generation

    Pricing:
    - Video + Audio: $0.15/second (720p/1080p), $0.35/second (4k)
    - Video only: $0.10/second (720p/1080p), $0.30/second (4k)
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Get Google Gen AI client"""
        if self._client is None:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(
                    vertexai=True,
                    api_key=Config.COMPASS_API_KEY,
                    http_options=types.HttpOptions(
                        api_version='v1',
                        base_url=COMPASS_BASE_URL,
                    )
                )
            except ImportError:
                raise ImportError("Please install google-genai: pip install google-genai")
        return self._client

    async def create_video(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        generate_audio: bool = True,
        image_path: str = None,
        output: str = None
    ) -> Dict[str, Any]:
        """
        Video generation (text-to-video or image-to-video)

        Args:
            prompt: Video description
            duration: Duration (seconds) - Veo 3.1 Fast only supports 4, 6, 8 seconds
            aspect_ratio: Aspect ratio (16:9, 9:16)
            resolution: Resolution (720p, 1080p, 4k) - 1080p/4k requires duration=8
            generate_audio: Whether to generate audio
            image_path: Image path (used for image-to-video, as first frame)
            output: Output file path
        """
        try:
            from google.genai.types import GenerateVideosConfig, Image
        except ImportError:
            return {"success": False, "error": "Please install google-genai: pip install google-genai"}

        client = self._get_client()

        # Validate duration parameter (Veo 3.1 Fast only supports 4, 6, 8 seconds)
        valid_durations = [4, 6, 8]
        if duration not in valid_durations:
            logger.warning(f"⚠️ Veo 3.1 Fast only supports 4/6/8 seconds, auto-adjusted to 8 seconds")
            duration = 8

        # 1080p/4k requires 8 second duration
        if resolution in ["1080p", "4k"] and duration != 8:
            logger.warning(f"⚠️ {resolution} resolution requires 8 second duration, auto-adjusted")
            duration = 8

        # Build configuration
        config = GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            duration_seconds=str(duration),
            resolution=resolution,
        )

        # Process image input (image-to-video)
        image_param = None
        if image_path:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image not found: {image_path}"}

            with open(image_path, 'rb') as f:
                img_bytes = f.read()

            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                       '.webp': 'image/webp'}
            mime_type = mime_map.get(ext, 'image/jpeg')

            image_param = Image(
                image_bytes=base64.b64encode(img_bytes).decode(),
                mime_type=mime_type,
            )
            logger.info(f"📤 Creating Veo 3 image-to-video task: {prompt[:50]}...")
        else:
            logger.info(f"📤 Creating Veo 3 text-to-video task: {prompt[:50]}...")

        try:
            # Call API
            kwargs = {
                "model": Config.VEO3_MODEL,
                "prompt": prompt,
                "config": config,
            }
            if image_param:
                kwargs["image"] = image_param

            operation = client.models.generate_videos(**kwargs)

            logger.info(f"✅ Task submitted, waiting for completion...")

            # Wait for completion
            video_url = await self._wait_for_operation(client, operation)

            if video_url and output:
                await self._download_file(video_url, output)
                return {"success": True, "video_url": video_url, "output": output}

            return {"success": bool(video_url), "video_url": video_url}

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"success": False, "error": "COMPASS_API_KEY invalid or not set"}
            elif "402" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": "Insufficient balance, please top up"}
            elif "429" in error_msg or "rate" in error_msg.lower():
                return {"success": False, "error": "Rate limit exceeded, please retry later"}
            logger.error(f"❌ Veo 3 video generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_operation(self, client, operation, max_wait: int = 600) -> Optional[str]:
        """Wait for operation to complete"""
        start_time = time.monotonic()

        try:
            from google.genai.types import Video
        except ImportError:
            return None

        logger.info(f"⏳ Waiting for Veo 3 task to complete...")

        while not operation.done:
            elapsed = time.monotonic() - start_time
            if elapsed > max_wait:
                logger.error(f"❌ Task timeout ({max_wait} seconds)")
                return None

            logger.info(f"   [{int(elapsed)}s] Status: processing...")
            await asyncio.sleep(15)
            operation = client.operations.get(operation)

        logger.info(f"   Operation completed, parsing result...")

        # Check for errors
        if operation.error:
            error_msg = operation.error.get('message', str(operation.error))
            logger.error(f"❌ Video generation failed: {error_msg}")
            return {"success": False, "error": error_msg, "video_url": None}

        # Print raw operation info
        logger.info(f"   operation.done: {operation.done}")

        # Try multiple ways to get video URL
        video_uri = None

        # Method 1: Get from operation.result.generated_videos
        try:
            if operation.result and operation.result.generated_videos:
                gen_video = operation.result.generated_videos[0]
                if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                    video_uri = gen_video.video.uri
                    logger.info(f"   Successfully retrieved from result.generated_videos[0].video.uri")
        except Exception as e:
            logger.debug(f"   Method 1 failed: {e}")

        # Method 2: Get from operation.response
        if not video_uri and operation.response:
            try:
                if hasattr(operation.response, 'generated_videos'):
                    gen_video = operation.response.generated_videos[0]
                    if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                        video_uri = gen_video.video.uri
                        logger.info(f"   Successfully retrieved from response.generated_videos[0].video.uri")
            except Exception as e:
                logger.debug(f"   Method 2 failed: {e}")

        # Method 3: Get directly from operation
        if not video_uri:
            try:
                if hasattr(operation, 'generated_videos'):
                    gen_video = operation.generated_videos[0]
                    if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                        video_uri = gen_video.video.uri
                        logger.info(f"   Successfully retrieved from operation.generated_videos[0].video.uri")
            except Exception as e:
                logger.debug(f"   Method 3 failed: {e}")

        if video_uri:
            elapsed = time.monotonic() - start_time
            logger.info(f"✅ Veo 3 task completed (duration: {int(elapsed)} seconds)")
            return video_uri
        else:
            logger.error(f"❌ Unable to parse video URL")
            # Print operation object attributes for debugging
            logger.debug(f"   operation attributes: {dir(operation)}")
            if operation.response:
                logger.debug(f"   response attributes: {dir(operation.response)}")
            return None

    async def _download_file(self, url: str, output_path: str):
        """Download file"""
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ Saved to: {output_path}")

    async def create_video_with_fallback(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        generate_audio: bool = True,
        image_path: str = None,
        output: str = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Video generation (with strict fallback strategy)

        Fallback order:
        1. Retry (up to max_retries times)
        2. Adjust prompt (simplify/optimize description)
        3. Adjust reference image (reduce size/change format)
        4. Finally fallback to text-to-video (only when no other options)

        Args:
            prompt: Video description
            duration: Duration (seconds)
            aspect_ratio: Aspect ratio
            resolution: Resolution
            generate_audio: Whether to generate audio
            image_path: Image path (used for image-to-video)
            output: Output file path
            max_retries: Maximum retry count
        """
        original_prompt = prompt
        original_image = image_path

        # Record fallback state
        fallback_state = {
            "stage": "initial",
            "retries": 0,
            "prompt_adjusted": False,
            "image_adjusted": False,
            "downgraded_to_t2v": False,
            "history": []
        }

        # Stage 1: Initial attempt + retry
        for retry in range(max_retries + 1):
            fallback_state["retries"] = retry
            fallback_state["stage"] = "retry" if retry > 0 else "initial"

            logger.info(f"📹 Attempting video generation (attempt {retry + 1})...")

            result = await self.create_video(
                prompt=prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                generate_audio=generate_audio,
                image_path=image_path,
                output=output
            )

            if result.get("success"):
                fallback_state["history"].append({
                    "stage": fallback_state["stage"],
                    "success": True,
                    "prompt": prompt[:100]
                })
                result["fallback_state"] = fallback_state
                return result

            # Record failure
            error = result.get("error", "Unknown error")
            fallback_state["history"].append({
                "stage": fallback_state["stage"],
                "success": False,
                "error": error,
                "prompt": prompt[:100]
            })

            # Check if error is retryable
            if "429" in error or "rate" in error.lower():
                logger.warning(f"⚠️ Rate limit exceeded, waiting 60 seconds before retry...")
                await asyncio.sleep(60)
                continue
            elif "timeout" in error.lower() or "network" in error:
                logger.warning(f"⚠️ Network/timeout error, waiting 30 seconds before retry...")
                await asyncio.sleep(30)
                continue
            elif "401" in error or "Unauthorized" in error:
                # Cannot resolve through retry, return directly
                return {"success": False, "error": error, "fallback_state": fallback_state}
            elif "402" in error or "quota" in error.lower():
                return {"success": False, "error": error, "fallback_state": fallback_state}

        # Stage 2: Adjust prompt
        fallback_state["stage"] = "adjust_prompt"
        fallback_state["prompt_adjusted"] = True

        adjusted_prompt = self._adjust_prompt(prompt)
        logger.info(f"📝 Adjusted prompt attempt: {adjusted_prompt[:50]}...")

        result = await self.create_video(
            prompt=adjusted_prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            generate_audio=generate_audio,
            image_path=image_path,
            output=output
        )

        fallback_state["history"].append({
            "stage": "adjust_prompt",
            "success": result.get("success", False),
            "prompt": adjusted_prompt[:100]
        })

        if result.get("success"):
            result["fallback_state"] = fallback_state
            return result

        # Stage 3: Adjust reference image (only for image-to-video)
        if image_path:
            fallback_state["stage"] = "adjust_image"
            fallback_state["image_adjusted"] = True

            adjusted_image = await self._adjust_reference_image(image_path)
            if adjusted_image:
                logger.info(f"🖼️ Adjusted reference image attempt: {adjusted_image}")

                result = await self.create_video(
                    prompt=adjusted_prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    generate_audio=generate_audio,
                    image_path=adjusted_image,
                    output=output
                )

                fallback_state["history"].append({
                    "stage": "adjust_image",
                    "success": result.get("success", False),
                    "image": adjusted_image
                })

                if result.get("success"):
                    result["fallback_state"] = fallback_state
                    return result

        # Stage 4: Final fallback to text-to-video (only when image-to-video unavailable)
        # Note: Fiction/short drama does not allow fallback to text-to-video
        if not image_path:
            fallback_state["stage"] = "downgrade_t2v"
            fallback_state["downgraded_to_t2v"] = True

            logger.warning(f"⚠️ Final fallback: using text-to-video mode")
            result = await self.create_video(
                prompt=adjusted_prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                generate_audio=generate_audio,
                image_path=None,
                output=output
            )

            fallback_state["history"].append({
                "stage": "downgrade_t2v",
                "success": result.get("success", False)
            })

            result["fallback_state"] = fallback_state
            return result

        # Image-to-video final failure, return error (no fallback)
        return {
            "success": False,
            "error": "Image-to-video generation failed, all fallback strategies attempted",
            "fallback_state": fallback_state,
            "suggestion": "Please check reference image quality or change prompt"
        }

    def _adjust_prompt(self, prompt: str) -> str:
        """
        Adjust prompt to improve success rate

        Strategy:
        1. Remove/rewrite sensitive words like copyright, celebrities, etc.
        2. Simplify overly complex descriptions
        3. Preserve core elements
        """
        # Sensitive words list (copyright, celebrities, brands, etc. that may cause generation failure)
        sensitive_patterns = [
            # Celebrity names (common)
            "taylor swift", "elon musk", "donald trump", "biden", "obama",
            "michael jackson", "madonna", "beyonce", "kanye", "kim kardashian",
            "leonardo dicaprio", "brad pitt", "tom cruise", "jennifer lawrence",
            # Brands/Copyright
            "disney", "marvel", "dc comics", "star wars", "harry potter",
            "nike", "adidas", "apple", "microsoft", "google", "facebook",
            "coca-cola", "pepsi", "mcdonalds", "starbucks",
            # Character names
            "mickey mouse", "batman", "superman", "spider-man", "iron man",
            "hulk", "thor", "captain america", "wonder woman",
            # Other sensitive words
            "celebrity", "famous person", "well-known",
        ]

        adjusted = prompt.lower()
        replaced_words = []

        for pattern in sensitive_patterns:
            if pattern in adjusted:
                # Replace with generic description
                adjusted = adjusted.replace(pattern, "person")
                replaced_words.append(pattern)

        if replaced_words:
            logger.info(f"📝 Removed sensitive words: {', '.join(replaced_words)}")

        # Simplification strategy: keep first 200 characters of core description
        if len(prompt) > 200:
            # Find first complete sentence
            simplified = prompt[:200]
            if '.' in simplified:
                last_period = simplified.rfind('.')
                simplified = simplified[:last_period + 1]
            logger.info(f"📝 Prompt simplified: {len(prompt)} -> {len(simplified)} characters")
            return simplified

        return prompt.strip()

    async def _adjust_reference_image(self, image_path: str) -> Optional[str]:
        """
        Adjust reference image to improve success rate

        Strategy:
        1. Reduce size to 1280px
        2. Convert format to JPEG
        """
        try:
            from PIL import Image
        except ImportError:
            logger.warning("⚠️ PIL not installed, cannot adjust image")
            return None

        try:
            img = Image.open(image_path)
            w, h = img.size

            # Reduce to target size
            target_size = 1280
            if max(w, h) > target_size:
                scale = target_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                logger.info(f"🖼️ Image reduced: {w}x{h} -> {new_w}x{new_h}")

            # Convert to RGB (remove alpha channel)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Save as JPEG
            base, _ = os.path.splitext(image_path)
            adjusted_path = f"{base}_adjusted.jpg"
            img.save(adjusted_path, quality=85)

            logger.info(f"🖼️ Image converted: {image_path} -> {adjusted_path}")
            return adjusted_path

        except Exception as e:
            logger.error(f"❌ Image adjustment failed: {e}")
            return None


# ============== Image Generation (Storyboard) ==============

class ImageClient:
    """
    Image Generation Client (for storyboard generation)

    Uses Compass API to call Gemini Flash Image model for image generation,
    used for fiction/short drama two-stage workflow: first generate storyboard,
    then use as video first frame.

    Fallback strategy:
    1. Default uses gemini-3.1-flash-image-preview
    2. Falls back to gemini-2.5-flash-image on failure
    """

    PRIMARY_MODEL = "gemini-3.1-flash-image-preview"
    FALLBACK_MODEL = "gemini-2.5-flash-image"

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Get Google Gen AI client"""
        if self._client is None:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(
                    vertexai=True,
                    api_key=Config.COMPASS_API_KEY,
                    http_options=types.HttpOptions(
                        api_version='v1',
                        base_url=COMPASS_BASE_URL,
                    )
                )
            except ImportError:
                raise ImportError("Please install google-genai: pip install google-genai")
        return self._client

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        reference_image: str = None,
        output: str = None
    ) -> Dict[str, Any]:
        """
        Image generation (for storyboard)

        Supports:
        - Text-to-image: only provide prompt
        - Image-to-image: provide prompt + reference_image

        Fallback strategy:
        1. Default uses PRIMARY_MODEL (gemini-3.1-flash-image-preview)
        2. Falls back to FALLBACK_MODEL (gemini-2.5-flash-image) on failure

        Args:
            prompt: Image description (image_prompt)
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            reference_image: Reference image path (for image-to-image/style transfer)
            output: Output file path
        """
        try:
            from google.genai.types import GenerateContentConfig, Modality, Part, ImageConfig
        except ImportError:
            return {"success": False, "error": "Please install google-genai: pip install google-genai"}

        client = self._get_client()

        logger.info(f"🖼️ Creating image generation task: {prompt[:50]}...")

        # Build contents
        contents = []

        # If reference image exists, add image (image-to-image)
        if reference_image and os.path.exists(reference_image):
            with open(reference_image, 'rb') as f:
                img_bytes = f.read()
            contents.append(Part.from_bytes(data=img_bytes, mime_type='image/png'))
            logger.info(f"  Using reference image: {reference_image}")

        # Add text prompt
        contents.append(prompt)

        # Try using primary model
        result = await self._generate_with_model(
            client, self.PRIMARY_MODEL, contents, aspect_ratio, output
        )

        if result.get("success"):
            result["model"] = self.PRIMARY_MODEL
            return result

        # Primary model failed, try fallback model
        error_msg = result.get("error", "")
        logger.warning(f"⚠️ Primary model {self.PRIMARY_MODEL} failed: {error_msg}")
        logger.info(f"🔄 Trying fallback model {self.FALLBACK_MODEL}...")

        result = await self._generate_with_model(
            client, self.FALLBACK_MODEL, contents, aspect_ratio, output
        )

        if result.get("success"):
            result["model"] = self.FALLBACK_MODEL
            result["fallback_used"] = True
            return result

        return result

    async def _generate_with_model(
        self,
        client,
        model: str,
        contents: list,
        aspect_ratio: str,
        output: str
    ) -> Dict[str, Any]:
        """Generate image using specified model"""
        from google.genai.types import GenerateContentConfig, Modality, ImageConfig

        try:
            logger.info(f"  Using model: {model}")

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=GenerateContentConfig(
                    response_modalities=[Modality.TEXT, Modality.IMAGE],
                    image_config=ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )

            logger.info(f"⏳ Waiting for image generation to complete...")

            # Parse result
            if response and response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        logger.info(f"  Text response: {part.text[:100]}...")
                    elif part.inline_data:
                        # Save image
                        image_bytes = part.inline_data.data
                        if output:
                            Path(output).parent.mkdir(parents=True, exist_ok=True)
                            with open(output, 'wb') as f:
                                if isinstance(image_bytes, str):
                                    f.write(base64.b64decode(image_bytes))
                                else:
                                    f.write(image_bytes)
                            logger.info(f"✅ Image saved: {output}")
                        return {"success": True, "output": output}

            return {"success": False, "error": "Image generation failed, unable to parse return result"}

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"success": False, "error": "COMPASS_API_KEY invalid or not set"}
            elif "402" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": "Insufficient balance, please top up"}
            elif "429" in error_msg or "rate" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                return {"success": False, "error": "Request rate limit exceeded or quota depleted"}
            elif "503" in error_msg or "UNAVAILABLE" in error_msg:
                return {"success": False, "error": "Service temporarily unavailable"}
            logger.error(f"❌ Image generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _download_file(self, url: str, output_path: str):
        """Download file"""
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ Image saved: {output_path}")


# ============== Suno Music Generation ==============

class SunoClient:
    """Suno Music Generation Client"""

    def __init__(self):
        import httpx
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, style: str, instrumental: bool = True, output: str = None) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "instrumental": instrumental,
            "model": "V3_5",
            "customMode": True,
            "style": style,
            "callbackUrl": "https://example.com/callback"
        }

        logger.info(f"🎵 Creating music generation task: {prompt[:50]}...")

        try:
            response = await self.client.post(
                f"{Config.SUNO_API_URL}/generate",
                json=payload,
                headers={"Authorization": f"Bearer {Config.SUNO_API_KEY}"}
            )
            response.raise_for_status()
            result = response.json()

            if result.get("code") != 200:
                return {"success": False, "error": result.get("msg", "Unknown error")}

            task_id = result["data"]["taskId"]
            logger.info(f"✅ Task created: {task_id}")

            audio_url = await self._wait_for_completion(task_id)

            if audio_url and output:
                await self._download_file(audio_url, output)
                return {"success": True, "audio_url": audio_url, "output": output}

            return {"success": True, "audio_url": audio_url, "task_id": task_id}

        except Exception as e:
            logger.error(f"❌ Suno music generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_completion(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        start_time = time.monotonic()

        logger.info(f"⏳ Waiting for music generation...")

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > max_wait:
                logger.error(f"❌ Task timeout ({max_wait} seconds)")
                return None

            try:
                response = await self.client.get(
                    f"{Config.SUNO_API_URL}/generate/record-info?taskId={task_id}",
                    headers={"Authorization": f"Bearer {Config.SUNO_API_KEY}"}
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") != 200:
                    logger.warning(f"⚠️ Query failed: {result.get('msg')}")
                    await asyncio.sleep(5)
                    continue

                data = result.get("data", {})
                status = data.get("status")

                if status == "SUCCESS":
                    tracks = data.get("response", {}).get("sunoData", [])
                    if tracks:
                        audio_url = tracks[0].get("audioUrl")
                        logger.info(f"✅ Music generation completed (duration: {int(elapsed)} seconds)")
                        return audio_url

                elif status == "FAILED":
                    logger.error("❌ Music generation failed")
                    return None

                await asyncio.sleep(5)

            except Exception as e:
                logger.warning(f"⚠️ Query exception: {e}")
                await asyncio.sleep(5)

    async def _download_file(self, url: str, output_path: str):
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ Music saved: {output_path}")

    async def close(self):
        await self.client.aclose()


# ============== Volcano Engine TTS ==============

class TTSClient:
    """Volcano Engine TTS Client"""

    VOICE_TYPES = {
        "female_narrator": "BV700_streaming",
        "female_gentle": "BV034_streaming",
        "male_narrator": "BV701_streaming",
        "male_warm": "BV033_streaming",
    }

    EMOTION_MAP = {
        "neutral": None,
        "happy": "happy",
        "sad": "sad",
        "gentle": "gentle",
        "serious": "serious",
    }

    async def synthesize(self, text: str, output: str, voice: str = "female_narrator", emotion: str = None, speed: float = 1.0) -> Dict[str, Any]:
        import httpx
        import uuid
        import base64

        voice_type = self.VOICE_TYPES.get(voice, "BV700_streaming")

        payload = {
            "app": {
                "appid": Config.VOLCENGINE_TTS_APP_ID,
                "token": "access_token",
                "cluster": "volcano_tts",
            },
            "user": {"uid": "vico_tts_user"},
            "audio": {
                "voice_type": voice_type,
                "encoding": "mp3",
                "rate": 24000,
                "speed_ratio": speed,
                "volume_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
            },
        }

        if emotion and emotion in self.EMOTION_MAP and self.EMOTION_MAP[emotion]:
            payload["audio"]["emotion"] = self.EMOTION_MAP[emotion]

        logger.info(f"🔊 TTS synthesis: {text[:30]}...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openspeech.bytedance.com/api/v1/tts",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer;{Config.VOLCENGINE_TTS_TOKEN}",
                    }
                )
                response.raise_for_status()
                result = response.json()

            code = result.get("code", -1)
            if code != 3000:
                return {"success": False, "error": result.get("message", f"API error: {code}")}

            audio_data = base64.b64decode(result.get("data", ""))
            if not audio_data:
                return {"success": False, "error": "Empty audio data"}

            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "wb") as f:
                f.write(audio_data)

            duration_ms = int(result.get("addition", {}).get("duration", "0"))
            logger.info(f"✅ TTS saved: {output} ({duration_ms}ms)")

            return {"success": True, "output": output, "duration_ms": duration_ms}

        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            return {"success": False, "error": str(e)}


# ============== Character/Persona Management ==============

class PersonaManager:
    """
    Character/Persona Manager

    Used to manage character reference images in projects, ensuring cross-shot character consistency.
    Only used when video involves characters, pure scenery/object videos don't need it.

    Usage:
        manager = PersonaManager(project_dir)
        manager.register("Xiao Mei", "female", "path/to/reference.jpg", "long hair, round face, glasses")
        ref_path = manager.get_reference("Xiao Mei")
        characters = manager.export_for_storyboard()
    """

    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else None
        self.personas = {}  # {persona_id: {name, gender, features, reference_image}}
        self._persona_file = None

        if self.project_dir:
            self._persona_file = self.project_dir / "personas.json"
            self._load()

    def _load(self):
        """Load character data from file"""
        if self._persona_file and self._persona_file.exists():
            try:
                with open(self._persona_file, "r", encoding="utf-8") as f:
                    self.personas = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load personas.json: {e}")
                self.personas = {}

    def _save(self):
        """Save character data to file"""
        if self._persona_file:
            self._persona_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persona_file, "w", encoding="utf-8") as f:
                json.dump(self.personas, f, indent=2, ensure_ascii=False)

    def register(
        self,
        name: str,
        gender: str,
        reference_image: Optional[str] = None,
        features: str = ""
    ) -> str:
        """
        Register character/persona

        Args:
            name: Character name
            gender: Gender (male/female)
            reference_image: Reference image path (can be None, added in Phase 2)
            features: Appearance feature description

        Returns:
            persona_id
        """
        # Generate unique ID
        persona_id = name.lower().replace(" ", "_")
        counter = 1
        original_id = persona_id
        while persona_id in self.personas:
            persona_id = f"{original_id}_{counter}"
            counter += 1

        self.personas[persona_id] = {
            "name": name,
            "gender": gender,
            "reference_image": reference_image,
            "features": features
        }

        self._save()
        if reference_image:
            logger.info(f"✅ Character registered: {name} (ID: {persona_id}, reference image: {reference_image})")
        else:
            logger.info(f"✅ Character registered: {name} (ID: {persona_id}, no reference image)")

        return persona_id

    def update_reference_image(self, persona_id: str, reference_image: str) -> bool:
        """
        Update character reference image (used in Phase 2)

        Args:
            persona_id: Character ID
            reference_image: New reference image path

        Returns:
            Whether successful
        """
        if persona_id not in self.personas:
            logger.warning(f"⚠️ Character not found: {persona_id}")
            return False

        self.personas[persona_id]["reference_image"] = reference_image
        self._save()
        logger.info(f"✅ Updated reference image for {persona_id}: {reference_image}")
        return True

    def has_reference_image(self, persona_id: str) -> bool:
        """Check if character has reference image"""
        persona = self.personas.get(persona_id)
        if persona:
            return bool(persona.get("reference_image"))
        return False

    def list_personas_without_reference(self) -> List[str]:
        """Return list of all character IDs without reference images"""
        return [
            pid for pid, data in self.personas.items()
            if not data.get("reference_image")
        ]

    def get_reference(self, persona_id: str) -> Optional[str]:
        """Get character reference image path"""
        persona = self.personas.get(persona_id)
        if persona:
            return persona.get("reference_image")
        return None

    def get_features(self, persona_id: str) -> str:
        """
        Get character feature description (for prompt)

        Returns:
            Feature description string
        """
        persona = self.personas.get(persona_id)
        if not persona:
            return ""

        parts = []

        # Gender
        gender = persona.get("gender", "")
        if gender == "female":
            parts.append("woman")
        elif gender == "male":
            parts.append("man")

        # Features
        features = persona.get("features", "")
        if features:
            parts.append(features)

        # Name as reference identifier
        name = persona.get("name", "")
        if name:
            return f"{', '.join(parts)} (reference: {name})"

        return ", ".join(parts)

    def get_persona_prompt(self, persona_id: str) -> str:
        """
        Get persona prompt for Veo 3

        Format: "Reference for {GENDER} ({name}): MUST preserve exact appearance - {features}"
        """
        persona = self.personas.get(persona_id)
        if not persona:
            return ""

        gender = persona.get("gender", "person")
        name = persona.get("name", "")
        features = persona.get("features", "")

        gender_upper = "WOMAN" if gender == "female" else "MAN" if gender == "male" else "PERSON"

        prompt = f"Reference for {gender_upper} ({name}): MUST preserve exact appearance"
        if features:
            prompt += f" - {features}"

        return prompt

    def list_personas(self) -> List[dict]:
        """List all characters"""
        return [
            {"id": pid, **pdata}
            for pid, pdata in self.personas.items()
        ]

    def export_for_storyboard(self) -> List[Dict[str, Any]]:
        """
        Export as storyboard.json compatible characters format

        Returns:
            List compatible with storyboard.json elements.characters format
        """
        characters = []
        for pid, pdata in self.personas.items():
            name = pdata.get("name", "")
            name_en = pid.replace("_", " ").title().replace(" ", "")

            ref_image = pdata.get("reference_image")
            reference_images = [ref_image] if ref_image else []

            characters.append({
                "name": name,
                "gender": pdata.get("gender", ""),
                "reference_image": ref_image,
                "features": pdata.get("features", "")
            })

        return characters

    def get_character_image_mapping(self) -> Dict[str, str]:
        """
        Generate character_image_mapping (for storyboard.json)

        Returns:
            {Element_Name: image_N, ...}
        """
        mapping = {}
        for i, (pid, pdata) in enumerate(self.personas.items()):
            name = pdata.get("name", "")
            name_en = pid.replace("_", " ").title().replace(" ", "")
            element_id = f"Element_{name_en}"
            mapping[element_id] = f"image_{i + 1}"
        return mapping

    def has_personas(self) -> bool:
        """Whether any characters are registered"""
        return len(self.personas) > 0

    def remove(self, persona_id: str) -> bool:
        """Delete character"""
        if persona_id in self.personas:
            del self.personas[persona_id]
            self._save()
            return True
        return False

    def clear(self):
        """Clear all characters"""
        self.personas = {}
        self._save()


# ============== CLI Entry Point ==============

async def cmd_video(args):
    """Video generation command (Veo 3.1 Fast)"""
    if not Config.COMPASS_API_KEY:
        print(json.dumps({"success": False, "error": "COMPASS_API_KEY not configured"}, indent=2, ensure_ascii=False))
        return 1

    # Check SDK
    try:
        from google import genai
    except ImportError:
        print(json.dumps({"success": False, "error": "Please install google-genai: pip install google-genai"}, indent=2, ensure_ascii=False))
        return 1

    # Read aspect_ratio from storyboard.json
    aspect_ratio = args.aspect_ratio
    if args.storyboard:
        aspect_ratio = get_aspect_from_storyboard(args.storyboard) or aspect_ratio

    # Duration processing
    duration = args.duration
    resolution = args.resolution

    # 1080p/4k must use 8 seconds
    if resolution in ["1080p", "4k"]:
        if duration is None:
            duration = 8
            logger.info(f"📐 Resolution {resolution} automatically using 8 second duration")
        elif duration != 8:
            logger.warning(f"⚠️ Resolution {resolution} requires 8 second duration, automatically adjusted ({duration} seconds -> 8 seconds)")
            duration = 8

    # 720p must specify duration (via --duration or storyboard.json)
    if duration is None:
        print(json.dumps({"success": False, "error": "Please specify duration via --duration, or design in storyboard.json"}, indent=2, ensure_ascii=False))
        return 1

    # Image size validation and processing
    image_path = args.image
    if image_path and os.path.exists(image_path):
        result = validate_and_resize_image(image_path)
        if result["success"] and result["resized"]:
            image_path = result["output_path"]

    # Process BGM constraint
    prompt = args.prompt
    if args.no_bgm:
        bgm_constraint = "No background music. Natural ambient sound only."
        if bgm_constraint.lower() not in prompt.lower():
            prompt = f"{prompt} {bgm_constraint}"

    client = Veo3Client()
    result = await client.create_video(
        prompt=prompt,
        duration=duration,
        aspect_ratio=aspect_ratio or "9:16",
        resolution=resolution,
        generate_audio=args.audio,
        image_path=image_path,
        output=args.output
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_image(args):
    """Image generation command (storyboard)"""
    if not Config.COMPASS_API_KEY:
        print(json.dumps({"success": False, "error": "COMPASS_API_KEY not configured"}, indent=2, ensure_ascii=False))
        return 1

    # Check SDK
    try:
        from google import genai
    except ImportError:
        print(json.dumps({"success": False, "error": "Please install google-genai: pip install google-genai"}, indent=2, ensure_ascii=False))
        return 1

    # Read aspect_ratio from storyboard.json
    aspect_ratio = args.aspect_ratio
    if args.storyboard:
        aspect_ratio = get_aspect_from_storyboard(args.storyboard) or aspect_ratio

    client = ImageClient()
    result = await client.generate(
        prompt=args.prompt,
        aspect_ratio=aspect_ratio or "9:16",
        reference_image=args.reference if args.reference else None,
        output=args.output
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_music(args):
    """Music generation command"""
    if not Config.SUNO_API_KEY:
        print(json.dumps({"success": False, "error": "SUNO_API_KEY not configured"}, indent=2, ensure_ascii=False))
        return 1

    # Read music config from creative.json
    prompt = args.prompt
    style = args.style
    if args.creative:
        config = get_music_config_from_creative(args.creative)
        if config:
            prompt = prompt or config.get("prompt")
            style = style or config.get("style")

    if not prompt or not style:
        print(json.dumps({"success": False, "error": "Please provide --prompt and --style, or use --creative to read from creative.json"}, indent=2, ensure_ascii=False))
        return 1

    client = SunoClient()
    result = await client.generate(prompt=prompt, style=style, instrumental=args.instrumental, output=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_tts(args):
    """TTS synthesis command"""
    if not Config.VOLCENGINE_TTS_APP_ID or not Config.VOLCENGINE_TTS_TOKEN:
        print(json.dumps({"success": False, "error": "Volcano Engine TTS credentials not configured"}, indent=2, ensure_ascii=False))
        return 1

    client = TTSClient()
    result = await client.synthesize(text=args.text, output=args.output, voice=args.voice, emotion=args.emotion, speed=args.speed)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_check(args):
    """Environment check command"""
    import shutil

    results = {"ready": True, "checks": {}, "api_keys": {}}

    # Python
    results["checks"]["python"] = {"version": sys.version, "ok": sys.version_info >= (3, 9)}

    # FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    results["checks"]["ffmpeg"] = {"installed": ffmpeg_path is not None}

    # google-genai SDK
    try:
        from google import genai
        results["checks"]["google-genai"] = {"installed": True}
    except ImportError:
        results["checks"]["google-genai"] = {"installed": False}
        results["ready"] = False

    # httpx
    try:
        import httpx
        results["checks"]["httpx"] = {"installed": True, "version": httpx.__version__}
    except ImportError:
        results["checks"]["httpx"] = {"installed": False}
        results["ready"] = False

    # API Keys
    results["api_keys"] = {
        "COMPASS_API_KEY": {"set": bool(Config.COMPASS_API_KEY), "purpose": "Veo 3 video generation"},
        "SUNO_API_KEY": {"set": bool(Config.SUNO_API_KEY), "purpose": "Suno music generation"},
        "VOLCENGINE_TTS": {"set": bool(Config.VOLCENGINE_TTS_APP_ID), "purpose": "Volcano Engine TTS"},
    }

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if results["ready"] else 1


def main():
    parser = argparse.ArgumentParser(description="Vico Tools Veo3 - Video Creation Tool (Veo 3.1 Fast)")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check")

    image_parser = subparsers.add_parser("image")
    image_parser.add_argument("--prompt", "-p", required=True, help="Image description (image_prompt)")
    image_parser.add_argument("--aspect-ratio", "-a", default="9:16", help="Aspect ratio")
    image_parser.add_argument("--reference", "-r", help="Reference image path (for character consistency)")
    image_parser.add_argument("--storyboard", "-s", help="storyboard.json path, automatically reads aspect_ratio")
    image_parser.add_argument("--output", "-o", help="Output file path")

    video_parser = subparsers.add_parser("video")
    video_parser.add_argument("--image", "-i", help="Input image path (image-to-video, as first frame)")
    video_parser.add_argument("--prompt", "-p", required=True, help="Video description")
    video_parser.add_argument("--duration", "-d", type=int, default=None, choices=[4, 6, 8], help="Duration (seconds): 4/6/8, auto-selected if not specified (1080p/4k auto uses 8 seconds)")
    video_parser.add_argument("--aspect-ratio", "-a", default="9:16", help="Aspect ratio")
    video_parser.add_argument("--resolution", "-r", default="720p", choices=["720p", "1080p", "4k"], help="Resolution (default 720p, 1080p/4k auto uses 8 second duration)")
    video_parser.add_argument("--storyboard", "-s", help="storyboard.json path, automatically reads aspect_ratio")
    video_parser.add_argument("--audio", action="store_true", default=True, help="Generate audio (default enabled)")
    video_parser.add_argument("--no-audio", action="store_false", dest="audio", help="Disable audio generation")
    video_parser.add_argument("--no-bgm", action="store_true", default=True, help="Add 'No background music' constraint to prompt (default enabled)")
    video_parser.add_argument("--output", "-o", help="Output file path")

    music_parser = subparsers.add_parser("music")
    music_parser.add_argument("--prompt", "-p", help="Music description (optional, can be omitted when using --creative)")
    music_parser.add_argument("--style", "-s", help="Music style (optional, can be omitted when using --creative)")
    music_parser.add_argument("--creative", "-c", help="creative.json path, automatically reads music config")
    music_parser.add_argument("--instrumental", action="store_true", default=True)
    music_parser.add_argument("--output", "-o")

    tts_parser = subparsers.add_parser("tts")
    tts_parser.add_argument("--text", "-t", required=True)
    tts_parser.add_argument("--output", "-o", required=True)
    tts_parser.add_argument("--voice", "-v", default="female_narrator")
    tts_parser.add_argument("--emotion", "-e", default=None, choices=["neutral", "happy", "sad", "gentle", "serious"])
    tts_parser.add_argument("--speed", type=float, default=1.0)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "check": cmd_check,
        "video": cmd_video,
        "image": cmd_image,
        "music": cmd_music,
        "tts": cmd_tts,
    }

    return asyncio.run(commands[args.command](args))


if __name__ == "__main__":
    sys.exit(main())