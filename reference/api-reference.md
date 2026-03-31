# API 工具参考（Veo 3）

**重要**：所有 `--prompt` 参数必须使用英文编写，以获得最佳生成效果。

## video_gen_tools.py - API 工具

```bash
# 环境检查
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check

# 文生视频
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A cat napping in the sunlight" \
  --duration 6 \
  --aspect-ratio 9:16 \
  --resolution 720p \
  --audio \
  --output output.mp4

# 图生视频（图片作为首帧）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image input.jpg \
  --prompt "The person in the image starts to smile" \
  --duration 8 \
  --aspect-ratio 9:16 \
  --resolution 1080p \
  --audio \
  --output output.mp4

# 从 storyboard.json 读取比例
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output output.mp4

# 图片生成（分镜图）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic start frame. A woman sitting by a coffee shop window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output image.png

# 音乐生成
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --prompt "Relaxing and pleasant background music" \
  --style "acoustic pop" \
  --output music.mp3

# 从 creative.json 读取音乐配置
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output music.mp3

# TTS 语音
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "要合成的文本" \
  --voice female_narrator \
  --output audio.mp3
```

---

## 参数说明

### video 子命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--prompt` / `-p` | 视频描述（必需） | - |
| `--image` / `-i` | 首帧图片路径（图生视频） | - |
| `--duration` / `-d` | 时长（秒），范围 3-60 | 5 |
| `--resolution` / `-r` | 分辨率：720p, 1080p, 4k | 1080p |
| `--aspect-ratio` / `-a` | 宽高比：9:16, 16:9, 1:1 | 9:16 |
| `--storyboard` / `-s` | storyboard.json 路径，自动读取 aspect_ratio | - |
| `--audio` | 生成音频 | True |
| `--output` / `-o` | 输出文件路径 | - |

### image 子命令

| 参数 | 说明 |
|------|------|
| `--prompt` / `-p` | 图片描述（必需） |
| `--aspect-ratio` / `-a` | 宽高比：9:16, 16:9, 1:1 |
| `--reference` / `-r` | 参考图路径（用于角色一致性） |
| `--output` / `-o` | 输出文件路径 |

### music 子命令

| 参数 | 说明 |
|------|------|
| `--prompt` / `-p` | 音乐描述 |
| `--style` / `-s` | 音乐风格 |
| `--creative` / `-c` | creative.json 路径 |
| `--instrumental` | 纯音乐（默认 True） |
| `--output` / `-o` | 输出文件路径 |

### tts 子命令

| 参数 | 说明 |
|------|------|
| `--text` / `-t` | 要合成的文本（必需） |
| `--voice` / `-v` | 音色：female_narrator, female_gentle, male_narrator, male_warm |
| `--emotion` / `-e` | 情感：neutral, happy, sad, gentle, serious |
| `--speed` | 语速（0.5-2.0） |
| `--output` / `-o` | 输出文件路径（必需） |

---

## video_gen_editor.py - 剪辑工具

```bash
# 拼接视频
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json

# 音频混合
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py mix \
  --video video.mp4 \
  --bgm music.mp3 \
  --output final.mp4

# 转场
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py transition \
  --inputs video1.mp4 video2.mp4 \
  --type fade \
  --output output.mp4

# 调色
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py color \
  --video video.mp4 \
  --preset cinematic \
  --output output.mp4
```

**转场类型**：fade | dissolve | wipeleft | wiperight | wipeup | wipedown | slideleft | slideright | slideup | slidedown | circleopen | circleclose

**调色预设**：warm | cool | vibrant | cinematic | desaturated | vintage

---

## 配置文件

API Key 配置在 `~/.claude/skills/video-gen-veo3/config.json`：

```json
{
  "COMPASS_API_KEY": "your-compass-api-key",
  "SUNO_API_KEY": "your-suno-api-key",
  "VOLCENGINE_TTS_APP_ID": "your-app-id",
  "VOLCENGINE_TTS_ACCESS_TOKEN": "your-token"
}
```

---

## 两阶段流程示例（虚构片）

```bash
# Step 1: 生成分镜图
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic realistic start frame. A 25-year-old Asian woman with long black hair, sitting by a coffee shop window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output generated/frames/scene1_shot1_frame.png

# Step 2: 分镜图作为首帧生成视频
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image generated/frames/scene1_shot1_frame.png \
  --prompt "The woman in the image slowly opens her eyes with a gentle smile. Keep 9:16 vertical composition." \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```