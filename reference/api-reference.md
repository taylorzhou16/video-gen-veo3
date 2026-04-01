# API Tool Reference (Veo 3)

**Important**: All `--prompt` parameters must be written in English for best generation results.

## video_gen_tools.py - API Tools

```bash
# Environment check
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check

# Text-to-video
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A cat napping in the sunlight" \
  --duration 6 \
  --aspect-ratio 9:16 \
  --resolution 720p \
  --audio \
  --output output.mp4

# Image-to-video (image as first frame)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image input.jpg \
  --prompt "The person in the image starts to smile" \
  --duration 8 \
  --aspect-ratio 9:16 \
  --resolution 1080p \
  --audio \
  --output output.mp4

# Read aspect ratio from storyboard.json
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output output.mp4

# Image generation (storyboard image)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic start frame. A woman sitting by a coffee shop window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output image.png

# Music generation
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --prompt "Relaxing and pleasant background music" \
  --style "acoustic pop" \
  --output music.mp3

# Read music config from creative.json
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output music.mp3

# TTS voice synthesis
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "Text to synthesize" \
  --voice female_narrator \
  --output audio.mp3
```

---

## Parameter Reference

### video subcommand

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--prompt` / `-p` | Video description (required) | - |
| `--image` / `-i` | First frame image path (for image-to-video) | - |
| `--duration` / `-d` | Duration (seconds), range 3-60 | 5 |
| `--resolution` / `-r` | Resolution: 720p, 1080p, 4k | 1080p |
| `--aspect-ratio` / `-a` | Aspect ratio: 9:16, 16:9, 1:1 | 9:16 |
| `--storyboard` / `-s` | storyboard.json path, auto-reads aspect_ratio | - |
| `--audio` | Generate audio | True |
| `--output` / `-o` | Output file path | - |

### image subcommand

| Parameter | Description |
|-----------|-------------|
| `--prompt` / `-p` | Image description (required) |
| `--aspect-ratio` / `-a` | Aspect ratio: 9:16, 16:9, 1:1 |
| `--reference` / `-r` | Reference image path (for character consistency) |
| `--output` / `-o` | Output file path |

### music subcommand

| Parameter | Description |
|-----------|-------------|
| `--prompt` / `-p` | Music description |
| `--style` / `-s` | Music style |
| `--creative` / `-c` | creative.json path |
| `--instrumental` | Instrumental only (default True) |
| `--output` / `-o` | Output file path |

### tts subcommand

| Parameter | Description |
|-----------|-------------|
| `--text` / `-t` | Text to synthesize (required) |
| `--voice` / `-v` | Voice: female_narrator, female_gentle, male_narrator, male_warm |
| `--emotion` / `-e` | Emotion: neutral, happy, sad, gentle, serious |
| `--speed` | Speaking rate (0.5-2.0) |
| `--output` / `-o` | Output file path (required) |

---

## video_gen_editor.py - Editing Tools

```bash
# Video concatenation
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json

# Audio mixing
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py mix \
  --video video.mp4 \
  --bgm music.mp3 \
  --output final.mp4

# Transition
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py transition \
  --inputs video1.mp4 video2.mp4 \
  --type fade \
  --output output.mp4

# Color grading
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py color \
  --video video.mp4 \
  --preset cinematic \
  --output output.mp4
```

**Transition Types**: fade | dissolve | wipeleft | wiperight | wipeup | wipedown | slideleft | slideright | slideup | slidedown | circleopen | circleclose

**Color Grading Presets**: warm | cool | vibrant | cinematic | desaturated | vintage

---

## Configuration

API Key configuration in `~/.claude/skills/video-gen-veo3/config.json`:

```json
{
  "COMPASS_API_KEY": "your-compass-api-key",
  "SUNO_API_KEY": "your-suno-api-key",
  "VOLCENGINE_TTS_APP_ID": "your-app-id",
  "VOLCENGINE_TTS_ACCESS_TOKEN": "your-token"
}
```

---

## Two-stage Process Example (Fiction)

```bash
# Step 1: Generate storyboard image
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic realistic start frame. A 25-year-old Asian woman with long black hair, sitting by a coffee shop window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output generated/frames/scene1_shot1_frame.png

# Step 2: Use storyboard image as first frame for video generation
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image generated/frames/scene1_shot1_frame.png \
  --prompt "The woman in the image slowly opens her eyes with a gentle smile. Keep 9:16 vertical composition." \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```