# video-gen-veo3

AI Video Editing Tool (Veo 3.1 Fast version).

## Changelog

### v1.0.3 (2026-04-01)

**Full English Localization**
- Translated all code, comments, log messages, and documentation to English
- Updated language requirement: respond in the same language as the user
- No Chinese characters remain in the entire codebase

**Audio Mixing Optimization**
- Added `normalize=0` to FFmpeg `amix` filter to preserve original volume ratios
- Improved volume recommendations for different video types:
  - Video ambient/sync sound: 0.8
  - Narration/voiceover: 1.5-2.0
  - Background music (BGM): 0.1-0.15 (varies by video type)
- Prevents auto-normalization that previously reduced overall audio quality

**Documentation Updates**
- All reference documents now in English
- Added audio mixing guidelines to SKILL.md
- Updated API reference with clear parameter descriptions

### v1.0.2 (2026-03-31)

**Narration Planning Feature**
- Phase 2: Added narration judgment logic, decides whether narration is needed based on video type (documentary/vlog/commercial, etc.)
- Phase 3: Synchronously design `narration_segments` (timing + copy) when generating storyboard
- Phase 4: Added narration generation step (call TTS per segment after video/music generation)
- Phase 5: Added narration insertion step (insert at correct position based on `overall_time_range`)

**TTS Enhancement**
- Added `--emotion` parameter, supports neutral/happy/sad/gentle/serious five emotions
- Supports automatic mapping from voice_style to TTS parameters (e.g. "gentle female voice" → female_gentle + gentle)

**Suno API Update**
- Upgraded to V3_5 model
- Updated polling interface and response data structure

### v1.0.1 (2026-03-31)

**Image Generation Model Upgrade**
- Changed image generation model to `gemini-3.1-flash-image-preview` (previously `imagen-3.0-generate-002`)
- Supports both text-to-image and image-to-image modes
- Added model fallback strategy: main model `gemini-3.1-flash-image-preview` falls back to `gemini-2.5-flash-image` on failure

**Video Generation Fallback Strategy**
- Added strict fallback order, no arbitrary fallback from image-to-video to text-to-video
- Stage 1: Retry (max 2 times)
- Stage 2: Adjust Prompt (remove sensitive words like copyright, celebrity names)
- Stage 3: Adjust Reference Image (resize, convert format)
- Stage 4: Only fallback to text-to-video when no reference image (fiction/short drama not allowed to fallback)

**Sensitive Word Handling**
- Added filtering for celebrity, brand, copyrighted character sensitive words
- Automatically replace with generic descriptions to improve generation success rate

## Features

- **Video Generation**: Use Veo 3.1 Fast API to generate videos (text-to-video, image-to-video)
- **Automatic Audio**: Native support for ambient sounds, sound effects, simple dialogue generation
- **Storyboard Design**: Structured storyboard script generation
- **Post-production Editing**: FFmpeg concatenation, transitions, color grading, music

## Veo 3.1 Fast Specifications

| Parameter | Value |
|-----------|-------|
| Duration | 4s / 6s / 8s |
| Resolution | 720p / 1080p / 4k |
| Aspect Ratio | 16:9 / 9:16 |
| Audio | Auto-generated (ambient + dialogue) |

**Constraint**: 1080p/4k resolution must use 8 second duration.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json`:

```json
{
  "COMPASS_API_KEY": "your-compass-api-key",
  "SUNO_API_KEY": "your-suno-api-key",
  "VOLCENGINE_TTS_APP_ID": "your-app-id",
  "VOLCENGINE_TTS_ACCESS_TOKEN": "your-token"
}
```

## Usage

```bash
# Environment check
python video_gen_tools.py check

# Text-to-video
python video_gen_tools.py video \
  --prompt "A cat napping in the sunlight" \
  --duration 6 \
  --resolution 720p \
  --aspect-ratio 9:16 \
  --audio \
  --output output.mp4

# Image-to-video
python video_gen_tools.py video \
  --image input.jpg \
  --prompt "The person in the image starts to smile" \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output output.mp4

# Image generation (storyboard image)
python video_gen_tools.py image \
  --prompt "Cinematic start frame. A woman sitting by a coffee shop window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output image.png

# Music generation
python video_gen_tools.py music \
  --prompt "Relaxing and pleasant background music" \
  --style "acoustic pop" \
  --output music.mp3

# TTS voice synthesis
python video_gen_tools.py tts \
  --text "Text to synthesize" \
  --voice female_narrator \
  --emotion gentle \
  --output audio.mp3

# Video concatenation
python video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json
```

## File Structure

```
.
├── SKILL.md              # Claude Code Skill definition
├── video_gen_tools.py    # API tools (video/image/music/TTS generation)
├── video_gen_editor.py   # Editing tools (concatenation/transition/color grading)
├── config.json           # API configuration
├── requirements.txt      # Python dependencies
└── reference/
    ├── storyboard-spec.md  # Storyboard design specifications
    ├── prompt-guide.md     # Prompt writing guidelines
    └── api-reference.md    # API reference documentation
```

## Dependencies

- Python 3.9+
- FFmpeg 6.0+
- google-genai
- httpx
- Pillow (optional, for image processing)

## License

MIT