# Veo 3 Prompt 编写规范

## 目录

- **重要规则**
- 基础概念
- 文生视频 Prompt
- 图生视频 Prompt
- image_prompt（分镜图生成）
- 两阶段流程（虚构片）
- 一致性规范
- 比例约束
- 台词与音频
- 附录：模板速查

---

## 重要规则

**所有 video_prompt 和 image_prompt 必须使用英文编写。**

Veo 3.1 Fast 对英文 prompt 的理解更准确，能生成更高质量的结果。

**但台词内容保持角色原本的语言（不能 OOC）**：
- 中文角色说中文台词
- 英文角色说英文台词
- 台词内容嵌入英文 prompt 中

**示例**：
```
The female lead (a 25-year-old Asian woman with long black hair) looks up with a gentle smile and says, "这里真的很安静，我很喜欢。" Clear voice, moderate pace.
```

---

## 基础概念

### Veo 3 能力对比

| 功能 | Veo 3.1 Fast | Kling-3.0 | Vidu Q3 Pro |
|------|-------------|-----------|-------------|
| 文生视频 | ✅ | ✅ | ✅ |
| 图生视频 | ✅ | ✅ | ✅ |
| 自动音频 | ✅ 原生支持 | ✅ | ✅ |
| 参考图 (referenceImages) | ❌（仅 Veo 3.1 支持） | ❌ (仅 Omni) | ❌ |
| 多镜头模式 (multi_shot) | ❌ 不支持 | ✅ | ❌ |
| 首帧控制 | ✅ | ✅ | ✅ |
| 最大时长 | 8秒 | 10秒 | 8秒 |
| 最高分辨率 | 4k | 1080p | 720p |

### 关键差异

**Veo 3.1 Fast vs Kling/Vidu**：
- Veo 3.1 Fast **不支持**参考图（referenceImages，仅 Veo 3.1 支持），角色一致性只能通过首帧控制或详细文字描述
- Veo 3.1 Fast **不支持**多镜头模式（multi_shot），每个镜头独立生成
- Veo 3.1 Fast 自动音频更强大，支持简单对话
- Veo 3.1 Fast 时长限制：4/6/8秒（1080p/4k 必须用 8秒）
- Veo 3.1 Fast 支持更高分辨率（4k）

---

## 文生视频 Prompt

### 结构要素（按顺序）

1. **整体动作概述** — 简要描述镜头整体动作
2. **分段动作** — 按时间轴：0-2s, 2-5s...（长视频推荐）
3. **主体描述** — 人物/物体的外观特征
4. **场景/环境** — 地点、时间、环境细节
5. **运镜描述** — 推/拉/摇/移/跟/升降
6. **风格/氛围** — 电影感、光线、色调
7. **台词信息** — 角色、内容、情绪、语速（如有）
8. **比例保护** — "保持XX比例构图"

### 基础模板

```
整体：{镜头整体动作描述}

分段动作（{duration}秒）：
{time_range_1}: {动作描述}
{time_range_2}: {动作描述 + 台词同步}
...

运镜：{镜头运动描述}
节奏：{运动节奏}
画面稳定性：{保持稳定/轻微晃动}
{台词信息}
保持{比例}构图，不破坏画面比例
```

### 完整示例（6秒镜头，720p 默认配置）

```
Overall: A woman looks up from her contemplation toward the window, a gentle smile gradually appearing on her face.

Segmented actions (6 seconds):
0-2s: Woman in profile, gazing out the window with a calm expression
2-4s: The corners of her mouth slowly curve upward, her gaze softens
4-6s: She turns fully toward the camera with a natural, gentle smile

Camera: Slow push in, steady
Rhythm: Slow and smooth
Stability: Stable
Dialogue: The woman says gently, "这是我最喜欢的地方。" Clear voice, moderate pace.
Keep 9:16 vertical composition, subject centered in frame
```

### 简洁模板（短视频）

```
[Subject] + [Action] + [Scene] + [Style] + [Camera] + [Aspect Ratio]

Example:
A 25-year-old Asian woman with long black hair, wearing a beige knit sweater,
sitting by the window in a cozy coffee shop, slowly opening her eyes with a gentle smile,
warm afternoon sunlight streaming through the large windows, cinematic color grading, shallow depth of field,
slow push in, 9:16 vertical composition
```

---

## 图生视频 Prompt

### 工作模式

图生视频模式下：
1. **图片作为首帧**：视频从这张图片开始
2. **Prompt 描述运动**：描述图片中元素如何运动
3. **自动继承画面**：场景、光线、构图从图片继承

### Prompt 结构

```
[Motion/Action] + [Mood/Atmosphere] + [Camera Movement] + [Aspect Ratio Protection]
```

### 完整示例

**输入图片**：一张女性肖像照片

**video_prompt**：
```
The woman in the image slowly opens her eyes, revealing a gentle smile,
warm atmosphere, slight push in, keep 9:16 vertical composition
```

### 注意事项

- Prompt 重点描述**动作**，场景从图片自动继承
- 不要重复描述图片中已有的静态元素
- 描述运动时保持画面的连贯性

---

## image_prompt（分镜图生成）

用于生成分镜图作为首帧。**虚构片/短剧必须先生成分镜图**。

### 五要素结构

1. **场景**：时间、地点、环境
2. **主体**：人物外貌、服饰、姿态
3. **光影**：光线方向、色温、氛围
4. **风格**：cinematic / realistic / anime
5. **比例**：竖屏9:16 / 横屏16:9 / 正方形1:1

### 基础模板

```
Cinematic realistic start frame.

Scene: {具体场景描述}
Location details: {环境细节}

{人物外貌详细描述}，{姿态}，{表情}，{位置}

Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {灯光描述}
Color grade: {色调}
Aspect ratio: {画面比例}

Style: {cinematic realistic/film grain/etc.}
```

### 完整示例

```
Cinematic realistic start frame.

Scene: A cozy coffee shop interior, afternoon sunlight streaming through large windows
Location details: wooden tables, warm lighting, coffee cups, soft background blur

A 25-year-old Asian woman with long black hair, wearing a beige knit sweater,
sitting by the window, hands wrapped around a coffee cup, gentle smile

Shot scale: Medium shot
Camera angle: Eye-level, slightly from the side
Lighting: Warm natural light from window, soft shadows
Color grade: Warm golden tones

Style: Cinematic realistic, film grain, shallow depth of field, 9:16 aspect ratio
```

---

## 两阶段流程（虚构片）

**虚构片/短剧、MV短片必须走两阶段流程**：

```
阶段1: Image Prompt → 生成分镜图（控制场景/画风/灯光/氛围/色彩/妆造）
         ↓
阶段2: 分镜图作为首帧 → img2video（Veo 3）
```

### Step 1: 生成分镜图

使用 image_prompt 生成分镜图：

```bash
python video_gen_tools.py image \
  --prompt "Cinematic realistic start frame.
Scene: 温馨咖啡馆内部...
A 25-year-old Asian woman with long black hair...
Style: Cinematic realistic, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output generated/frames/scene1_shot1_frame.png
```

### Step 2: 分镜图作为首帧生成视频

```bash
python video_gen_tools.py video \
  --image generated/frames/scene1_shot1_frame.png \
  --prompt "图中人物缓缓睁开眼睛，露出温柔微笑。保持竖屏9:16构图。" \
  --duration 5 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

### 跨镜头角色一致性

由于 Veo 3 不支持多参考图，跨镜头一致性需要通过：

1. **角色参考图**：用于生成分镜图时保持人物外貌一致
2. **详细的文字描述**：每个 image_prompt 使用相同的人物描述
3. **分镜图首帧**：确保场景和人物姿态一致

**角色一致性模板**：

在每个包含人物的分镜图 image_prompt 中，保持以下描述一致：

```
人物标识：{名字}
外貌特征：{性别}，{年龄}，{发型}，{面部特征}，{体型}
服饰描述：{款式}，{颜色}，{材质}，{配饰}
标志性特征：{特殊标记、习惯动作等}
```

**示例**：
```
小美，25岁亚洲女性，黑色长直发及腰，瓜子脸，大眼睛，
穿着白色衬衫和牛仔裤，戴着细银项链，
习惯性将头发别到耳后
```

---

## 一致性规范

### 单一镜头内的一致性

- 保持主体特征描述一致
- 保持场景描述一致
- 保持风格描述一致

### 跨镜头的一致性（Veo 3 限制）

Veo 3 不支持多参考图，跨镜头一致性需要通过：

1. **分镜图首帧**：先生成分镜图，再作为首帧生成视频
2. **详细的文字描述**：每个镜头使用相同的人物描述
3. **角色参考图**：用于生成分镜图时保持人物外貌

---

## 比例约束

### 画面比例

| 比例 | 适用平台 | 描述方式 |
|------|---------|---------|
| 9:16 | 抖音/小红书 | "竖屏构图，9:16画面比例，人物/主体位于画面中央" |
| 16:9 | B站/YouTube | "横屏构图，16:9画面比例" |
| 1:1 | Instagram | "正方形构图，1:1画面比例，主体居中" |

### CLI 参数

```bash
# 通过 --aspect-ratio 参数传递
python video_gen_tools.py video --prompt "..." --aspect-ratio 9:16
```

**重要**：`aspect_ratio` 从 `storyboard.json` 读取，所有视频生成必须传递此参数。

---

## 台词与音频

### Veo 3 自动音频

Veo 3 自动生成以下音频：
- **环境音**：风声、雨声、街道噪音、咖啡馆背景音等
- **音效**：脚步声、开门声、物品碰撞等
- **简单对话**：基本的语音内容

### 台词融入 Prompt

当镜头包含台词时，**必须在 video_prompt 中完整描述**：角色（含外貌）、台词内容（引号包裹，**保持角色原语言**）、表情/情绪、声音特质和语速。

**Prompt 用英文编写，台词保持角色语言**：

```
The female lead (a 25-year-old Asian woman with long black hair) looks up at the server,
smiling gently and says, "这里真的很安静，我很喜欢。"
Clear, pleasant voice, moderate pace.
```

### audio 字段与 API 映射

| storyboard 字段 | API 参数 | 说明 |
|----------------|----------|------|
| `audio.enabled = true` | `--audio` | 生成环境音/台词 |
| `audio.enabled = false` | 无 `--audio` | 静音输出 |

### BGM 约束

BGM 由后期合成（Suno 生成或用户提供），不在视频生成阶段处理。

---

## TTS 旁白生成

**触发条件**：`storyboard.json` 存在 `narration_segments` 字段。

**数据来源**：
- `narration_config.voice_style` → 映射到 TTS 的 voice 和 emotion 参数
- `narration_segments[].text` → TTS 的 --text 参数
- `narration_segments[].segment_id` → 输出文件命名

**CLI 调用示例**：

```bash
# 每段旁白单独生成
python video_gen_tools.py tts \
  --text "这是一个宁静的下午，阳光透过落地窗洒进咖啡馆..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3
```

**voice 参数（火山引擎 TTS 音色）**：

| 参数值 | 音色说明 | 火山引擎 ID |
|-------|---------|------------|
| `female_narrator` | 女声旁白，专业沉稳 | BV700_streaming |
| `female_gentle` | 女声温柔，柔和亲切 | BV034_streaming |
| `male_narrator` | 男声旁白，专业沉稳 | BV701_streaming |
| `male_warm` | 男声温暖，磁性亲切 | BV033_streaming |

**emotion 参数（可选）**：

| 参数值 | 情感风格 |
|-------|---------|
| `neutral` | 中性（默认） |
| `happy` | 开心 |
| `sad` | 悲伤 |
| `gentle` | 温柔 |
| `serious` | 严肃 |

**voice_style 到 TTS 参数映射**：

用户在 Phase 2 指定的 voice_style（如"温柔女声"）会在 Phase 3 映射到具体的 TTS 参数：
- "温柔女声" → `voice: female_gentle, emotion: gentle`
- "专业女声旁白" → `voice: female_narrator, emotion: neutral`
- "磁性男声" → `voice: male_warm, emotion: neutral`
- "严肃男声" → `voice: male_narrator, emotion: serious`

**重要**：一条视频内使用同一套 voice + emotion 参数，保证旁白风格统一。

---

## 附录：模板速查

### 文生视频模板（完整版）

```
Overall: {镜头整体动作描述}

Segmented actions ({duration}s):
{time_range_1}: {动作描述}
{time_range_2}: {动作描述 + 台词同步}

Camera: {镜头运动描述}
Rhythm: {运动节奏}
Stability: {stable/slight shake}
{台词信息}
Keep {比例} composition, maintain aspect ratio
```

### 文生视频模板（简洁版）

```
[Subject] + [Action] + [Scene] + [Style] + [Camera] + [Aspect Ratio]
```

### 图生视频模板

```
[Motion/Action] + [Atmosphere] + [Camera] + [Aspect Ratio Protection]

Example:
The woman in the image slowly opens her eyes with a gentle smile,
warm atmosphere, slight push in, keep 9:16 vertical composition
```

### image_prompt 模板（分镜图）

```
Cinematic realistic start frame.

Scene: {场景描述}
Location details: {环境细节}

{人物外貌描述}, {姿态}, {表情}, {位置}

Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {灯光描述}
Color grade: {色调}
Aspect ratio: {画面比例}

Style: Cinematic realistic, film grain, shallow depth of field
```

### 两阶段流程示例

```
# Step 1: 生成分镜图
image_prompt = "Cinematic start frame. A 25-year-old Asian woman with long black hair..."

# Step 2: 分镜图作为首帧
video_prompt = "图中人物缓缓睁开眼睛..."
```