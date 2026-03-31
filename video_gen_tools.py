#!/usr/bin/env python3
"""
Vico Tools Veo3 - 视频创作API命令行工具集（Veo 3.1 Fast 版本）

使用 Compass API (Google Gen AI SDK) 调用 Veo 3.1 Fast

用法：
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

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== 配置管理 ==============

CONFIG_FILE = Path.home() / ".claude" / "skills" / "video-gen-veo3" / "config.json"

# Compass API Base URL
COMPASS_BASE_URL = "https://compass.llm.shopee.io/compass-api/v1"


def load_config() -> Dict[str, str]:
    """从配置文件加载 API keys"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


class Config:
    """从配置文件和环境变量加载配置（配置文件优先）"""

    _cached_config = None

    @classmethod
    def _get_config(cls) -> Dict[str, str]:
        if cls._cached_config is None:
            cls._cached_config = load_config()
        return cls._cached_config

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """优先从配置文件获取，其次环境变量"""
        config = cls._get_config()
        return config.get(key, os.getenv(key, default))

    # Compass API (Veo 3)
    @property
    def COMPASS_API_KEY(self) -> str:
        return self.get("COMPASS_API_KEY", "")

    # Veo 3.1 Fast 配置
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


# ============== 图片尺寸验证与处理 ==============

def validate_and_resize_image(
    image_path: str,
    output_path: str = None,
    min_size: int = 720,
    max_size: int = 2048,
    target_size: int = 1280
) -> Dict[str, Any]:
    """
    验证并调整图片尺寸

    Args:
        image_path: 图片路径
        output_path: 输出路径（None 时自动生成）
        min_size: 最小边长限制（小于此值会放大）
        max_size: 最大边长限制（大于此值会缩小）
        target_size: 目标尺寸（放大时使用）

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
        logger.warning("⚠️ PIL 未安装，跳过图片尺寸检查")
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
            logger.info(f"📐 图片尺寸过小 {w}x{h}，需要放大到至少 {min_size}px")
        elif max_dim > max_size:
            scale = max_size / max_dim
            need_resize = True
            logger.info(f"📐 图片尺寸过大 {w}x{h}，需要缩小到最多 {max_size}px")

        if need_resize:
            new_w = int(w * scale)
            new_h = int(h * scale)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)

            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_resized{ext}"

            img_resized.save(output_path, quality=95)
            logger.info(f"📐 图片尺寸调整: {w}x{h} → {new_w}x{new_h}")

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
        logger.error(f"❌ 图片尺寸处理失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "output_path": image_path
        }


# ============== Storyboard / Creative 读取工具 ==============

def get_aspect_from_storyboard(storyboard_path: str) -> Optional[str]:
    """从 storyboard.json 读取 aspect_ratio"""
    try:
        with open(storyboard_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("aspect_ratio")
    except Exception:
        return None


def get_music_config_from_creative(creative_path: str) -> Optional[Dict[str, Any]]:
    """从 creative.json 读取音乐配置"""
    try:
        with open(creative_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            music = data.get("music", {})
            return {
                "need_bgm": music.get("need_bgm", True),
                "style": music.get("style"),
                "prompt": music.get("prompt")  # 可选的详细描述
            }
    except Exception:
        return None


# ============== Veo 3 视频生成（使用 Google Gen AI SDK）==============

class Veo3Client:
    """
    Veo 3.1 Fast 视频生成客户端（使用 Google Gen AI SDK）

    功能特点：
    - 文生视频 + 音频
    - 图生视频 + 音频（图片作为首帧）
    - 支持分辨率：720p, 1080p, 4k
    - 自动音频生成

    定价：
    - Video + Audio: $0.15/second (720p/1080p), $0.35/second (4k)
    - Video only: $0.10/second (720p/1080p), $0.30/second (4k)
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        """获取 Google Gen AI 客户端"""
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
                raise ImportError("请安装 google-genai: pip install google-genai")
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
        视频生成（文生视频或图生视频）

        Args:
            prompt: 视频描述
            duration: 时长（秒）- Veo 3.1 Fast 只支持 4, 6, 8 秒
            aspect_ratio: 宽高比 (16:9, 9:16)
            resolution: 分辨率 (720p, 1080p, 4k) - 1080p/4k 必须 duration=8
            generate_audio: 是否生成音频
            image_path: 图片路径（图生视频时使用，作为首帧）
            output: 输出文件路径
        """
        try:
            from google.genai.types import GenerateVideosConfig, Image
        except ImportError:
            return {"success": False, "error": "请安装 google-genai: pip install google-genai"}

        client = self._get_client()

        # 验证 duration 参数（Veo 3.1 Fast 只支持 4, 6, 8 秒）
        valid_durations = [4, 6, 8]
        if duration not in valid_durations:
            logger.warning(f"⚠️ Veo 3.1 Fast 只支持 4/6/8 秒，已自动调整为 8 秒")
            duration = 8

        # 1080p/4k 必须使用 8 秒时长
        if resolution in ["1080p", "4k"] and duration != 8:
            logger.warning(f"⚠️ {resolution} 分辨率必须使用 8 秒时长，已自动调整")
            duration = 8

        # 构建配置
        config = GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            duration_seconds=str(duration),
            resolution=resolution,
        )

        # 处理图片输入（图生视频）
        image_param = None
        if image_path:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"图片不存在: {image_path}"}

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
            logger.info(f"📤 创建 Veo 3 图生视频任务: {prompt[:50]}...")
        else:
            logger.info(f"📤 创建 Veo 3 文生视频任务: {prompt[:50]}...")

        try:
            # 调用 API
            kwargs = {
                "model": Config.VEO3_MODEL,
                "prompt": prompt,
                "config": config,
            }
            if image_param:
                kwargs["image"] = image_param

            operation = client.models.generate_videos(**kwargs)

            logger.info(f"✅ 任务已提交，等待完成...")

            # 等待完成
            video_url = await self._wait_for_operation(client, operation)

            if video_url and output:
                await self._download_file(video_url, output)
                return {"success": True, "video_url": video_url, "output": output}

            return {"success": bool(video_url), "video_url": video_url}

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"success": False, "error": "COMPASS_API_KEY 无效或未设置"}
            elif "402" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": "余额不足，请充值后重试"}
            elif "429" in error_msg or "rate" in error_msg.lower():
                return {"success": False, "error": "请求频率超限，请稍后重试"}
            logger.error(f"❌ Veo 3 视频生成失败: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_operation(self, client, operation, max_wait: int = 600) -> Optional[str]:
        """等待操作完成"""
        start_time = time.monotonic()

        try:
            from google.genai.types import Video
        except ImportError:
            return None

        logger.info(f"⏳ 等待 Veo 3 任务完成...")

        while not operation.done:
            elapsed = time.monotonic() - start_time
            if elapsed > max_wait:
                logger.error(f"❌ 任务超时 ({max_wait}秒)")
                return None

            logger.info(f"   [{int(elapsed)}s] 状态: processing...")
            await asyncio.sleep(15)
            operation = client.operations.get(operation)

        logger.info(f"   操作完成，解析结果...")

        # 检查是否有错误
        if operation.error:
            error_msg = operation.error.get('message', str(operation.error))
            logger.error(f"❌ 视频生成失败: {error_msg}")
            return {"success": False, "error": error_msg, "video_url": None}

        # 打印 operation 的原始信息
        logger.info(f"   operation.done: {operation.done}")

        # 尝试多种方式获取视频 URL
        video_uri = None

        # 方式1: 从 operation.result.generated_videos 获取
        try:
            if operation.result and operation.result.generated_videos:
                gen_video = operation.result.generated_videos[0]
                if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                    video_uri = gen_video.video.uri
                    logger.info(f"   从 result.generated_videos[0].video.uri 获取成功")
        except Exception as e:
            logger.debug(f"   方式1失败: {e}")

        # 方式2: 从 operation.response 获取
        if not video_uri and operation.response:
            try:
                if hasattr(operation.response, 'generated_videos'):
                    gen_video = operation.response.generated_videos[0]
                    if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                        video_uri = gen_video.video.uri
                        logger.info(f"   从 response.generated_videos[0].video.uri 获取成功")
            except Exception as e:
                logger.debug(f"   方式2失败: {e}")

        # 方式3: 直接从 operation 获取
        if not video_uri:
            try:
                if hasattr(operation, 'generated_videos'):
                    gen_video = operation.generated_videos[0]
                    if hasattr(gen_video, 'video') and hasattr(gen_video.video, 'uri'):
                        video_uri = gen_video.video.uri
                        logger.info(f"   从 operation.generated_videos[0].video.uri 获取成功")
            except Exception as e:
                logger.debug(f"   方式3失败: {e}")

        if video_uri:
            elapsed = time.monotonic() - start_time
            logger.info(f"✅ Veo 3 任务完成 (耗时: {int(elapsed)}秒)")
            return video_uri
        else:
            logger.error(f"❌ 无法解析视频 URL")
            # 打印 operation 对象的属性以便调试
            logger.debug(f"   operation 属性: {dir(operation)}")
            if operation.response:
                logger.debug(f"   response 属性: {dir(operation.response)}")
            return None

    async def _download_file(self, url: str, output_path: str):
        """下载文件"""
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ 已保存到: {output_path}")

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
        视频生成（带严格降级策略）

        降级顺序：
        1. 重试（最多 max_retries 次）
        2. 调整 prompt（简化/优化描述）
        3. 调整参考图（缩小尺寸/更换格式）
        4. 最后降级到文生视频（仅在无其他选择时）

        Args:
            prompt: 视频描述
            duration: 时长（秒）
            aspect_ratio: 宽高比
            resolution: 分辨率
            generate_audio: 是否生成音频
            image_path: 图片路径（图生视频时使用）
            output: 输出文件路径
            max_retries: 最大重试次数
        """
        original_prompt = prompt
        original_image = image_path

        # 记录降级状态
        fallback_state = {
            "stage": "initial",
            "retries": 0,
            "prompt_adjusted": False,
            "image_adjusted": False,
            "downgraded_to_t2v": False,
            "history": []
        }

        # Stage 1: 初始尝试 + 重试
        for retry in range(max_retries + 1):
            fallback_state["retries"] = retry
            fallback_state["stage"] = "retry" if retry > 0 else "initial"

            logger.info(f"📹 尝试生成视频 (第{retry + 1}次)...")

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

            # 记录失败
            error = result.get("error", "未知错误")
            fallback_state["history"].append({
                "stage": fallback_state["stage"],
                "success": False,
                "error": error,
                "prompt": prompt[:100]
            })

            # 检查是否是可重试的错误
            if "429" in error or "rate" in error.lower():
                logger.warning(f"⚠️ 频率限制，等待60秒后重试...")
                await asyncio.sleep(60)
                continue
            elif "timeout" in error.lower() or "网络" in error:
                logger.warning(f"⚠️ 网络/超时错误，等待30秒后重试...")
                await asyncio.sleep(30)
                continue
            elif "401" in error or "Unauthorized" in error:
                # 无法通过重试解决的错误，直接返回
                return {"success": False, "error": error, "fallback_state": fallback_state}
            elif "402" in error or "quota" in error.lower():
                return {"success": False, "error": error, "fallback_state": fallback_state}

        # Stage 2: 调整 prompt
        fallback_state["stage"] = "adjust_prompt"
        fallback_state["prompt_adjusted"] = True

        adjusted_prompt = self._adjust_prompt(prompt)
        logger.info(f"📝 调整 prompt 尝试: {adjusted_prompt[:50]}...")

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

        # Stage 3: 调整参考图（仅在图生视频时）
        if image_path:
            fallback_state["stage"] = "adjust_image"
            fallback_state["image_adjusted"] = True

            adjusted_image = await self._adjust_reference_image(image_path)
            if adjusted_image:
                logger.info(f"🖼️ 调整参考图尝试: {adjusted_image}")

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

        # Stage 4: 最后降级到文生视频（仅在无法使用图生视频时）
        # 注意：虚构片/短剧不允许降级到文生视频
        if not image_path:
            fallback_state["stage"] = "downgrade_t2v"
            fallback_state["downgraded_to_t2v"] = True

            logger.warning(f"⚠️ 最后降级：使用文生视频模式")
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

        # 图生视频最终失败，返回错误（不降级）
        return {
            "success": False,
            "error": "图生视频生成失败，已尝试所有降级策略",
            "fallback_state": fallback_state,
            "suggestion": "请检查参考图质量或更换prompt"
        }

    def _adjust_prompt(self, prompt: str) -> str:
        """
        调整 prompt 以提高成功率

        策略：
        1. 移除/改写版权、名人等敏感词汇
        2. 简化过于复杂的描述
        3. 保留核心要素
        """
        # 敏感词汇列表（版权、名人、品牌等可能导致生成失败的词汇）
        sensitive_patterns = [
            # 名人姓名（常见）
            "taylor swift", "elon musk", "donald trump", "biden", "obama",
            "michael jackson", "madonna", "beyonce", "kanye", "kim kardashian",
            "leonardo dicaprio", "brad pitt", "tom cruise", "jennifer lawrence",
            # 品牌/版权
            "disney", "marvel", "dc comics", "star wars", "harry potter",
            "nike", "adidas", "apple", "microsoft", "google", "facebook",
            "coca-cola", "pepsi", "mcdonalds", "starbucks",
            # 角色名
            "mickey mouse", "batman", "superman", "spider-man", "iron man",
            "hulk", "thor", "captain america", "wonder woman",
            # 其他敏感词
            "celebrity", "famous person", "well-known",
        ]

        adjusted = prompt.lower()
        replaced_words = []

        for pattern in sensitive_patterns:
            if pattern in adjusted:
                # 替换为通用描述
                adjusted = adjusted.replace(pattern, "person")
                replaced_words.append(pattern)

        if replaced_words:
            logger.info(f"📝 移除敏感词汇: {', '.join(replaced_words)}")

        # 简化策略：保留前200字符的核心描述
        if len(prompt) > 200:
            # 找到第一个完整句子
            simplified = prompt[:200]
            if '.' in simplified:
                last_period = simplified.rfind('.')
                simplified = simplified[:last_period + 1]
            logger.info(f"📝 Prompt 已简化: {len(prompt)} → {len(simplified)} 字符")
            return simplified

        return prompt.strip()

    async def _adjust_reference_image(self, image_path: str) -> Optional[str]:
        """
        调整参考图以提高成功率

        策略：
        1. 缩小尺寸到 1280px
        2. 转换格式为 JPEG
        """
        try:
            from PIL import Image
        except ImportError:
            logger.warning("⚠️ PIL 未安装，无法调整图片")
            return None

        try:
            img = Image.open(image_path)
            w, h = img.size

            # 缩小到目标尺寸
            target_size = 1280
            if max(w, h) > target_size:
                scale = target_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                logger.info(f"🖼️ 图片已缩小: {w}x{h} → {new_w}x{new_h}")

            # 转换为 RGB（移除 alpha 通道）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 保存为 JPEG
            base, _ = os.path.splitext(image_path)
            adjusted_path = f"{base}_adjusted.jpg"
            img.save(adjusted_path, quality=85)

            logger.info(f"🖼️ 图片已转换: {image_path} → {adjusted_path}")
            return adjusted_path

        except Exception as e:
            logger.error(f"❌ 图片调整失败: {e}")
            return None


# ============== 图片生成（分镜图）==============

class ImageClient:
    """
    图片生成客户端（用于生成分镜图）

    使用 Compass API 调用 Gemini Flash Image 模型生成图片，
    用于虚构片/短剧的两阶段流程：先生成分镜图，再用作视频首帧。

    降级策略：
    1. 默认使用 gemini-3.1-flash-image-preview
    2. 失败时用 gemini-2.5-flash-image 兜底
    """

    PRIMARY_MODEL = "gemini-3.1-flash-image-preview"
    FALLBACK_MODEL = "gemini-2.5-flash-image"

    def __init__(self):
        self._client = None

    def _get_client(self):
        """获取 Google Gen AI 客户端"""
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
                raise ImportError("请安装 google-genai: pip install google-genai")
        return self._client

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "9:16",
        reference_image: str = None,
        output: str = None
    ) -> Dict[str, Any]:
        """
        图片生成（用于分镜图）

        支持：
        - 文生图：仅提供 prompt
        - 图生图：提供 prompt + reference_image

        降级策略：
        1. 默认使用 PRIMARY_MODEL (gemini-3.1-flash-image-preview)
        2. 失败时用 FALLBACK_MODEL (gemini-2.5-flash-image) 兜底

        Args:
            prompt: 图片描述（image_prompt）
            aspect_ratio: 宽高比 (16:9, 9:16, 1:1)
            reference_image: 参考图路径（用于图生图/风格迁移）
            output: 输出文件路径
        """
        try:
            from google.genai.types import GenerateContentConfig, Modality, Part, ImageConfig
        except ImportError:
            return {"success": False, "error": "请安装 google-genai: pip install google-genai"}

        client = self._get_client()

        logger.info(f"🖼️ 创建图片生成任务: {prompt[:50]}...")

        # 构建 contents
        contents = []

        # 如果有参考图，添加图片（图生图）
        if reference_image and os.path.exists(reference_image):
            with open(reference_image, 'rb') as f:
                img_bytes = f.read()
            contents.append(Part.from_bytes(data=img_bytes, mime_type='image/png'))
            logger.info(f"  使用参考图: {reference_image}")

        # 添加文本 prompt
        contents.append(prompt)

        # 尝试使用主模型
        result = await self._generate_with_model(
            client, self.PRIMARY_MODEL, contents, aspect_ratio, output
        )

        if result.get("success"):
            result["model"] = self.PRIMARY_MODEL
            return result

        # 主模型失败，尝试降级模型
        error_msg = result.get("error", "")
        logger.warning(f"⚠️ 主模型 {self.PRIMARY_MODEL} 失败: {error_msg}")
        logger.info(f"🔄 尝试降级模型 {self.FALLBACK_MODEL}...")

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
        """使用指定模型生成图片"""
        from google.genai.types import GenerateContentConfig, Modality, ImageConfig

        try:
            logger.info(f"  使用模型: {model}")

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=GenerateContentConfig(
                    response_modalities=[Modality.TEXT, Modality.IMAGE],
                    image_config=ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )

            logger.info(f"⏳ 等待图片生成完成...")

            # 解析结果
            if response and response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        logger.info(f"  文本响应: {part.text[:100]}...")
                    elif part.inline_data:
                        # 保存图片
                        image_bytes = part.inline_data.data
                        if output:
                            Path(output).parent.mkdir(parents=True, exist_ok=True)
                            with open(output, 'wb') as f:
                                if isinstance(image_bytes, str):
                                    f.write(base64.b64decode(image_bytes))
                                else:
                                    f.write(image_bytes)
                            logger.info(f"✅ 图片已保存: {output}")
                        return {"success": True, "output": output}

            return {"success": False, "error": "图片生成失败，无法解析返回结果"}

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                return {"success": False, "error": "COMPASS_API_KEY 无效或未设置"}
            elif "402" in error_msg or "quota" in error_msg.lower():
                return {"success": False, "error": "余额不足，请充值后重试"}
            elif "429" in error_msg or "rate" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg:
                return {"success": False, "error": "请求频率超限或配额耗尽"}
            elif "503" in error_msg or "UNAVAILABLE" in error_msg:
                return {"success": False, "error": "服务暂时不可用"}
            logger.error(f"❌ 图片生成失败: {e}")
            return {"success": False, "error": str(e)}

    async def _download_file(self, url: str, output_path: str):
        """下载文件"""
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ 图片已保存: {output_path}")


# ============== Suno 音乐生成 ==============

class SunoClient:
    """Suno 音乐生成客户端"""

    def __init__(self):
        import httpx
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            headers={"Content-Type": "application/json"}
        )

    async def generate(self, prompt: str, style: str, instrumental: bool = True, output: str = None) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "style": style,
            "instrumental": instrumental,
        }

        logger.info(f"🎵 创建音乐生成任务: {prompt[:30]}...")

        try:
            response = await self.client.post(
                f"{Config.SUNO_API_URL}/generate",
                json=payload,
                headers={"Authorization": f"Bearer {Config.SUNO_API_KEY}"}
            )
            response.raise_for_status()
            result = response.json()

            task_id = result.get("task_id") or result.get("id")
            if task_id:
                audio_url = await self._wait_for_completion(task_id)
                if audio_url and output:
                    await self._download_file(audio_url, output)
                    return {"success": True, "audio_url": audio_url, "output": output}
                return {"success": True, "audio_url": audio_url}

            audio_url = result.get("audio_url") or result.get("url")
            if audio_url and output:
                await self._download_file(audio_url, output)
                return {"success": True, "audio_url": audio_url, "output": output}

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"❌ Suno 音乐生成失败: {e}")
            return {"success": False, "error": str(e)}

    async def _wait_for_completion(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        start_time = time.monotonic()

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > max_wait:
                return None

            try:
                response = await self.client.get(
                    f"{Config.SUNO_API_URL}/task/{task_id}",
                    headers={"Authorization": f"Bearer {Config.SUNO_API_KEY}"}
                )
                result = response.json()
                state = result.get("state") or result.get("status")

                if state in ["completed", "success"]:
                    return result.get("audio_url") or result.get("url")
                elif state in ["failed", "error"]:
                    return None

                await asyncio.sleep(5)
            except:
                await asyncio.sleep(5)

    async def _download_file(self, url: str, output_path: str):
        import httpx
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            with open(output_path, 'wb') as f:
                f.write(response.content)
        logger.info(f"✅ 音乐已保存: {output_path}")

    async def close(self):
        await self.client.aclose()


# ============== 火山引擎 TTS ==============

class TTSClient:
    """火山引擎 TTS 客户端"""

    VOICE_MAP = {
        "female_narrator": "BV001_stream_flow",
        "female_gentle": "BV700_stream_flow",
        "male_narrator": "BV002_stream_flow",
        "male_warm": "BV406_stream_flow",
    }

    async def synthesize(self, text: str, output: str, voice: str = "female_narrator", emotion: str = None, speed: float = 1.0) -> Dict[str, Any]:
        import httpx

        voice_id = self.VOICE_MAP.get(voice, "BV001_stream_flow")
        payload = {
            "app_id": Config.VOLCENGINE_TTS_APP_ID,
            "user_id": "vico_user",
            "content": [{"text": text, "type": "text"}],
            "audio_config": {
                "voice_type": voice_id,
                "speed_ratio": speed,
                "audio_type": "mp3"
            }
        }

        logger.info(f"🔊 TTS合成: {text[:30]}...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openspeech.bytedance.com/api/v1/tts",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer; {Config.VOLCENGINE_TTS_TOKEN}"
                    }
                )
                response.raise_for_status()

                Path(output).parent.mkdir(parents=True, exist_ok=True)
                with open(output, 'wb') as f:
                    f.write(response.content)

                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', output],
                    capture_output=True, text=True
                )
                duration_ms = int(float(result.stdout.strip()) * 1000) if result.stdout.strip() else 0

                logger.info(f"✅ TTS已保存: {output} ({duration_ms}ms)")
                return {"success": True, "output": output, "duration_ms": duration_ms}

        except Exception as e:
            logger.error(f"❌ TTS失败: {e}")
            return {"success": False, "error": str(e)}


# ============== 人物角色管理 ==============

class PersonaManager:
    """
    人物角色管理器

    用于管理项目中的人物参考图，确保跨镜头角色一致性。
    只有当视频涉及人物时才使用，纯风景/物品视频不需要。

    使用方式：
        manager = PersonaManager(project_dir)
        manager.register("小美", "female", "path/to/reference.jpg", "长发、圆脸、戴眼镜")
        ref_path = manager.get_reference("小美")
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
        """从文件加载人物数据"""
        if self._persona_file and self._persona_file.exists():
            try:
                with open(self._persona_file, "r", encoding="utf-8") as f:
                    self.personas = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ 加载 personas.json 失败: {e}")
                self.personas = {}

    def _save(self):
        """保存人物数据到文件"""
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
        注册人物角色

        Args:
            name: 人物名称
            gender: 性别 (male/female)
            reference_image: 参考图路径（可为 None，Phase 2 补充）
            features: 外貌特征描述

        Returns:
            persona_id
        """
        # 生成唯一ID
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
            logger.info(f"✅ 已注册人物: {name} (ID: {persona_id}, 参考图: {reference_image})")
        else:
            logger.info(f"✅ 已注册人物: {name} (ID: {persona_id}, 无参考图)")

        return persona_id

    def update_reference_image(self, persona_id: str, reference_image: str) -> bool:
        """
        更新人物参考图（Phase 2 使用）

        Args:
            persona_id: 人物ID
            reference_image: 新的参考图路径

        Returns:
            是否成功
        """
        if persona_id not in self.personas:
            logger.warning(f"⚠️ 人物不存在: {persona_id}")
            return False

        self.personas[persona_id]["reference_image"] = reference_image
        self._save()
        logger.info(f"✅ 已更新 {persona_id} 的参考图: {reference_image}")
        return True

    def has_reference_image(self, persona_id: str) -> bool:
        """检查人物是否有参考图"""
        persona = self.personas.get(persona_id)
        if persona:
            return bool(persona.get("reference_image"))
        return False

    def list_personas_without_reference(self) -> List[str]:
        """返回所有没有参考图的人物ID列表"""
        return [
            pid for pid, data in self.personas.items()
            if not data.get("reference_image")
        ]

    def get_reference(self, persona_id: str) -> Optional[str]:
        """获取人物参考图路径"""
        persona = self.personas.get(persona_id)
        if persona:
            return persona.get("reference_image")
        return None

    def get_features(self, persona_id: str) -> str:
        """
        获取人物特征描述（用于 prompt）

        Returns:
            特征描述字符串
        """
        persona = self.personas.get(persona_id)
        if not persona:
            return ""

        parts = []

        # 性别
        gender = persona.get("gender", "")
        if gender == "female":
            parts.append("woman")
        elif gender == "male":
            parts.append("man")

        # 特征
        features = persona.get("features", "")
        if features:
            parts.append(features)

        # 名字作为参考标识
        name = persona.get("name", "")
        if name:
            return f"{', '.join(parts)} (reference: {name})"

        return ", ".join(parts)

    def get_persona_prompt(self, persona_id: str) -> str:
        """
        获取用于 Veo 3 的人物 prompt

        格式: "Reference for {GENDER} ({name}): MUST preserve exact appearance - {features}"
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
        """列出所有人物"""
        return [
            {"id": pid, **pdata}
            for pid, pdata in self.personas.items()
        ]

    def export_for_storyboard(self) -> List[Dict[str, Any]]:
        """
        导出为 storyboard.json 兼容的 characters 格式

        Returns:
            符合 storyboard.json elements.characters 格式的列表
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
        生成 character_image_mapping（用于 storyboard.json）

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
        """是否有人物注册"""
        return len(self.personas) > 0

    def remove(self, persona_id: str) -> bool:
        """删除人物"""
        if persona_id in self.personas:
            del self.personas[persona_id]
            self._save()
            return True
        return False

    def clear(self):
        """清空所有人物"""
        self.personas = {}
        self._save()


# ============== 命令行入口 ==============

async def cmd_video(args):
    """视频生成命令（Veo 3.1 Fast）"""
    if not Config.COMPASS_API_KEY:
        print(json.dumps({"success": False, "error": "COMPASS_API_KEY 未配置"}, indent=2, ensure_ascii=False))
        return 1

    # 检查 SDK
    try:
        from google import genai
    except ImportError:
        print(json.dumps({"success": False, "error": "请安装 google-genai: pip install google-genai"}, indent=2, ensure_ascii=False))
        return 1

    # 从 storyboard.json 读取 aspect_ratio
    aspect_ratio = args.aspect_ratio
    if args.storyboard:
        aspect_ratio = get_aspect_from_storyboard(args.storyboard) or aspect_ratio

    # 时长处理
    duration = args.duration
    resolution = args.resolution

    # 1080p/4k 必须用 8 秒
    if resolution in ["1080p", "4k"]:
        if duration is None:
            duration = 8
            logger.info(f"📐 分辨率 {resolution} 自动使用 8秒时长")
        elif duration != 8:
            logger.warning(f"⚠️ 分辨率 {resolution} 必须使用 8秒时长，已自动调整 ({duration}秒 → 8秒)")
            duration = 8

    # 720p 必须指定时长（通过 --duration 或 storyboard.json）
    if duration is None:
        print(json.dumps({"success": False, "error": "请通过 --duration 指定时长，或在 storyboard.json 中设计"}, indent=2, ensure_ascii=False))
        return 1

    # 图片尺寸验证与处理
    image_path = args.image
    if image_path and os.path.exists(image_path):
        result = validate_and_resize_image(image_path)
        if result["success"] and result["resized"]:
            image_path = result["output_path"]

    client = Veo3Client()
    result = await client.create_video(
        prompt=args.prompt,
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
    """图片生成命令（分镜图）"""
    if not Config.COMPASS_API_KEY:
        print(json.dumps({"success": False, "error": "COMPASS_API_KEY 未配置"}, indent=2, ensure_ascii=False))
        return 1

    # 检查 SDK
    try:
        from google import genai
    except ImportError:
        print(json.dumps({"success": False, "error": "请安装 google-genai: pip install google-genai"}, indent=2, ensure_ascii=False))
        return 1

    # 从 storyboard.json 读取 aspect_ratio
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
    """音乐生成命令"""
    if not Config.SUNO_API_KEY:
        print(json.dumps({"success": False, "error": "SUNO_API_KEY 未配置"}, indent=2, ensure_ascii=False))
        return 1

    # 从 creative.json 读取音乐配置
    prompt = args.prompt
    style = args.style
    if args.creative:
        config = get_music_config_from_creative(args.creative)
        if config:
            prompt = prompt or config.get("prompt")
            style = style or config.get("style")

    if not prompt or not style:
        print(json.dumps({"success": False, "error": "请提供 --prompt 和 --style，或使用 --creative 从 creative.json 读取"}, indent=2, ensure_ascii=False))
        return 1

    client = SunoClient()
    result = await client.generate(prompt=prompt, style=style, instrumental=args.instrumental, output=args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_tts(args):
    """TTS合成命令"""
    if not Config.VOLCENGINE_TTS_APP_ID or not Config.VOLCENGINE_TTS_TOKEN:
        print(json.dumps({"success": False, "error": "火山引擎 TTS 凭证未配置"}, indent=2, ensure_ascii=False))
        return 1

    client = TTSClient()
    result = await client.synthesize(text=args.text, output=args.output, voice=args.voice, speed=args.speed)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


async def cmd_check(args):
    """环境检查命令"""
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
        "COMPASS_API_KEY": {"set": bool(Config.COMPASS_API_KEY), "purpose": "Veo 3 视频生成"},
        "SUNO_API_KEY": {"set": bool(Config.SUNO_API_KEY), "purpose": "Suno 音乐生成"},
        "VOLCENGINE_TTS": {"set": bool(Config.VOLCENGINE_TTS_APP_ID), "purpose": "火山引擎 TTS"},
    }

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if results["ready"] else 1


def main():
    parser = argparse.ArgumentParser(description="Vico Tools Veo3 - 视频创作工具（Veo 3.1 Fast）")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("check")

    image_parser = subparsers.add_parser("image")
    image_parser.add_argument("--prompt", "-p", required=True, help="图片描述（image_prompt）")
    image_parser.add_argument("--aspect-ratio", "-a", default="9:16", help="宽高比")
    image_parser.add_argument("--reference", "-r", help="参考图路径（用于角色一致性）")
    image_parser.add_argument("--storyboard", "-s", help="storyboard.json 路径，自动读取 aspect_ratio")
    image_parser.add_argument("--output", "-o", help="输出文件路径")

    video_parser = subparsers.add_parser("video")
    video_parser.add_argument("--image", "-i", help="输入图片路径（图生视频，作为首帧）")
    video_parser.add_argument("--prompt", "-p", required=True, help="视频描述")
    video_parser.add_argument("--duration", "-d", type=int, default=None, choices=[4, 6, 8], help="时长(秒): 4/6/8，不指定则自动选择（1080p/4k 自动用8秒）")
    video_parser.add_argument("--aspect-ratio", "-a", default="9:16", help="宽高比")
    video_parser.add_argument("--resolution", "-r", default="720p", choices=["720p", "1080p", "4k"], help="分辨率（默认720p，1080p/4k 自动使用8秒时长）")
    video_parser.add_argument("--storyboard", "-s", help="storyboard.json 路径，自动读取 aspect_ratio")
    video_parser.add_argument("--audio", action="store_true", default=True, help="生成音频（默认开启）")
    video_parser.add_argument("--output", "-o", help="输出文件路径")

    music_parser = subparsers.add_parser("music")
    music_parser.add_argument("--prompt", "-p", help="音乐描述（可选，使用 --creative 时可省略）")
    music_parser.add_argument("--style", "-s", help="音乐风格（可选，使用 --creative 时可省略）")
    music_parser.add_argument("--creative", "-c", help="creative.json 路径，自动读取音乐配置")
    music_parser.add_argument("--instrumental", action="store_true", default=True)
    music_parser.add_argument("--output", "-o")

    tts_parser = subparsers.add_parser("tts")
    tts_parser.add_argument("--text", "-t", required=True)
    tts_parser.add_argument("--output", "-o", required=True)
    tts_parser.add_argument("--voice", "-v", default="female_narrator")
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