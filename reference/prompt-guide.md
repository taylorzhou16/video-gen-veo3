# Veo 3 Prompt Writing Guidelines

## Table of Contents

- **Important Rules**
- Basic Concepts
- Text-to-video Prompt
- Image-to-video Prompt
- image_prompt (Storyboard Image Generation)
- Two-stage Process (Fiction)
- Consistency Standards
- Aspect Ratio Constraints
- Dialogue and Audio
- Appendix: Quick Templates

---

## Important Rules

**All video_prompt and image_prompt must be written in English.**

Veo 3.1 Fast understands English prompts more accurately and produces higher quality results.

**But dialogue content should match the character's language context**:
- For English-speaking characters: use English dialogue
- For non-English contexts: dialogue can be in the appropriate language, but the prompt wrapper should still be in English
- Example for multilingual scenarios: The character says, "[dialogue in character's language]"

**Example**:
```
The female lead (a 25-year-old Asian woman with long black hair) looks up with a gentle smile and says, "It's really quiet here, I like it." Clear voice, moderate pace.
```

---

## Basic Concepts

### Veo 3 Capabilities Comparison

| Feature | Veo 3.1 Fast | Kling-3.0 | Vidu Q3 Pro |
|---------|--------------|-----------|-------------|
| Text-to-video | ✅ | ✅ | ✅ |
| Image-to-video | ✅ | ✅ | ✅ |
| Automatic Audio | ✅ Native support | ✅ | ✅ |
| Reference Images (referenceImages) | ❌ (Only Veo 3.1 supports) | ❌ (Only Omni) | ❌ |
| Multi-shot mode (multi_shot) | ❌ Not supported | ✅ | ❌ |
| First Frame Control | ✅ | ✅ | ✅ |
| Max Duration | 8s | 10s | 8s |
| Max Resolution | 4k | 1080p | 720p |

### Key Differences

**Veo 3.1 Fast vs Kling/Vidu**:
- Veo 3.1 Fast **does not support** reference images (referenceImages, only Veo 3.1 supports), character consistency only through first frame control or detailed text description
- Veo 3.1 Fast **does not support** multi-shot mode (multi_shot), each shot generated independently
- Veo 3.1 Fast has more powerful automatic audio, supports simple dialogue
- Veo 3.1 Fast duration limit: 4/6/8s (1080p/4k must use 8s)
- Veo 3.1 Fast supports higher resolution (4k)

---

## Text-to-video Prompt

### Structure Elements (in order)

1. **Overall Action Summary** — Briefly describe overall shot action
2. **Segmented Actions** — By timeline: 0-2s, 2-5s... (recommended for longer videos)
3. **Subject Description** — Character/object appearance features
4. **Scene/Environment** — Location, time, environment details
5. **Camera Movement** — Push/pull/pan/tilt/track/crane
6. **Style/Atmosphere** — Cinematic, lighting, color tone
7. **Dialogue Information** — Character, content, emotion, speaking rate (if any)
8. **Aspect Ratio Protection** — "Keep XX aspect ratio composition"
9. **BGM Constraint** — Add "No background music. Natural ambient sound only." if `audio.no_bgm = true`

### Basic Template

```
Overall: {Shot overall action description}

Segmented actions ({duration}s):
{time_range_1}: {Action description}
{time_range_2}: {Action description + dialogue sync}
...

Camera: {Camera movement description}
Rhythm: {Movement rhythm}
Stability: {Keep stable/Slight shake}
{Dialogue information}
Keep {aspect ratio} composition, maintain aspect ratio
{BGM constraint}
```

### Complete Example (6-second shot, 720p default configuration)

```
Overall: A woman looks up from her contemplation toward the window, a gentle smile gradually appearing on her face.

Segmented actions (6 seconds):
0-2s: Woman in profile, gazing out the window with a calm expression
2-4s: The corners of her mouth slowly curve upward, her gaze softens
4-6s: She turns fully toward the camera with a natural, gentle smile

Camera: Slow push in, steady
Rhythm: Slow and smooth
Stability: Stable
Dialogue: The woman says gently, "This is my favorite place." Clear voice, moderate pace.
Keep 9:16 vertical composition, subject centered in frame
No background music. Natural ambient sound only.
```

### Concise Template (Short Video)

```
[Subject] + [Action] + [Scene] + [Style] + [Camera] + [Aspect Ratio] + [BGM Constraint]

Example:
A 25-year-old Asian woman with long black hair, wearing a beige knit sweater,
sitting by the window in a cozy coffee shop, slowly opening her eyes with a gentle smile,
warm afternoon sunlight streaming through the large windows, cinematic color grading, shallow depth of field,
slow push in, 9:16 vertical composition, no background music, natural ambient sound only
```

---

## Image-to-video Prompt

### Working Mode

In image-to-video mode:
1. **Image as first frame**: Video starts from this image
2. **Prompt describes motion**: Describes how elements in the image move
3. **Automatically inherits visuals**: Scene, lighting, composition inherited from image

### Prompt Structure

```
[Motion/Action] + [Mood/Atmosphere] + [Camera Movement] + [Aspect Ratio Protection] + [BGM Constraint]
```

### Complete Example

**Input Image**: A female portrait photo

**video_prompt**:
```
The woman in the image slowly opens her eyes, revealing a gentle smile,
warm atmosphere, slight push in, keep 9:16 vertical composition.
No background music. Natural ambient sound only.
```

### Notes

- Prompt focuses on describing **action**, scene automatically inherited from image
- Don't repeat description of static elements already in the image
- Maintain visual coherence when describing motion

---

## image_prompt (Storyboard Image Generation)

Used to generate storyboard images as first frames. **Fiction/Short Drama must generate storyboard images first**.

### Five-element Structure

1. **Scene**: Time, location, environment
2. **Subject**: Character appearance, clothing, posture
3. **Lighting**: Light direction, color temperature, atmosphere
4. **Style**: cinematic / realistic / anime
5. **Ratio**: Vertical 9:16 / Horizontal 16:9 / Square 1:1

### Basic Template

```
Cinematic realistic start frame.

Scene: {Specific scene description}
Location details: {Environment details}

{Character appearance detailed description}, {posture}, {expression}, {position}

Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {Lighting description}
Color grade: {Color tone}
Aspect ratio: {Aspect ratio}

Style: {cinematic realistic/film grain/etc.}
```

### Complete Example

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

## Two-stage Process (Fiction)

**Fiction/Short Drama, MV Short Films must follow two-stage process**:

```
Stage 1: Image Prompt → Generate storyboard image (control scene/style/lighting/atmosphere/color/makeup/costume)
         ↓
Stage 2: Storyboard image as first frame → img2video (Veo 3)
```

### Step 1: Generate Storyboard Image

Use image_prompt to generate storyboard image:

```bash
python video_gen_tools.py image \
  --prompt "Cinematic realistic start frame.
Scene: Cozy coffee shop interior...
A 25-year-old Asian woman with long black hair...
Style: Cinematic realistic, 9:16 aspect ratio" \
  --aspect-ratio 9:16 \
  --output generated/frames/scene1_shot1_frame.png
```

### Step 2: Storyboard Image as First Frame for Video Generation

```bash
python video_gen_tools.py video \
  --image generated/frames/scene1_shot1_frame.png \
  --prompt "The person in the image slowly opens their eyes, revealing a gentle smile. Keep 9:16 vertical composition." \
  --duration 5 \
  --resolution 1080p \
  --aspect-ratio 9:16 \
  --audio \
  --output generated/videos/scene1_shot1.mp4
```

### Cross-shot Character Consistency

Since Veo 3 doesn't support multiple reference images, cross-shot consistency needs:

1. **Character Reference Image**: Used to maintain character appearance consistency when generating storyboard images
2. **Detailed Text Description**: Use same character description in each image_prompt
3. **Storyboard Image First Frame**: Ensures scene and character posture consistency

**Character Consistency Template**:

In each image_prompt containing characters, keep the following description consistent:

```
Character ID: {name}
Appearance features: {gender}, {age}, {hairstyle}, {facial features}, {body type}
Clothing description: {style}, {color}, {material}, {accessories}
Signature features: {Special marks, habitual gestures, etc.}
```

**Example**:
```
Xiaomei, 25-year-old Asian female, long straight black hair to waist, oval face, large eyes,
wearing white shirt and jeans, wearing thin silver necklace,
habitually tucks hair behind ear
```

---

## Consistency Standards

### Within Single Shot

- Keep subject feature description consistent
- Keep scene description consistent
- Keep style description consistent

### Cross-shot Consistency (Veo 3 Limitation)

Veo 3 doesn't support multiple reference images, cross-shot consistency needs:

1. **Storyboard image first frame**: First generate storyboard image, then use as first frame for video generation
2. **Detailed text description**: Use same character description in each shot
3. **Character reference image**: Used to maintain character appearance when generating storyboard images

---

## Aspect Ratio Constraints

### Aspect Ratios

| Ratio | Platform | Description |
|-------|----------|-------------|
| 9:16 | TikTok/Xiaohongshu | "Vertical composition, 9:16 aspect ratio, character/subject centered in frame" |
| 16:9 | Bilibili/YouTube | "Horizontal composition, 16:9 aspect ratio" |
| 1:1 | Instagram | "Square composition, 1:1 aspect ratio, subject centered" |

### CLI Parameters

```bash
# Pass via --aspect-ratio parameter
python video_gen_tools.py video --prompt "..." --aspect-ratio 9:16
```

**Important**: `aspect_ratio` is read from `storyboard.json`, all video generation must pass this parameter.

---

## Dialogue and Audio

### Veo 3 Automatic Audio

Veo 3 automatically generates the following audio:
- **Ambient Sounds**: Wind, rain, street noise, coffee shop background, etc.
- **Sound Effects**: Footsteps, door opening, object collisions, etc.
- **Simple Dialogue**: Basic voice content

### Dialogue Integration in Prompt

When a shot contains dialogue, **must fully describe in video_prompt**: character (including appearance), dialogue content (in quotes, **keep character's original language**), expression/emotion, voice quality and speaking rate.

**Prompt in English, dialogue keeps character language**:

```
The female lead (a 25-year-old Asian woman with long black hair) looks up at the server,
smiling gently and says, "It's really quiet here, I like it."
Clear, pleasant voice, moderate pace.
```

### audio Field and API Mapping

| Storyboard Field | API Parameter | Description |
|-----------------|---------------|-------------|
| `audio.enabled = true` | `--audio` | Generate ambient sound/dialogue |
| `audio.enabled = false` | No `--audio` | Silent output |
| `audio.no_bgm = true` | Add constraint to prompt | Add "No background music. Natural ambient sound only." |
| `audio.no_bgm = false` | No constraint | Video model decides freely |

### BGM Constraints

BGM is mixed in post-production (Suno generated or user provided), not generated during video generation.

**When `audio.no_bgm = true`, must add the following at the end of video_prompt**:
```
No background music. Natural ambient sound only.
```

**Decision Logic (based on `creative.json`'s `bgm.type`)**:
- `bgm.type = "ai_generated"` → All shots `no_bgm = true` (BGM by Suno, mixed in post)
- `bgm.type = "user_provided"` → All shots `no_bgm = true` (BGM by user, mixed in post)
- `bgm.type = "none"` → All shots `no_bgm = false` (video model decides)

**Note**: Do not separately write Sound effects, let the model automatically generate ambient sounds based on the scene (e.g., car engine sounds, keyboard typing, wind, etc.).

---

## TTS Narration Generation

**Trigger Condition**: `storyboard.json` has `narration_segments` field.

**Data Sources**:
- `narration_config.voice_style` → Maps to TTS voice and emotion parameters
- `narration_segments[].text` → TTS --text parameter
- `narration_segments[].segment_id` → Output file naming

**CLI Call Example**:

```bash
# Generate each narration segment separately
python video_gen_tools.py tts \
  --text "This is a peaceful afternoon, sunlight streams through the floor-to-ceiling windows into the coffee shop..." \
  --voice female_narrator \
  --emotion gentle \
  --output generated/narration/narr_1.mp3
```

**voice Parameter (Volcano Engine TTS Voices)**:

| Parameter Value | Voice Description | Volcano Engine ID |
|----------------|-------------------|-------------------|
| `female_narrator` | Female narrator, professional and steady | BV700_streaming |
| `female_gentle` | Female voice gentle, soft and friendly | BV034_streaming |
| `male_narrator` | Male narrator, professional and steady | BV701_streaming |
| `male_warm` | Male voice warm, magnetic and friendly | BV033_streaming |

**emotion Parameter (Optional)**:

| Parameter Value | Emotion Style |
|-----------------|---------------|
| `neutral` | Neutral (default) |
| `happy` | Happy |
| `sad` | Sad |
| `gentle` | Gentle |
| `serious` | Serious |

**voice_style to TTS Parameter Mapping**:

User-specified voice_style in Phase 2 (e.g. "gentle female voice") maps to specific TTS parameters in Phase 3:
- "gentle female voice" → `voice: female_gentle, emotion: gentle`
- "professional female narrator" → `voice: female_narrator, emotion: neutral`
- "warm male voice" → `voice: male_warm, emotion: neutral`
- "serious male voice" → `voice: male_narrator, emotion: serious`

**Important**: Use the same voice + emotion parameters within one video to maintain consistent narration style.

---

## Appendix: Quick Templates

### Text-to-video Template (Complete)

```
Overall: {Shot overall action description}

Segmented actions ({duration}s):
{time_range_1}: {Action description}
{time_range_2}: {Action description + dialogue sync}

Camera: {Camera movement description}
Rhythm: {Movement rhythm}
Stability: {stable/slight shake}
{Dialogue information}
Keep {aspect ratio} composition, maintain aspect ratio
```

### Text-to-video Template (Concise)

```
[Subject] + [Action] + [Scene] + [Style] + [Camera] + [Aspect Ratio]
```

### Image-to-video Template

```
[Motion/Action] + [Atmosphere] + [Camera] + [Aspect Ratio Protection]

Example:
The woman in the image slowly opens her eyes with a gentle smile,
warm atmosphere, slight push in, keep 9:16 vertical composition
```

### image_prompt Template (Storyboard Image)

```
Cinematic realistic start frame.

Scene: {Scene description}
Location details: {Environment details}

{Character appearance description}, {posture}, {expression}, {position}

Shot scale: {wide/medium/close-up}
Camera angle: {eye-level/high/low}
Lighting: {Lighting description}
Color grade: {Color tone}
Aspect ratio: {Aspect ratio}

Style: Cinematic realistic, film grain, shallow depth of field
```

### Two-stage Process Example

```
# Step 1: Generate storyboard image
image_prompt = "Cinematic start frame. A 25-year-old Asian woman with long black hair..."

# Step 2: Storyboard image as first frame
video_prompt = "The person in the image slowly opens their eyes..."
```