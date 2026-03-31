# Veo 3 分镜设计规范

## 目录

- Storyboard 结构（Scene / Shot）
- 人物注册与引用规范
- 分镜设计原则与时长限制
- shot_id 命名规则
- T2V/I2V 选择规则
- 两阶段流程（虚构片）
- 首帧生成策略
- 台词融入 video_prompt
- Storyboard JSON 格式
- Review 检查机制
- 展示给用户确认

---

## Storyboard 结构

采用 **场景-分镜两层结构**：`scenes[] → shots[]`

- **场景 (Scene)**：语义+视觉+时空相对稳定的叙事单元，时长 = 下属分镜时长之和
- **分镜 (Shot)**：最小视频生成单元，时长固定 8 秒（Veo 3.1 Fast 最高分辨率要求）

---

## 人物注册与引用规范

### 命名体系

| 层级 | 用途 | 命名规范 | 示例 |
|------|------|---------|------|
| **人物名称** | 显示名称，用于用户交互、中文描述 | 中文名 | `小美`, `主角` |
| **性别** | 人物性别 | male / female | `female` |
| **参考图** | 人物外貌参考 | 图片路径或 null | `/path/to/ref.jpg` |

### Workflow 中的使用流程

**Phase 1: 人物识别**
- 用户确认人物身份后，注册到 personas.json
- **注意**：Phase 1 只处理用户已上传的参考图，未上传的 `reference_image` 留空，由 Phase 2 补充

**Phase 2: 角色参考图收集（关键）**
- 检查 `reference_image` 为空的角色
- 询问用户：AI生成 / 上传参考图 / 接受纯文字（警告）
- 更新 personas.json

**Phase 3: 分镜设计（LLM 自动生成）**
- LLM 根据 personas.json 生成分镜
- 虚构片/短剧：**强制先生成分镜图**，然后 img2video

**Phase 4: 执行生成**
- 虚构片：先用角色参考图生成分镜图，再用分镜图作为首帧生成视频
- Vlog/写实类：直接用用户素材作为首帧

---

## 场景字段（Scene）

- `scene_id`：场景编号（如 "scene_1"）
- `scene_name`：场景名称
- `duration`：场景总时长 = 下属所有分镜时长之和
- `narrative_goal`：主叙事目标
- `spatial_setting`：空间设定
- `time_state`：时间状态
- `visual_style`：视觉母风格
- `shots[]`：分镜列表

---

## 分镜字段（Shot）

- `shot_id`：分镜编号（格式见下文命名规则）
- `duration`：时长（单位：秒，Veo 3.1 Fast 支持 4/6/8 秒，1080p/4k 必须用 8秒）
- `shot_type`：景别类型，可选：establishing（全景）/ dialogue（对话）/ action（动作）/ closeup（特写）/ insert（插入镜头）
- `description`：简要描述
- `generation_mode`：生成模式，可选：text2video / img2video
- `video_prompt`：视频生成提示词
- `image_prompt`：图片提示词（img2video 时可选，用于生成分镜图）
- `frame_path`：首帧图片路径（img2video 时使用）
- `dialogue`：台词信息（结构化）
- `transition`：转场效果
- `audio`：音频配置（enabled, generate_audio）
- `characters`：镜头涉及的角色（可选）

---

## 分镜设计原则

1. **时长分配**：总时长 = 目标时长（±5秒）
2. **节奏变化**：通过景别、转场、动作变化体现节奏
3. **景别变化**：连续镜头应有景别差异
4. **转场选择**：根据情绪选择合适转场
5. **单一动作原则**：同一分镜内最多 1 个主要动作
6. **空间不变原则**：禁止在 shot 内发生空间环境变化
7. **描述具体原则**：禁止抽象动作描述，用具体动作替代

### 时长限制（Veo 3.1 Fast）

| 镜头类型 | 建议时长 | 说明 |
|---------|---------|------|
| 普通镜头 | 4-6 秒 | 对话、日常动作、中景镜头 |
| 复杂运动 | 4 秒 | 快速运动、动作戏、推拉镜头 |
| 静态情绪 | 6-8 秒 | 特写、情绪表达、缓推镜头 |

**分辨率约束**：
- **720p（默认）**：可用 4/6/8 秒
- **1080p/4k**：**必须用 8 秒**

---

## shot_id 命名规则

格式：`scene{场景号}_shot{分镜号}`

| 类型 | 示例 | 说明 |
|------|------|------|
| 单分镜 | `scene1_shot1`、`scene2_shot1` | 标准命名 |

---

## T2V/I2V 选择规则

### 项目类型与生成模式

| 项目类型 | 素材情况 | 生成模式 | 说明 |
|---------|---------|---------|------|
| **虚构片/短剧** | 有/无角色参考图 | `img2video` | 强制分镜图 |
| **MV短片** | 有/无角色参考图 | `img2video` | 强制分镜图 |
| **Vlog/写实类** | 用户真实素材 | `img2video` | 用户素材首帧 |
| **广告片/宣传片** | 有真实素材 | `img2video` | 产品素材首帧 |
| **广告片/宣传片** | 无真实素材 | `img2video` | 强制分镜图 |
| 无明确类型 | 无素材 | `text2video` | 纯文生视频 |

### 决策树

```
有素材图片吗？
├── 有 → img2video（图生视频）
│         └── 使用素材作为首帧
│
└── 无 → text2video（文生视频）
          └── 纯文字描述生成
```

---

## 两阶段流程（虚构片）

**虚构片/短剧、MV短片必须走两阶段流程**：

```
阶段1: Image Prompt → 生成分镜图
         ↓
阶段2: 分镜图作为首帧 → img2video（Veo 3）
```

### Step 1: 生成分镜图

使用 image_prompt 生成分镜图，如果镜头涉及角色，需引用角色参考图。

### Step 2: 分镜图作为首帧

将生成的分镜图作为 `--image` 参数传入 Veo 3 图生视频。

---

## 首帧生成策略

### frame_strategy 字段

| frame_strategy | 说明 | 执行方式 |
|---|------|---------|
| `none` | 无需首帧 | 直接调用文生视频 API |
| `first_frame_only` | 仅首帧 | 生成首帧图 → img2video API |

### 分镜图生成流程

当需要生成分镜图作为首帧时：

1. 编写 `image_prompt`（详见 prompt-guide.md）
2. 使用图片生成模型生成分镜图
3. 将分镜图作为 `frame_path` 传入 img2video

---

## 台词融入 video_prompt

当镜头包含台词时，**必须在 video_prompt 中完整描述**：角色（含外貌）、台词内容（引号包裹）、表情/情绪、声音特质和语速。

```json
{
  "shot_id": "scene1_shot5",
  "video_prompt": "小美（25岁亚洲女性，黑色长直发）抬头看向服务生，温柔微笑着说：'这里真的很安静，我很喜欢。' 声音清脆悦耳，语速适中偏慢。保持竖屏9:16构图。",
  "dialogue": {
    "speaker": "小美",
    "content": "这里真的很安静，我很喜欢。",
    "emotion": "温柔、愉悦",
    "voice_type": "清脆女声"
  },
  "audio": {
    "enabled": true,
    "generate_audio": true
  }
}
```

### audio 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | boolean | 是否生成音频（包含环境音 + 台词） |
| `generate_audio` | boolean | Veo 3 自动生成音频，默认 true |

### BGM 决策逻辑

BGM 由后期合成，不在视频生成阶段处理：
- `bgm.type = "ai_generated"` → Suno 生成 BGM，后期混音
- `bgm.type = "user_provided"` → 用户提供 BGM，后期混音
- `bgm.type = "none"` → 无 BGM

---

## Storyboard JSON 格式

```json
{
  "project_name": "项目名称",
  "project_type": "虚构片/短剧",
  "target_duration": 30,
  "aspect_ratio": "9:16",
  "resolution": "1080p",
  "elements": {
    "characters": [
      {
        "name": "小美",
        "gender": "female",
        "reference_image": "/path/to/ref.jpg",
        "features": "25岁亚洲女性，黑色长直发，瓜子脸"
      }
    ]
  },
  "scenes": [
    {
      "scene_id": "scene_1",
      "scene_name": "开场 - 咖啡馆",
      "duration": 15,
      "narrative_goal": "展示咖啡馆氛围",
      "spatial_setting": "温馨的城市咖啡馆",
      "time_state": "下午3点",
      "visual_style": "温暖色调，电影感",
      "shots": [
        {
          "shot_id": "scene1_shot1",
          "duration": 5,
          "shot_type": "establishing",
          "description": "咖啡馆全景",
          "generation_mode": "img2video",
          "video_prompt": "温馨的城市咖啡馆内部全景，午后阳光透过落地窗洒进来，镜头缓慢推近。保持竖屏9:16构图。",
          "image_prompt": "Cinematic realistic start frame. 温馨的城市咖啡馆内部全景，午后阳光透过落地窗洒进来，浅景深，电影感，9:16画面比例",
          "frame_path": "generated/frames/scene1_shot1_frame.png",
          "dialogue": null,
          "transition": "fade_in",
          "characters": [],
          "audio": {
            "enabled": true,
            "generate_audio": true
          }
        },
        {
          "shot_id": "scene1_shot2",
          "duration": 5,
          "shot_type": "closeup",
          "description": "女主角特写",
          "generation_mode": "img2video",
          "video_prompt": "小美（25岁亚洲女性，黑色长直发）坐在咖啡馆窗边，温柔微笑着说：'这里真的很安静，我很喜欢。' 声音清脆悦耳，语速适中。保持竖屏9:16构图。",
          "image_prompt": "Cinematic realistic start frame. 25岁亚洲女性，黑色长直发，穿着白色衬衫，坐在咖啡馆窗边，温柔微笑，温暖光线，电影感，9:16画面比例",
          "frame_path": "generated/frames/scene1_shot2_frame.png",
          "dialogue": {
            "speaker": "小美",
            "content": "这里真的很安静，我很喜欢。",
            "emotion": "温柔、愉悦",
            "voice_type": "清脆女声"
          },
          "transition": "cut",
          "characters": ["小美"],
          "audio": {
            "enabled": true,
            "generate_audio": true
          }
        }
      ]
    }
  ],
  "props": [],
  "decision_log": {}
}
```

---

## Review 检查机制

生成 storyboard 后，必须检查以下项目：

**1. 结构完整性**
- 总时长 = 镜头数 × 单镜头时长（通常 8秒）
- 场景时长 = 下属分镜时长之和

**2. 分镜规则**
- 每个分镜时长 4/6/8 秒（1080p/4k 必须用 8秒）
- 无多动作分镜、无分镜内空间变化

**3. Prompt 规范**
- 所有 video_prompt 包含比例信息
- 台词已融入 video_prompt
- 无抽象动作描述

**4. 技术选择**
- text2video/img2video 选择合理
- 虚构片强制 img2video + 分镜图
- 分辨率设置正确

---

## 展示给用户确认

**必须在用户明确确认后，才能进入执行阶段！**

确认时展示每个镜头的：
- 场景信息
- 生成模式（text2video/img2video）
- video_prompt
- image_prompt（如有）
- frame_path（如有）
- 台词
- 时长
- 转场

用户可选择：确认并执行 / 修改分镜 / 调整时长 / 更换转场 / 取消