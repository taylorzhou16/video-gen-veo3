---
name: video-gen-veo3
description: AI video editing tool (Veo 3.1 Fast version). Analyze materials, generate creative ideas, design storyboards, execute editing. Uses Veo 3.1 Fast for video generation (supports text-to-video, image-to-video). Triggers when users request video creation with Veo 3, Veo 3.1 Fast, or Compass API.
argument-hint: <material_directory_or_video_file>
---

# Vico-Edit Veo3 User Guide

**Role**: Director Agent — Understand creative intent, coordinate all resources, deliver video works.

**Language Requirement**: Respond in the same language the user uses. If user writes in Chinese, respond in Chinese; if user writes in English, respond in English.

---

## Recommended Configuration

**Must use a multimodal model** (such as Claude Opus/Sonnet/Kimi-K2.5) for the best experience. The model itself has visual understanding capabilities and can analyze images directly through the Read tool.

---

## Core Concepts

- **Tool Files**: video_gen_tools.py (API calls) and video_gen_editor.py (FFmpeg editing) are command-line tools
- **Flexible Planning, Robust Execution**: Planning phase produces structured artifacts, execution phase is driven by storyboard plan
- **Graceful Degradation**: Proactively seek user help when encountering problems, rather than getting stuck

### Veo 3.1 Fast Capabilities Overview

| Feature | Input | Output | Resolution |
|---------|-------|--------|------------|
| Text-to-video + Audio | Text prompt | Video + Audio | 720p, 1080p, 4k |
| Image-to-video + Audio | Image + Text prompt | Video + Audio | 720p, 1080p, 4k |
| Text-to-video (no audio) | Text prompt | Video | 720p, 1080p, 4k |
| Image-to-video (no audio) | Image + Text prompt | Video | 720p, 1080p, 4k |

**Key Features**:
- **Automatic Audio Generation**: Native sound effects, ambient sounds, simple dialogue
- **Image-to-video**: Image as first frame
- **High Resolution**: Up to 4k output
- **Duration Limits**: 4/6/8 seconds (1080p/4k must use 8 seconds)

**Comparison with Kling/Vidu**:

| Feature | Veo 3.1 Fast | Kling-3.0 | Vidu Q3 Pro |
|---------|--------------|-----------|-------------|
| Text-to-video | ✅ | ✅ | ✅ |
| Image-to-video (first frame) | ✅ | ✅ | ✅ |
| Automatic Audio | ✅ Native support | ✅ | ✅ |
| Multi-shot mode (multi_shot) | ❌ | ✅ | ❌ |
| Max Duration | 8s | 10s | 8s |
| Max Resolution | 4k | 1080p | 720p |

---

## Quick Start Workflow

```
Environment Check → Material Collection → Creative Confirmation → Storyboard Design → Generation Execution → Editing Output
      5s                Interactive         Interactive           Interactive           Automatic            Automatic
```

### Workflow Progress Checklist

```
Task Progress:
- [ ] Phase 0: Environment Check (python video_gen_tools.py check)
- [ ] Phase 1: Material Collection (scan + visual analysis + character identification)
- [ ] Phase 2: Creative Confirmation (question card interaction + character reference collection)
- [ ] Phase 3: Storyboard Design (generate storyboard.json + auto generation mode selection + user confirmation)
- [ ] Phase 4: Generation Execution (Veo 3 API calls + progress tracking)
- [ ] Phase 5: Editing Output (concatenation + transitions + color grading + music)
```

---

## Phase 0: Environment Check

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check
```

- Basic dependencies (FFmpeg/Python/httpx) fail → Stop and provide installation instructions
- API key not configured → Record status, ask later as needed

---

## Phase 1: Material Collection

### Material Source Identification

- **Directory path** → Scan directory or user-sent image/video files
- **Video file** → Analyze that video directly
- **No materials** → Pure creative mode

### Visual Analysis Process

Use the Read tool to read images. Record scene description, subject content, emotional tone, color style.

If unable to analyze images, proactively ask the user to describe each material's content.

### Character Identification (Conditional)

**Triggered only when user provides character portrait images** (ask user if unsure).

Execution steps:
1. Read image content, identify all characters
2. Ask user to confirm each character's identity
3. Register each using PersonaManager:

```python
from video_gen_tools import PersonaManager
manager = PersonaManager(project_dir)

# Case A: User provided reference image
manager.register("Xiaomei", "female", "path/to/ref.jpg", "long hair, oval face")

# Case B: User did not provide reference image (Phase 2 will supplement)
manager.register("Protagonist", "male", None, "short hair, sporty style")
```

**Phase 1 Key Principles**:
- Only process reference images **already uploaded** by user
- For characters without uploads, set reference_image to `None`, supplemented in Phase 2
- Do not ask about reference images not uploaded at this stage

### Phase 1 Outputs

Create project directory `~/video-gen-projects/{project_name}_{timestamp}/`, outputs:
- `state.json` — Project status
- `analysis/analysis.json` — Material analysis results
- `personas.json` — Character registry (reference_image may be None)

**personas.json Structure**:
```json
{
  "personas": [
    {
      "name": "Xiaomei",
      "gender": "female",
      "reference_image": "/path/to/ref.jpg",
      "features": "long hair, oval face"
    },
    {
      "name": "Protagonist",
      "gender": "male",
      "reference_image": null,
      "features": "short hair, sporty style"
    }
  ]
}
```

---

## Phase 2: Creative Confirmation

**Use question cards to interact with user**, collecting key information.

### Question Card Design

**Question 1: Video Style**
- Options: Cinematic | Vlog Style | Commercial | Documentary | Art/Experimental
- Description: Determines overall tone for color grading, transitions, and music

**Question 2: Target Duration**
- Options: 15s (short video) | 30s (standard) | 60s (long video) | Custom
- Description: Affects number of shots and pacing

**Question 3: Aspect Ratio**
- Options: 9:16 (TikTok/Xiaohongshu) | 16:9 (Bilibili/YouTube)
- Description: Choose based on publishing platform

**Question 4: Resolution and Shot Duration**
- Options:
  - 720p (default) + 4s/6s/8s
  - 1080p + 8s (high quality)
  - 4k + 8s (highest quality)
- Description: **1080p/4k must use 8 second duration**, 720p can choose 4/6/8s

**Question 5: Audio (Sync Sound)**
- Options: Auto generate (Veo 3 auto-generates ambient sounds/dialogue) | No audio needed
- Description: Veo 3 automatically generates ambient sounds, sound effects, simple dialogue (sync sound)

**Question 6: Narration/Voiceover**

**First determine if video type is suitable for narration**:

| Video Style | Narration Need | Description |
|-------------|----------------|-------------|
| Cinematic/Fiction | Usually not needed | Character dialogue is primary, narration breaks immersion |
| Documentary | Usually needed | Scene explanation, background introduction |
| Vlog Style | May be needed | Travel commentary, mood recording |
| Commercial | May be needed | Product introduction, brand story |
| Art/Experimental | Case by case | Concept expression may need narration |

**When uncertain, ask the user**:

> Does this video need narration/voiceover?
> - **No narration needed** (character dialogue is primary, or pure visual expression)
> - **Need AI-generated narration** (I will write copy based on storyboard)
> - **I already have narration copy** (user provides complete text)

**Distinguish Two Audio Generation Methods**:

**A. Character Dialogue (Sync Sound)**
- Generated directly by Veo 3 video generation model
- Need to clearly describe in shot's video_prompt: character, dialogue, emotion, speaking rate, voice quality
- Set `audio: true` during video generation

**B. Narration/Voiceover (Post-production Dubbing)**
- Generated by TTS in post-production, mixed in during editing phase
- Used for scene explanation, background introduction, emotional enhancement
- Phase 3 will design narration copy and timing points based on storyboard

**Important Principle**: For shots that can capture sync sound, do not use post-production TTS dubbing!

**Question 7: Music Needs**
- Options: AI-generated BGM | No music needed | I already have music
- Description: BGM generated by Suno or provided by user, mixed in post-production

**BGM Decision Impact on video_prompt**:
- If "AI-generated BGM" or "I already have music" selected → All shots will have `audio.no_bgm = true`, video_prompt will include "No background music. Natural ambient sound only."
- If "No music needed" selected → Shots will have `audio.no_bgm = false`, video model decides freely

**Important**: This ensures video generation only produces ambient sounds and sync dialogue, BGM is added separately in post-production.

**Question 8: Character Reference Image Collection**

**Trigger Condition**: Check personas.json, trigger when characters have null/empty `reference_image`.

**Ask for each character without reference image**:

> **Character "{name}" needs a reference image**
>
> Please select reference image source:
> - **A. AI-generated character image** (recommended, auto-generates standard reference image)
> - **B. Upload reference image** (user provides character photo)
> - **C. Accept text-only generation** (character appearance may be inconsistent across shots)

### Phase 2 Outputs

- `creative/creative.json` — Creative plan
- Updated `personas.json` — Supplemented reference_images (if any)
- `creative/decision_log.json` — Decision record

**creative.json narration field structure**:

```json
{
  "narration": {
    "type": "ai_generated",           // none / ai_generated / user_provided
    "voice_style": "gentle female voice",  // Narration style (user-specified when ai_generated)
    "user_text": "Complete narration copy provided by user"  // Required when user_provided
  }
}
```

| type | Description | Phase 3 Handling |
|------|-------------|------------------|
| `none` | No narration needed | Do not plan narration_segments |
| `ai_generated` | AI designs copy | Auto-write narration based on storyboard, segment by shot |
| `user_provided` | User already has copy | Segment user_text by shot timing points |

---

## Phase 3: Storyboard Design

### Mandatory Reading Before Generating Storyboard

**Before generating storyboard script, must read the following two documents**:

```
Read: reference/storyboard-spec.md   # Storyboard specifications, JSON format
Read: reference/prompt-guide.md       # Prompt writing guidelines
```

### Step 1: Sync Character Info to Storyboard

**Sync from personas.json to storyboard.json**:

```python
from video_gen_tools import PersonaManager

manager = PersonaManager(project_dir)

# Generate storyboard.json's elements.characters
characters = manager.export_for_storyboard()

# Write to storyboard.json
storyboard["elements"] = {"characters": characters}
```

### Step 2: Auto Generation Mode Selection

**Automatically select generation mode based on project type** (no manual decision needed):

#### Project Type Determination (Phase 1 auto-identification)

| User Intent Keywords | Project Type |
|---------------------|--------------|
| "drama", "story", "narrative" | Fiction/Short Drama |
| "vlog", "travel diary", "life record" | Vlog/Documentary |
| "commercial", "promotional video", "product showcase" | Commercial/Promotional |
| "MV", "music video" | MV Short Film |

#### Decision Tree

**Fiction/Short Drama, MV Short Films**:
```
Fiction content → All shots must generate storyboard image first
                  └── img2video (image-to-video)
                      └── --image: Storyboard image first frame
```

**Vlog/Documentary, Commercial/Promotional (with real materials)**:
```
Real materials → Need first frame control
                 └── img2video (image-to-video)
                     └── --image: User material first frame
```

**Commercial/Promotional (no real materials)**:
```
No materials → Must generate storyboard image first
               └── img2video (image-to-video)
                   └── --image: Storyboard image first frame
```

#### Selection Rules Table

| Project Type | Material Situation | Generation Mode | Description |
|--------------|-------------------|-----------------|-------------|
| Fiction/Short Drama | With/without character reference | **img2video** | Mandatory storyboard image, character consistency via first frame control |
| MV Short Film | With/without character reference | **img2video** | Mandatory storyboard image, music-driven |
| Vlog/Documentary | User's real materials | **img2video** | User material first frame control |
| Commercial/Promotional | Has real materials | **img2video** | Product/company material first frame |
| Commercial/Promotional | No real materials | **img2video** | Mandatory storyboard image |
| No clear type | No materials | **text2video** | Pure text-to-video |

**Core Principles**:
1. **Fiction must generate storyboard images**, then use img2video
2. **Use same mode within one project**, do not mix

### Step 3: Generate Storyboard

**Core Structure**: Storyboard uses `scenes[] → shots[]` two-layer structure.

**Key Design Principles**:
1. Total duration = Target duration (±5s)
2. Single action principle: Maximum 1 action per shot
3. Spatial invariance principle: No spatial environment changes within a shot
4. Concrete description principle: Replace abstract action descriptions with concrete actions
5. All video_prompts must include aspect ratio information
6. Dialogue must be integrated into video_prompt (character + content + emotion + voice)
7. **BGM constraint**: Add "No background music. Natural ambient sound only." at end of video_prompt if `audio.no_bgm = true`

**BGM Constraint Processing**:

Based on `creative.json`'s `bgm.type`, set `audio.no_bgm` for each shot:
- `bgm.type = "ai_generated"` → All shots `audio.no_bgm = true` (BGM by Suno, mixed in post)
- `bgm.type = "user_provided"` → All shots `audio.no_bgm = true` (BGM by user, mixed in post)
- `bgm.type = "none"` → All shots `audio.no_bgm = false` (video model decides)

**When `audio.no_bgm = true`, append to video_prompt**:
```
No background music. Natural ambient sound only.
```

**Example**:
```
# Without BGM constraint (bgm.type = "none")
video_prompt: "A woman sits by the window, gentle smile. Keep 9:16 vertical composition."

# With BGM constraint (bgm.type = "ai_generated" or "user_provided")
video_prompt: "A woman sits by the window, gentle smile. Keep 9:16 vertical composition. No background music. Natural ambient sound only."
```

**Duration Limits (Veo 3.1 Fast)**:

| Shot Type | Suggested Duration | Description |
|-----------|-------------------|-------------|
| Normal shots | 4-6s | Dialogue, daily actions, medium shots |
| Complex motion | 4-8s | Fast motion, action scenes, push/pull shots |
| Static emotion | 6-8s | Close-ups, emotional expression, slow push shots |

**Duration Design Principles**:
- **Duration is designed at storyboard stage**, CLI has no default value
- 720p can use 4/6/8s
- 1080p/4k **must use 8s** (auto-adjusted)

**Resolution Constraints**:
- 720p (default): Can use 4/6/8s
- 1080p/4k: Must use 8s

**Complete Storyboard Specifications**: See [reference/storyboard-spec.md](reference/storyboard-spec.md)
**Prompt Writing Guidelines**: See [reference/prompt-guide.md](reference/prompt-guide.md)

**Process Narration While Generating Storyboard**:

If `creative.narration.type` is not `none`, plan narration segments while generating storyboard:

1. **Read narration info**:
   - `voice_style` → Write to `narration_config.voice_style`
   - `user_text` (if any) → Segment by shot timing points

2. **Design narration copy based on shot content**:
   - Each narration segment corresponds to one shot or a group of consecutive shots
   - Each segment should be speakable in 2-5 seconds (about 30-50 characters)
   - Avoid shots with character dialogue (don't conflict with sync sound)

3. **Plan timing points and write to storyboard.json**:

```json
{
  "narration_config": {
    "voice_style": "gentle female voice"
  },
  "narration_segments": [
    {"segment_id": "narr_1", "overall_time_range": "0-3s", "text": "This is a peaceful afternoon..."},
    {"segment_id": "narr_2", "overall_time_range": "8-11s", "text": "She sits by the window..."}
  ]
}
```

### Step 4: Present to User for Confirmation (Mandatory Step)

**Must have explicit user confirmation before entering Phase 4!**

Display for each shot:
- Scene information
- Generation mode (text2video/img2video)
- video_prompt
- image_prompt (if any)
- frame_path (if any)
- Dialogue
- Duration
- Transition

Provide options: Confirm and Execute / Modify Storyboard / Adjust Narration / Adjust Duration / Change Transition / Cancel

### Phase 3 Outputs

- `storyboard/storyboard.json` — Storyboard script (including generation_mode, frame_path, narration_segments)

---

## Phase 4: Generation Execution

Execute video generation based on storyboard.json.

### Pre-execution Checks

**1. Reference Image Size Check**
- Read each shot's `frame_path` or `reference_images` from storyboard.json
- Detect all image sizes
- Min edge < 720px → Auto-scale up to 1280px
- Max edge > 2048px → Auto-scale down to 2048px

**2. Parameter Validation**
- Read `aspect_ratio` field from storyboard.json
- Set `--audio` parameter based on `audio` configuration

### Execution Rules

1. **First API call executes alone**, confirm success before parallelizing
2. **Maximum 3 concurrent** API generation calls
3. **Real-time update state.json** to record progress
4. **Retry up to 2 times on failure**, then ask user

### Veo 3 Generation Modes

**Important**: All `--prompt` must be written in English for best results.

**Text-to-video (pure creative, no materials)**:
```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --duration 6 \
  --resolution 720p \
  --aspect-ratio {aspect_ratio} \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

**Image-to-video (with first frame material/storyboard image)**:
```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image <image_path> \
  --prompt "The person in the image starts to smile gently" \
  --duration 8 \
  --resolution 1080p \
  --aspect-ratio {aspect_ratio} \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

### API Error Handling and Degradation Strategy

**Strict degradation order** (no arbitrary degradation to text-to-video):

| Degradation Stage | Operation | Description |
|------------------|-----------|-------------|
| **Stage 1: Retry** | Retry up to 2 times | Handle rate limits, network timeouts, etc. |
| **Stage 2: Adjust Prompt** | Simplify description, remove problematic words | Remove "extreme", "blur", etc. that may cause failures |
| **Stage 3: Adjust Reference Image** | Resize to 1280px, convert to JPEG | Only for image-to-video |
| **Stage 4: Degrade to text-to-video** | Only when no reference image | **Fiction/Short Drama not allowed to degrade** |

**Degradation Rules**:
1. **Fiction/Short Drama, MV Short Films**: Mandatory img2video, not allowed to degrade to text2video
2. **Vlog/Documentary, Commercial**: If materials exist, prefer img2video
3. **No materials case**: Only then can use text2video

**Error Type Handling**:

| Error Type | Handling |
|------------|----------|
| **401 Invalid Key** | Tell user to check COMPASS_API_KEY, no retry |
| **402 Insufficient Balance** | Tell user to top up, no retry |
| **429 Rate Limit** | Wait 60s then retry |
| **Network Timeout** | Wait 30s then retry |
| **Generation Failed** | Handle per degradation order |

### Music Generation (Optional)

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output generated/music/bgm.mp3
```

### Narration Generation (Conditional Trigger)

**Trigger Condition**: Read `narration_segments` from `storyboard.json`, trigger if exists.

**Generation Process**:

1. **Read narration_config and narration_segments**
2. **Call TTS for each segment**:

```bash
# Generate each narration segment separately
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "This is a peaceful afternoon..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3

python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text "She sits by the window..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_2.mp3
```

3. **Output file naming**: Named by `segment_id` (`narr_1.mp3`, `narr_2.mp3`...)

**Execution Order**:
```
Video segment generation → Music generation → Narration generation (if any) → Enter Phase 5 Editing
```

### Phase 4 Outputs

- `generated/videos/*.mp4` — Generated video segments
- `generated/frames/*.png` — Generated storyboard images (if any)
- `generated/music/*.mp3` — Generated background music (if any)
- `generated/narration/*.mp3` — Generated narration audio (if any)
- Updated `state.json` — Records generation progress

---

## Phase 5: Editing Output

### Video Concatenation

```bash
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs video1.mp4 video2.mp4 \
  --output final.mp4 \
  --storyboard storyboard/storyboard.json
```

### Audio Protection

Video segments may contain sync sound, sound effects - these must not be lost during concatenation. Silent segments will have silent audio track added automatically to ensure audio-video sync.

### Video Parameter Validation

Automatically check resolution/encoding/frame rate before concatenation, auto-normalize if inconsistent (1080x1920 / H.264 / 24fps).

### Synthesis Process

1. **Concatenate** → Connect in storyboard order (auto-normalize)
2. **Insert narration** → Position narration audio correctly based on `narration_segments` `overall_time_range` (if any)
3. **Transitions** → Add transition effects between shots
4. **Color grading** → Apply overall color grading style
5. **Music mixing** → Mix background music (see Audio Mixing Rules below)
6. **Output** → Generate final video

### Audio Mixing Rules

**Core Principle**: FFmpeg `amix` filter **must use `normalize=0`** to prevent auto-normalization that reduces volume.

**Volume Recommendations** (adjust flexibly based on video type):

| Audio Type | Recommended Volume | Description |
|------------|-------------------|-------------|
| Video ambient/sync sound | 0.8 | Preserve original audio atmosphere |
| Narration/voiceover | 1.5-2.0 | Ensure voice clarity |
| Background music (BGM) | 0.1-0.15 | Supportive background role |

**Video Type Adjustments**:

| Video Type | BGM Volume | Reason |
|------------|-----------|--------|
| Vlog/Documentary | 0.1-0.15 | Narration is primary |
| Cinematic/Fiction | 0.2-0.3 | Music enhances mood |
| Music Video (MV) | 0.5-0.7 | Music is core element |
| Commercial | 0.15-0.25 | Balance product info and music |

**FFmpeg amix Syntax**:
```bash
# Key: normalize=0 preserves original volume ratios
"[track1][track2]amix=inputs=2:duration=first:normalize=0[out]"
```

**Implementation Note**: `video_gen_editor.py` `mix_audio()` function has `normalize=0` hardcoded (line ~470).

### Music Mixing

Mix background music with proper volume control based on video type. Always use `normalize=0` to preserve intended volume ratios.

### Narration Insertion (Conditional Trigger)

- `output/final.mp4` — Final video

**Trigger Condition**: Read `narration_segments` from `storyboard.json`, trigger if exists.

**Insertion Method**: Use FFmpeg to insert narration audio at specified time points.

```bash
# Insert narration based on overall_time_range
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py narration \
  --video concat_output.mp4 \
  --storyboard storyboard/storyboard.json \
  --narration-dir generated/narration \
  --output with_narration.mp4
```

**Timing Point Calculation**:
- `overall_time_range` format: `"0-3s"` means starting at 0 seconds, lasting until 3 seconds
- Narration audio is inserted at `overall_time_range` start time
- Multiple narration segments are overlaid in time order

### Phase 5 Outputs

- `output/final.mp4` — Final video

---

## Tool Call Quick Reference

**Important**: All `--prompt` must be written in English.

```bash
# Environment check
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py check

# Text-to-video (read aspect_ratio from storyboard.json)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --prompt "A woman sitting by a coffee shop window with a gentle smile" \
  --duration 6 \
  --resolution 720p \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output <output>

# Image-to-video
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py video \
  --image <image_path> \
  --prompt "The person in the image starts to smile gently" \
  --duration 8 \
  --resolution 1080p \
  --storyboard storyboard/storyboard.json \
  --audio \
  --output <output>

# Image generation (storyboard image, read aspect_ratio from storyboard.json)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py image \
  --prompt "Cinematic start frame. A woman sitting by a window, warm lighting, cinematic look, 9:16 aspect ratio" \
  --storyboard storyboard/storyboard.json \
  --output <output>

# Music (pass --creative to read from creative.json)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py music \
  --creative creative/creative.json \
  --output <output>

# Narration (call per narration_segment)
python ~/.claude/skills/video-gen-veo3/video_gen_tools.py tts \
  --text <segment_copy> \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3

# Editing (pass --storyboard)
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py concat \
  --inputs <video_list> \
  --output <output> \
  --storyboard storyboard/storyboard.json

# Narration insertion (insert based on overall_time_range)
python ~/.claude/skills/video-gen-veo3/video_gen_editor.py narration \
  --video <video> \
  --storyboard storyboard/storyboard.json \
  --narration-dir generated/narration \
  --output <output>
```

---

## File Structure

```
~/video-gen-projects/{project_name}_{timestamp}/
├── state.json           # Project status
├── materials/           # Original materials
│   └── personas/        # Character reference images (Phase 2 generated)
├── analysis/
│   └── analysis.json    # Material analysis
├── creative/
│   ├── creative.json    # Creative plan
│   └── decision_log.json # Decision record
├── storyboard/
│   └ storyboard.json   # Storyboard script (including narration_segments)
├── generated/
│   ├── frames/          # Generated storyboard images
│   ├── videos/          # Generated videos
│   ├── music/           # Generated music
│   └── narration/       # Generated narration audio
└── output/
    └── final.mp4        # Final video
```

---

## Error Handling

| Issue | Handling |
|-------|----------|
| Visual analysis failed | Ask user to describe material content |
| API key not configured | Ask when first calling |
| API call failed | Retry 2 times → Ask user |
| Video generation failed | Try adjusting parameters or use original materials |
| Music generation failed | Generate silent video and notify |

---

## Dependencies

- FFmpeg 6.0+
- Python 3.9+
- httpx
- google-genai (Veo 3 SDK)
- PIL (optional, for image size processing)