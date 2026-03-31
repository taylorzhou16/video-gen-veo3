# video-gen-veo3

AI 视频剪辑工具（Veo 3.1 Fast 版本）。

## 功能

- **视频生成**：使用 Veo 3.1 Fast API 生成视频（文生视频、图生视频）
- **自动音频**：原生支持环境音、音效、简单对话生成
- **分镜设计**：结构化分镜脚本生成
- **后期剪辑**：FFmpeg 拼接、转场、调色、配乐

## Veo 3.1 Fast 规格

| 参数 | 值 |
|------|-----|
| 时长 | 4秒 / 6秒 / 8秒 |
| 分辨率 | 720p / 1080p / 4k |
| 宽高比 | 16:9 / 9:16 |
| 音频 | 自动生成（环境音+台词） |

**约束**：1080p/4k 分辨率必须使用 8 秒时长。

## 安装

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.json`：

```json
{
  "COMPASS_API_KEY": "your-compass-api-key",
  "SUNO_API_KEY": "your-suno-api-key",
  "VOLCENGINE_TTS_APP_ID": "your-app-id",
  "VOLCENGINE_TTS_ACCESS_TOKEN": "your-token"
}
```

## 使用

```bash
# 环境检查
python video_gen_tools.py check

# 文生视频
python video_gen_tools.py video \
  --prompt "一只猫在阳光下打盹" \
  --duration 6 \
  --resolution 720p \
  --aspect-ratio 9:16 \
  --audio \
  --output output.mp4

# 图生视频
python video_gen_tools.py video \
  --image input.jpg \
  --prompt "图中的人物开始微笑" \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output output.mp4

# 图片生成（分镜图）
python video_gen_tools.py image \
  --prompt "Cinematic start frame. 一位女性坐在咖啡馆窗边，温暖光线，电影感，9:16画面比例" \
  --aspect-ratio 9:16 \
  --output image.png

# 音乐生成
python video_gen_tools.py music \
  --prompt "轻松愉悦的背景音乐" \
  --style "acoustic pop" \
  --output music.mp3

# TTS 语音
python video_gen_tools.py tts \
  --text "要合成的文本" \
  --voice female_narrator \
  --output audio.mp3

# 视频拼接
python video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json
```

## 文件结构

```
.
├── SKILL.md              # Claude Code Skill 定义
├── video_gen_tools.py    # API 工具（视频/图片/音乐/TTS生成）
├── video_gen_editor.py   # 剪辑工具（拼接/转场/调色）
├── config.json           # API 配置
├── requirements.txt      # Python 依赖
└── reference/
    ├── storyboard-spec.md  # 分镜设计规范
    ├── prompt-guide.md     # Prompt 编写规范
    └── api-reference.md    # API 参考文档
```

## 依赖

- Python 3.9+
- FFmpeg 6.0+
- google-genai
- httpx
- Pillow (可选，用于图片处理)

## License

MIT