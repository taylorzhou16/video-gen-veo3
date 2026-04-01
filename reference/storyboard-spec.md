# Veo 3 Storyboard Design Specifications

## Table of Contents

- Storyboard Structure (Scene / Shot)
- Character Registration and Reference Guidelines
- Storyboard Design Principles and Duration Limits
- shot_id Naming Rules
- T2V/I2V Selection Rules
- Two-stage Process (Fiction)
- First Frame Generation Strategy
- Dialogue Integration in video_prompt
- Narration Segmentation Planning (narration_segments)
- Storyboard JSON Format
- Review Check Mechanism
- Present to User for Confirmation

---

## Storyboard Structure

Uses **Scene-Shot two-layer structure**: `scenes[] → shots[]`

- **Scene**: Semantically+visually+spatially relatively stable narrative unit, duration = sum of subordinate shot durations
- **Shot**: Minimum video generation unit, fixed duration of 8 seconds (Veo 3.1 Fast maximum resolution requirement)

---

## Character Registration and Reference Guidelines

### Naming System

| Level | Purpose | Naming Convention | Example |
|-------|---------|-------------------|---------|
| **Character Name** | Display name for user interaction, Chinese description | Chinese name | `Xiaomei`, `Protagonist` |
| **Gender** | Character gender | male / female | `female` |
| **Reference Image** | Character appearance reference | Image path or null | `/path/to/ref.jpg` |

### Usage in Workflow

**Phase 1: Character Identification**
- After user confirms character identities, register to personas.json
- **Note**: Phase 1 only processes reference images uploaded by user, for those not uploaded leave `reference_image` empty, supplemented in Phase 2

**Phase 2: Character Reference Image Collection (Key)**
- Check characters with empty `reference_image`
- Ask user: AI generate / Upload reference image / Accept text-only (with warning)
- Update personas.json

**Phase 3: Storyboard Design (LLM Auto-generation)**
- LLM generates storyboard based on personas.json
- Fiction/Short Drama: **Must generate storyboard image first**, then img2video

**Phase 4: Generation Execution**
- Fiction: First use character reference image to generate storyboard image, then use storyboard image as first frame for video generation
- Vlog/Documentary: Directly use user materials as first frame

---

## Scene Fields

- `scene_id`: Scene number (e.g. "scene_1")
- `scene_name`: Scene name
- `duration`: Total scene duration = sum of all subordinate shot durations
- `narrative_goal`: Main narrative objective
- `spatial_setting`: Spatial setting
- `time_state`: Time state
- `visual_style`: Visual master style
- `shots[]`: Shot list

---

## Shot Fields

- `shot_id`: Shot number (format see naming rules below)
- `duration`: Duration (unit: seconds, Veo 3.1 Fast supports 4/6/8 seconds, 1080p/4k must use 8 seconds)
- `shot_type`: Shot type, options: establishing / dialogue / action / closeup / insert
- `description`: Brief description
- `generation_mode`: Generation mode, options: text2video / img2video
- `video_prompt`: Video generation prompt
- `image_prompt`: Image prompt (optional for img2video, used to generate storyboard image)
- `frame_path`: First frame image path (used for img2video)
- `dialogue`: Dialogue information (structured)
- `transition`: Transition effect
- `audio`: Audio configuration (enabled, generate_audio)
- `characters`: Characters in shot (optional)

---

## Storyboard Design Principles

1. **Duration Allocation**: Total duration = Target duration (±5s)
2. **Rhythm Variation**: Reflect rhythm through shot type, transition, and action changes
3. **Shot Type Variation**: Consecutive shots should have shot type differences
4. **Transition Selection**: Choose appropriate transitions based on emotion
5. **Single Action Principle**: Maximum 1 main action per shot
6. **Spatial Invariance Principle**: No spatial environment changes within a shot
7. **Concrete Description Principle**: Replace abstract action descriptions with concrete actions

### Duration Limits (Veo 3.1 Fast)

| Shot Type | Suggested Duration | Description |
|-----------|-------------------|-------------|
| Normal shots | 4-6s | Dialogue, daily actions, medium shots |
| Complex motion | 4s | Fast motion, action scenes, push/pull shots |
| Static emotion | 6-8s | Close-ups, emotional expression, slow push shots |

**Resolution Constraints**:
- **720p (default)**: Can use 4/6/8s
- **1080p/4k**: **Must use 8s**

---

## shot_id Naming Rules

Format: `scene{scene_number}_shot{shot_number}`

| Type | Example | Description |
|------|---------|-------------|
| Single shot | `scene1_shot1`, `scene2_shot1` | Standard naming |

---

## T2V/I2V Selection Rules

### Project Type and Generation Mode

| Project Type | Material Situation | Generation Mode | Description |
|--------------|-------------------|-----------------|-------------|
| **Fiction/Short Drama** | With/without character reference | `img2video` | Mandatory storyboard image |
| **MV Short Film** | With/without character reference | `img2video` | Mandatory storyboard image |
| **Vlog/Documentary** | User's real materials | `img2video` | User material first frame |
| **Commercial/Promotional** | Has real materials | `img2video` | Product material first frame |
| **Commercial/Promotional** | No real materials | `img2video` | Mandatory storyboard image |
| No clear type | No materials | `text2video` | Pure text-to-video |

### Decision Tree

```
Have material images?
├── Yes → img2video (image-to-video)
│         └── Use material as first frame
│
└── No → text2video (text-to-video)
          └── Pure text description generation
```

---

## Two-stage Process (Fiction)

**Fiction/Short Drama, MV Short Films must follow two-stage process**:

```
Stage 1: Image Prompt → Generate storyboard image
         ↓
Stage 2: Storyboard image as first frame → img2video (Veo 3)
```

### Step 1: Generate Storyboard Image

Use image_prompt to generate storyboard image. If shot involves characters, reference character reference image.

### Step 2: Storyboard Image as First Frame

Pass the generated storyboard image as `--image` parameter to Veo 3 image-to-video.

---

## First Frame Generation Strategy

### frame_strategy Field

| frame_strategy | Description | Execution Method |
|----------------|-------------|------------------|
| `none` | No first frame needed | Directly call text-to-video API |
| `first_frame_only` | First frame only | Generate first frame image → img2video API |

### Storyboard Image Generation Process

When need to generate storyboard image as first frame:

1. Write `image_prompt` (see prompt-guide.md for details)
2. Use image generation model to generate storyboard image
3. Pass storyboard image as `frame_path` to img2video

---

## Dialogue Integration in video_prompt

When shot contains dialogue, **must fully describe in video_prompt**: character (including appearance), dialogue content (in quotes, **keep character's original language**), expression/emotion, voice quality and speaking rate.

**Prompt written in English, dialogue keeps character language**:

```json
{
  "shot_id": "scene1_shot5",
  "video_prompt": "Xiaomei (a 25-year-old Asian woman with long black hair) looks up at the server, smiling gently and says, 'It's really quiet here, I like it.' Clear, pleasant voice, moderate pace. Keep 9:16 vertical composition.",
  "dialogue": {
    "speaker": "Xiaomei",
    "content": "It's really quiet here, I like it.",
    "emotion": "gentle, pleasant",
    "voice_type": "clear female voice"
  },
  "audio": {
    "enabled": true,
    "generate_audio": true
  }
}
```

### audio Field Description

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether to generate audio (including ambient sound + dialogue) |
| `generate_audio` | boolean | Veo 3 auto-generates audio, default true |

### BGM Decision Logic

BGM is mixed in post-production, not handled during video generation:
- `bgm.type = "ai_generated"` → Suno generates BGM, post-production mixing
- `bgm.type = "user_provided"` → User provides BGM, post-production mixing
- `bgm.type = "none"` → No BGM

---

## Narration Segmentation Planning (narration_segments)

### Trigger Condition

When `creative.json`'s `narration.type` is not `none`, need to plan narration segments.

### Field Structure

```json
{
  "narration_config": {
    "voice_style": "gentle female voice"    // Maps to TTS voice + emotion parameters
  },
  "narration_segments": [
    {
      "segment_id": "narr_1",
      "overall_time_range": "0-3s",
      "text": "This is a peaceful afternoon..."
    },
    {
      "segment_id": "narr_2",
      "overall_time_range": "8-11s",
      "text": "She sits by the window..."
    }
  ]
}
```

### Field Description

| Field | Type | Description |
|-------|------|-------------|
| `narration_config.voice_style` | string | Narration style description, maps to TTS parameters |
| `narration_segments` | array | Narration segment list |
| `segment_id` | string | Segment number (narr_1, narr_2...) |
| `overall_time_range` | string | Time range, calculated from video start point (0 seconds) |
| `text` | string | Narration copy |

### Planning Principles

1. **Time Calculation**: `overall_time_range` starts from video beginning, format is `"start_sec-end_sec"`
2. **Avoid Dialogue**: Don't conflict with shots that have character dialogue
3. **Segment Length**: Each segment should be speakable in 2-5 seconds (about 30-50 characters)
4. **Content Echo**: Narration content should echo the corresponding shot's visuals

### voice_style to TTS Parameter Mapping

| voice_style | voice | emotion |
|-------------|-------|---------|
| "gentle female voice" | `female_gentle` | `gentle` |
| "professional female narrator" | `female_narrator` | `neutral` |
| "warm male voice" | `male_warm` | `neutral` |
| "serious male voice" | `male_narrator` | `serious` |

---

## Storyboard JSON Format

```json
{
  "project_name": "Project Name",
  "project_type": "Fiction/Short Drama",
  "target_duration": 30,
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "elements": {
    "characters": [
      {
        "name": "Xiaomei",
        "gender": "female",
        "reference_image": "/path/to/ref.jpg",
        "features": "25-year-old Asian female, long straight black hair, oval face"
      }
    ]
  },
  "scenes": [
    {
      "scene_id": "scene_1",
      "scene_name": "Opening - Coffee Shop",
      "duration": 15,
      "narrative_goal": "Show coffee shop atmosphere",
      "spatial_setting": "Cozy city coffee shop",
      "time_state": "3 PM",
      "visual_style": "Warm tones, cinematic",
      "shots": [
        {
          "shot_id": "scene1_shot1",
          "duration": 6,
          "shot_type": "establishing",
          "description": "Coffee shop wide shot",
          "generation_mode": "img2video",
          "video_prompt": "Interior of a cozy city coffee shop, afternoon sunlight streaming through large floor-to-ceiling windows, slow push in. Keep 9:16 vertical composition.",
          "image_prompt": "Cinematic realistic start frame. Interior of a cozy city coffee shop, afternoon sunlight streaming through large windows, shallow depth of field, cinematic look, 9:16 aspect ratio",
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
          "duration": 6,
          "shot_type": "closeup",
          "description": "Female protagonist close-up",
          "generation_mode": "img2video",
          "video_prompt": "Xiaomei (a 25-year-old Asian woman with long black hair) sits by the coffee shop window, smiling gently and says, 'It's really quiet here, I like it.' Clear, pleasant voice, moderate pace. Keep 9:16 vertical composition.",
          "image_prompt": "Cinematic realistic start frame. A 25-year-old Asian woman with long black hair, wearing a white shirt, sitting by the coffee shop window with a gentle smile, warm lighting, cinematic look, 9:16 aspect ratio",
          "frame_path": "generated/frames/scene1_shot2_frame.png",
          "dialogue": {
            "speaker": "Xiaomei",
            "content": "It's really quiet here, I like it.",
            "emotion": "gentle, pleasant",
            "voice_type": "clear female voice"
          },
          "transition": "cut",
          "characters": ["Xiaomei"],
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

## Review Check Mechanism

After generating storyboard, must check the following items:

**1. Structural Completeness**
- Total duration = Number of shots × Single shot duration (usually 8 seconds)
- Scene duration = Sum of subordinate shot durations

**2. Storyboard Rules**
- Each shot duration 4/6/8 seconds (1080p/4k must use 8 seconds)
- No multi-action shots, no spatial changes within shots

**3. Prompt Standards**
- All video_prompts include aspect ratio information
- Dialogue integrated into video_prompt
- No abstract action descriptions

**4. Technical Selection**
- text2video/img2video selection is reasonable
- Fiction mandatory img2video + storyboard image
- Resolution set correctly

---

## Present to User for Confirmation

**Must have explicit user confirmation before entering execution phase!**

When confirming, display for each shot:
- Scene information
- Generation mode (text2video/img2video)
- video_prompt
- image_prompt (if any)
- frame_path (if any)
- Dialogue
- Duration
- Transition

User can choose: Confirm and Execute / Modify Storyboard / Adjust Narration / Adjust Duration / Change Transition / Cancel