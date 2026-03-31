---
name: video-gen-veo3
description: AI视频剪辑工具（Veo 3.1 Fast 版本）。分析素材、生成创意、设计分镜、执行剪辑。使用 Veo 3.1 Fast 进行视频生成（支持文生视频、图生视频）。当用户要求使用 Veo 3、Veo 3.1 Fast、Compass API 制作视频时触发。
argument-hint: <素材目录或视频文件>
---

# Vico-Edit Veo3 使用指南

**角色**：Director Agent — 理解创作意图、协调所有资源、交付视频作品。

**语言要求**：所有回复必须使用中文。

---

## 推荐配置

**必须使用多模态模型**（如 Claude Opus/Sonnet/Kimi-K2.5）以获得最佳体验。模型本身具备视觉理解能力，可直接通过 Read 工具分析图片。

---

## 核心理念

- **工具文件**：video_gen_tools.py（API 调用）和 video_gen_editor.py（FFmpeg 剪辑）是命令行工具
- **灵活规划，稳健执行**：规划阶段产出结构化制品，执行阶段由分镜方案驱动
- **优雅降级**：遇到问题时主动寻求用户帮助，而不是卡住流程

### Veo 3.1 Fast 能力概览

| 功能 | 输入 | 输出 | 分辨率 |
|------|------|------|--------|
| 文生视频 + 音频 | Text prompt | Video + Audio | 720p, 1080p, 4k |
| 图生视频 + 音频 | Image + Text prompt | Video + Audio | 720p, 1080p, 4k |
| 文生视频（无音频） | Text prompt | Video | 720p, 1080p, 4k |
| 图生视频（无音频） | Image + Text prompt | Video | 720p, 1080p, 4k |

**核心特点**：
- **自动音频生成**：原生音效、环境音、简单对话
- **图生视频**：图片作为首帧
- **高分辨率**：最高 4k 输出
- **时长限制**：4/6/8 秒（1080p/4k 必须用 8秒）

**与 Kling/Vidu 对比**：

| 功能 | Veo 3.1 Fast | Kling-3.0 | Vidu Q3 Pro |
|------|-------------|-----------|-------------|
| 文生视频 | ✅ | ✅ | ✅ |
| 图生视频（首帧图） | ✅ | ✅ | ✅ |
| 自动音频 | ✅ 原生支持 | ✅ | ✅ |
| 多镜头模式 (multi_shot) | ❌ | ✅ | ❌ |
| 最大时长 | 8秒 | 10秒 | 8秒 |
| 最高分辨率 | 4k | 1080p | 720p |

---

## 快速启动流程

```
环境检查 → 素材收集 → 创意确认 → 分镜设计 → 执行生成 → 剪辑输出
   5秒        交互       交互        交互        自动        自动
```

### 工作流进度清单

```
Task Progress:
- [ ] Phase 0: 环境检查（python video_gen_tools.py check）
- [ ] Phase 1: 素材收集（扫描 + 视觉分析 + 人物识别）
- [ ] Phase 2: 创意确认（问题卡片交互 + 角色参考图收集）
- [ ] Phase 3: 分镜设计（生成 storyboard.json + 自动生成模式选择 + 用户确认）
- [ ] Phase 4: 执行生成（Veo 3 API 调用 + 进度跟踪）
- [ ] Phase 5: 剪辑输出（拼接 + 转场 + 调色 + 配乐）
```

---

## Phase 0: 环境检查

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check
```

- 基础依赖（FFmpeg/Python/httpx）不通过 → 停止并告知安装方法
- API key 未配置 → 记录状态，后续按需询问

---

## Phase 1: 素材收集

### 素材来源识别

- **目录路径** → 扫描目录或用户发送的图片/视频文件
- **视频文件** → 直接分析该视频
- **无素材** → 纯创意模式

### 视觉分析流程

使用 Read 工具读取图片。记录场景描述、主体内容、情感基调、颜色风格。

如果无法分析图片，主动询问用户描述每张素材内容。

### 人物识别（条件性）

**仅当用户提供了人物肖像图时触发**（不确定时询问用户）。

执行步骤：
1. 读取图片内容，识别所有人物
2. 询问用户确认每个人物的身份
3. 使用 PersonaManager 分别注册：

```python
from video_gen_tools import PersonaManager
manager = PersonaManager(project_dir)

# 情况A：用户提供了参考图
manager.register("小美", "female", "path/to/ref.jpg", "长发、瓜子脸")

# 情况B：用户未提供参考图（Phase 2 会补充）
manager.register("主角", "male", None, "短发、运动风格")
```

**Phase 1 关键原则**：
- 只处理用户**已上传**的参考图
- 未上传的角色 reference_image 设为 `None`，由 Phase 2 补充
- 不要在此阶段询问未上传的参考图

### Phase 1 产出

创建项目目录 `~/video-gen-projects/{project_name}_{timestamp}/`，产出：
- `state.json` — 项目状态
- `analysis/analysis.json` — 素材分析结果
- `personas.json` — 人物注册表（reference_image 可能为 None）

**personas.json 结构**：
```json
{
  "personas": [
    {
      "name": "小美",
      "gender": "female",
      "reference_image": "/path/to/ref.jpg",
      "features": "长发、瓜子脸"
    },
    {
      "name": "主角",
      "gender": "male",
      "reference_image": null,
      "features": "短发、运动风格"
    }
  ]
}
```

---

## Phase 2: 创意确认

**使用问题卡片与用户交互**，收集关键信息。

### 问题卡片设计

**问题 1: 视频风格**
- 选项：电影感 | Vlog风格 | 广告片 | 纪录片 | 艺术/实验
- 说明：决定调色、转场、配乐的整体基调

**问题 2: 目标时长**
- 选项：15秒（短视频）| 30秒（标准）| 60秒（长视频）| 自定义
- 说明：影响分镜数量和节奏

**问题 3: 画面比例**
- 选项：9:16（抖音/小红书）| 16:9（B站/YouTube）
- 说明：根据发布平台选择

**问题 4: 分辨率与单镜头时长**
- 选项：
  - 720p（默认）+ 4秒/6秒/8秒
  - 1080p + 8秒（高质量）
  - 4k + 8秒（最高质量）
- 说明：**1080p/4k 必须用 8 秒时长**，720p 可选 4/6/8 秒

**问题 5: 音频（同期声）**
- 选项：自动生成（Veo 3 自动生成环境音/台词）| 不需要音频
- 说明：Veo 3 自动生成环境音、音效、简单对话（同期声）

**问题 6: 旁白/解说**

**先判断视频类型是否适合加旁白**：

| 视频风格 | 旁白需求 | 说明 |
|---------|---------|------|
| 电影感/虚构片 | 通常不需要 | 角色台词为主，旁白会破坏沉浸感 |
| 纪录片 | 通常需要 | 场景解说、背景介绍 |
| Vlog风格 | 可能需要 | 旅行解说、心情记录 |
| 广告片 | 可能需要 | 产品介绍、品牌故事 |
| 艺术/实验 | 视情况 | 概念表达可能需要旁白 |

**拿不准时询问用户**：

> 这条视频是否需要旁白/解说？
> - **不需要旁白**（角色台词为主，或纯视觉表达）
> - **需要AI生成旁白**（我来根据分镜设计文案）
> - **我已有旁白文案**（用户提供完整文案）

**区分两种音频生成方式**：

**A. 角色台词（同期声）**
- 由 Veo 3 视频生成模型直接生成
- 需要在分镜的 video_prompt 中明确描述：角色、台词、情绪、语速、声音特质
- 视频生成时设置 `audio: true`

**B. 旁白/解说（后期配音）**
- 由 TTS 后期生成，在剪辑阶段合入
- 用于场景解说、背景介绍、情感烘托
- Phase 3 会根据分镜设计旁白文案和时间点

**重要原则**：能收同期声的镜头，都不要用后期 TTS 配音！

**问题 7: 配乐需求**
- 选项：AI生成BGM | 不需要配乐 | 我已有音乐
- 说明：BGM 由 Suno 生成或用户提供，后期合成

**问题 8: 角色参考图收集**

**触发条件**：检查 personas.json，存在 `reference_image` 为 null/空 的角色时触发。

**询问内容**（每个无参考图的角色）：

> **角色「{name}」需要参考图**
>
> 请选择参考图来源：
> - **A. AI生成角色形象**（推荐，自动生成标准参考图）
> - **B. 上传参考图**（用户提供人物照片）
> - **C. 接受纯文字生成**（角色外貌可能在不同镜头中不一致）

### Phase 2 产出

- `creative/creative.json` — 创意方案
- 更新 `personas.json` — 补充 reference_images（如有）
- `creative/decision_log.json` — 决策记录

**creative.json narration 字段结构**：

```json
{
  "narration": {
    "type": "ai_generated",           // none / ai_generated / user_provided
    "voice_style": "温柔女声",        // 旁白风格（ai_generated 时由用户指定）
    "user_text": "用户提供的完整旁白文案"  // user_provided 时必填
  }
}
```

| type | 说明 | Phase 3 处理 |
|------|------|-------------|
| `none` | 不需要旁白 | 不规划 narration_segments |
| `ai_generated` | AI 设计文案 | 根据分镜自动撰写旁白，按镜头分段 |
| `user_provided` | 用户已有文案 | 将 user_text 按镜头时间点分段 |

---

## Phase 3: 分镜设计

### 分镜生成前强制阅读

**在生成分镜脚本前，必须阅读以下两个文档**：

```
Read: reference/storyboard-spec.md   # 分镜规范、JSON格式
Read: reference/prompt-guide.md       # Prompt编写规范
```

### Step 1: 同步角色信息到 Storyboard

**从 personas.json 同步到 storyboard.json**：

```python
from video_gen_tools import PersonaManager

manager = PersonaManager(project_dir)

# 生成 storyboard.json 的 elements.characters
characters = manager.export_for_storyboard()

# 写入 storyboard.json
storyboard["elements"] = {"characters": characters}
```

### Step 2: 自动生成模式选择

**根据项目类型自动选择生成模式**（无需人工决策）：

#### 项目类型判断（Phase 1 自动识别）

| 用户意图关键词 | 项目类型 |
|---------------|---------|
| "短剧"、"剧情"、"故事" | 虚构片/短剧 |
| "vlog"、"旅行记录"、"生活记录" | Vlog/写实类 |
| "广告"、"宣传片"、"产品展示" | 广告片/宣传片 |
| "MV"、"音乐视频" | MV短片 |

#### 决策树

**虚构片/短剧、MV短片**：
```
虚构内容 → 所有镜头强制先生成分镜图
           └── img2video（图生视频）
               └── --image: 分镜图首帧
```

**Vlog/写实类、广告片/宣传片（有真实素材）**：
```
真实素材 → 需要首帧控制
           └── img2video（图生视频）
               └── --image: 用户素材首帧
```

**广告片/宣传片（无真实素材）**：
```
无素材 → 强制先生成分镜图
         └── img2video（图生视频）
             └── --image: 分镜图首帧
```

#### 选择规则表

| 项目类型 | 素材情况 | 生成模式 | 说明 |
|---------|---------|---------|------|
| 虚构片/短剧 | 有/无角色参考图 | **img2video** | 强制分镜图，角色一致性通过首帧控制 |
| MV短片 | 有/无角色参考图 | **img2video** | 强制分镜图，音乐驱动 |
| Vlog/写实类 | 用户真实素材 | **img2video** | 用户素材首帧控制 |
| 广告片/宣传片 | 有真实素材 | **img2video** | 产品/企业素材首帧 |
| 广告片/宣传片 | 无真实素材 | **img2video** | 强制分镜图 |
| 无明确类型 | 无素材 | **text2video** | 纯文生视频 |

**核心原则**：
1. **虚构片强制生成分镜图**，然后走 img2video
2. **同一项目使用同一模式**，不混用

### Step 3: 生成分镜

**核心结构**：Storyboard 采用 `scenes[] → shots[]` 两层结构。

**关键设计原则**：
1. 总时长 = 目标时长（±5秒）
2. 单一动作原则：同一分镜内最多 1 个动作
3. 空间不变原则：禁止在 shot 内发生空间环境变化
4. 描述具体原则：禁止抽象动作描述，用具体动作替代
5. 所有 video_prompt 必须包含比例信息
6. 台词必须融入 video_prompt（角色 + 内容 + 情绪 + 声音）

**时长限制（Veo 3.1 Fast）**：

| 镜头类型 | 建议时长 | 说明 |
|---------|---------|------|
| 普通镜头 | 4-6秒 | 对话、日常动作、中景镜头 |
| 复杂运动 | 4-8秒 | 快速运动、动作戏、推拉镜头 |
| 静态情绪 | 6-8秒 | 特写、情绪表达、缓推镜头 |

**时长设计原则**：
- **时长由 storyboard 阶段设计**，CLI 不设默认值
- 720p 可用 4/6/8 秒
- 1080p/4k **必须用 8秒**（自动调整）

**分辨率约束**：
- 720p（默认）：可用 4/6/8 秒
- 1080p/4k：必须用 8 秒

**完整分镜规范**：See [reference/storyboard-spec.md](reference/storyboard-spec.md)
**Prompt 编写规范**：See [reference/prompt-guide.md](reference/prompt-guide.md)

**生成分镜时同步处理旁白**：

若 `creative.narration.type` 不为 `none`，则在生成分镜的同时规划旁白分段：

1. **读取 narration 信息**：
   - `voice_style` → 写入 `narration_config.voice_style`
   - `user_text`（如有）→ 按镜头时间点分段

2. **根据镜头内容设计旁白文案**：
   - 每段旁白对应一个镜头或一组连续镜头
   - 每段控制在 2-5 秒可说完的长度（约 30-50 字）
   - 避开有角色台词的镜头（不要与同期声冲突）

3. **规划时间点并写入 storyboard.json**：

```json
{
  "narration_config": {
    "voice_style": "温柔女声"
  },
  "narration_segments": [
    {"segment_id": "narr_1", "overall_time_range": "0-3s", "text": "这是一个宁静的下午..."},
    {"segment_id": "narr_2", "overall_time_range": "8-11s", "text": "她坐在窗边..."}
  ]
}
```

### Step 4: 展示给用户确认（强制步骤）

**必须在用户明确确认后才能进入 Phase 4！**

展示每个镜头的：
- 场景信息
- 生成模式（text2video/img2video）
- video_prompt
- image_prompt（如有）
- frame_path（如有）
- 台词
- 时长
- 转场

提供选项：确认并执行 / 修改分镜 / 调整旁白 / 调整时长 / 更换转场 / 取消

### Phase 3 产出

- `storyboard/storyboard.json` — 分镜脚本（包含 generation_mode、frame_path、narration_segments）

---

## Phase 4: 执行生成

根据 storyboard.json 执行视频生成。

### 执行前检查

**1. 参考图尺寸检查**
- 从 storyboard.json 读取每个镜头的 `frame_path` 或 `reference_images`
- 检测所有图片尺寸
- 最小边 < 720px → 自动放大到 1280px
- 最大边 > 2048px → 自动缩小到 2048px

**2. 参数校验**
- 从 storyboard.json 读取 `aspect_ratio` 字段
- 根据 `audio` 配置设置 `--audio` 参数

### 执行规则

1. **首次 API 调用单独执行**，确认成功后再并发
2. **并发不超过 3 个** API 生成调用
3. **实时更新 state.json** 记录进度
4. **失败时重试** 最多 2 次，然后询问用户

### Veo 3 生成模式

**重要**：所有 `--prompt` 必须使用英文编写，以获得最佳效果。

**文生视频（纯创意，无素材）**：
```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --duration 6 \
  --resolution 720p \
  --aspect-ratio {aspect_ratio} \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

**图生视频（有首帧素材/分镜图）**：
```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image <图片路径> \
  --prompt "The person in the image starts to smile gently" \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio {aspect_ratio} \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

### API 错误处理与降级策略

**严格降级顺序**（不允许随意降级到文生视频）：

| 降级阶段 | 操作 | 说明 |
|---------|------|------|
| **Stage 1: 重试** | 重试最多 2 次 | 处理频率限制、网络超时等临时错误 |
| **Stage 2: 调整 Prompt** | 简化描述、移除问题词汇 | 移除 "extreme", "blur" 等可能导致失败的词汇 |
| **Stage 3: 调整参考图** | 缩小尺寸到 1280px、转换 JPEG | 仅图生视频时使用 |
| **Stage 4: 降级到文生视频** | 仅在无参考图时使用 | **虚构片/短剧不允许降级** |

**降级规则**：
1. **虚构片/短剧、MV短片**：强制 img2video，不允许降级到 text2video
2. **Vlog/写实类、广告片**：如有素材，优先使用 img2video
3. **无素材情况**：才可使用 text2video

**错误类型处理**：

| 错误类型 | 处理方式 |
|---------|---------|
| **401 无效 Key** | 告知用户检查 COMPASS_API_KEY，不重试 |
| **402 余额不足** | 告知用户充值，不重试 |
| **429 频率限制** | 等待 60s 后重试 |
| **网络超时** | 等待 30s 后重试 |
| **生成失败** | 按降级顺序处理 |

### 音乐生成（可选）

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output generated/music/bgm.mp3
```

### 旁白生成（条件触发）

**触发条件**：读取 `storyboard.json` 的 `narration_segments`，若存在则触发。

**生成流程**：

1. **读取 narration_config 和 narration_segments**
2. **按分段逐个调用 TTS**：

```bash
# 每段旁白单独生成
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "这是一个宁静的下午..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3

python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "她坐在窗边..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_2.mp3
```

3. **输出文件命名**：按 `segment_id` 命名（`narr_1.mp3`, `narr_2.mp3`...）

**执行顺序**：
```
视频片段生成 → 音乐生成 → 旁白生成（如有）→ 进入 Phase 5 剪辑
```

### Phase 4 产出

- `generated/videos/*.mp4` — 生成的视频片段
- `generated/frames/*.png` — 生成的分镜图（如有）
- `generated/music/*.mp3` — 生成的背景音乐（如有）
- `generated/narration/*.mp3` — 生成的旁白音频（如有）
- 更新 `state.json` — 记录生成进度

---

## Phase 5: 剪辑输出

### 视频拼接

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json
```

### 音频保护

视频片段可能包含同期声、音效，拼接时不能丢失。无声片段会自动补静音轨，确保音画同步。

### 视频参数校验

拼接前自动检查分辨率/编码/帧率，不一致时自动归一化（1080x1920 / H.264 / 24fps）。

### 合成流程

1. **拼接** → 按分镜顺序连接（自动归一化）
2. **插入旁白** → 按 `narration_segments` 的 `overall_time_range` 将旁白音频配到正确位置（如有）
3. **转场** → 添加镜头间转场效果
4. **调色** → 应用整体调色风格
5. **配乐** → 混合背景音乐
6. **输出** → 生成最终视频

### 旁白插入（条件触发）

**触发条件**：读取 `storyboard.json` 的 `narration_segments`，若存在则触发。

**插入方式**：使用 FFmpeg 在指定时间点插入旁白音频。

```bash
# 按 overall_time_range 插入旁白
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py narration \
  --video concat_output.mp4 \
  --storyboard storyboard/storyboard.json \
  --narration-dir generated/narration \
  --output with_narration.mp4
```

**时间点计算**：
- `overall_time_range` 格式：`"0-3s"` 表示从 0 秒开始，持续到 3 秒
- 旁白音频在 `overall_time_range` 的起始时间点插入
- 多段旁白按时间顺序依次叠加

### Phase 5 产出

- `output/final.mp4` — 最终视频

---

## 工具调用速查

**重要**：所有 `--prompt` 必须使用英文编写。

```bash
# 环境检查
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check

# 文生视频（从 storyboard.json 读取 aspect_ratio）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --duration 6 \
  --resolution 720p \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output <输出>

# 图生视频
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image <图片路径> \
  --prompt "The person in the image starts to smile gently" \
  --duration 8 \
  --resolution 1080p \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output <输出>

# 图片生成（分镜图，从 storyboard.json 读取 aspect_ratio）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic start frame. A woman sitting by a window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --storyboard storyboard/storyboard.json \
  --output <输出>

# 音乐（传 --creative 从 creative.json 读取）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output <输出>

# 旁白（按 narration_segments 分段调用）
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text <分段文案> \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3

# 剪辑（传 --storyboard）
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs <视频列表> \
  --output <输出> \
  --storyboard storyboard/storyboard.json

# 旁白插入（按 overall_time_range 插入）
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py narration \
  --video <视频> \
  --storyboard storyboard/storyboard.json \
  --narration-dir generated/narration \
  --output <输出>
```

---

## 文件结构

```
~/video-gen-projects/{project_name}_{timestamp}/
├── state.json           # 项目状态
├── materials/           # 原始素材
│   └── personas/        # 角色参考图（Phase 2 生成）
├── analysis/
│   └── analysis.json    # 素材分析
├── creative/
│   ├── creative.json    # 创意方案
│   └── decision_log.json # 决策记录
├── storyboard/
│   └ storyboard.json   # 分镜脚本（含 narration_segments）
├── generated/
│   ├── frames/          # 生成的分镜图
│   ├── videos/          # 生成的视频
│   ├── music/           # 生成的音乐
│   └── narration/       # 生成的旁白音频
└── output/
    └── final.mp4        # 最终视频
```

---

## 错误处理

| 问题 | 处理方式 |
|------|---------|
| 视觉分析失败 | 询问用户描述素材内容 |
| API key 未配置 | 首次调用时询问 |
| API 调用失败 | 重试 2 次 → 询问用户 |
| 视频生成失败 | 尝试调整参数或用原始素材 |
| 音乐生成失败 | 生成静音视频并告知 |

---

## 依赖

- FFmpeg 6.0+
- Python 3.9+
- httpx
- google-genai（Veo 3 SDK）
- PIL（可选，用于图片尺寸处理）