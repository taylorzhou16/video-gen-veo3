# Veo 3 Backend Guide

## Table of Contents

- Veo 3.1 Fast Capabilities Overview
- Project Type and Generation Mode
- Generation Mode Selection
- Two-stage Process (Fiction/Short Drama)
- Prompt Writing Suggestions
- Error Handling

---

## Veo 3.1 Fast Capabilities Overview

| Feature | Input | Output | Duration | Resolution |
|---------|-------|--------|----------|------------|
| **Text-to-video + Audio** | Text prompt | Video + Audio | 3-60s | 720p, 1080p, 4k |
| **Image-to-video + Audio** | Image + Text prompt | Video + Audio | 3-60s | 720p, 1080p, 4k |
| **Text-to-video (no audio)** | Text prompt | Video | 3-60s | 720p, 1080p, 4k |
| **Image-to-video (no audio)** | Image + Text prompt | Video | 3-60s | 720p, 1080p, 4k |

**Key Features**:
- **Automatic Audio Generation**: Veo 3 automatically generates ambient sounds, sound effects, simple dialogue
- **Image-to-video**: Supports image as starting frame
- **High Resolution**: Supports 720p, 1080p, 4k output
- **Long Duration**: Supports 3-60 second videos

**Note**: Veo 3 doesn't support multiple reference images (image_list) or multi-shot (multi_shot) features.

---

## Project Type and Generation Mode

### Project Type Determination

| User Intent Keywords | Project Type |
|---------------------|--------------|
| "drama", "story", "narrative" | Fiction/Short Drama |
| "vlog", "travel diary", "life record" | Vlog/Documentary |
| "commercial", "promotional video", "product showcase" | Commercial/Promotional |
| "MV", "music video" | MV Short Film |

### Generation Mode Selection

| Project Type | Material Situation | Generation Mode | Description |
|--------------|-------------------|-----------------|-------------|
| **Fiction/Short Drama** | With/without character reference | **img2video** | Mandatory storyboard image, character consistency via first frame control |
| **MV Short Film** | With/without character reference | **img2video** | Mandatory storyboard image, music-driven |
| **Vlog/Documentary** | User's real materials | **img2video** | User material first frame control |
| **Commercial/Promotional** | Has real materials | **img2video** | Product/company material first frame |
| **Commercial/Promotional** | No real materials | **img2video** | Mandatory storyboard image |
| No clear type | No materials | **text2video** | Pure text-to-video |

---

## Generation Mode Selection

### Decision Tree

```
Have material images?
├── Yes → Image-to-video mode
│         └── python video_gen_tools.py video --image <image> --prompt <description> --audio
│
└── No → Text-to-video mode
          └── python video_gen_tools.py video --prompt <description> --audio
```

### Scenario Quick Reference

| Scenario | Mode | Command Example |
|----------|------|-----------------|
| **Fiction/Short Drama** | img2video (storyboard image first) | Generate storyboard image → `--image frame.png --prompt "action description" --audio` |
| **Vlog/Documentary** | img2video (user materials) | `--image user_photo.jpg --prompt "action description" --audio` |
| **Pure Creative Generation** | text2video | `--prompt "A cat napping in the sunlight" --audio` |
| **Need Highest Quality** | 4k text-to-video | `--resolution 4k --prompt "..." --audio` |

---

## Two-stage Process (Fiction/Short Drama)

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
  --prompt "Cinematic realistic start frame.\nScene: Cozy coffee shop...\nLighting: Warm lighting...\nAspect ratio: 9:16" \
  --aspect-ratio 9:16 \
  --output generated/frames/scene1_shot1_frame.png
```

**image_prompt Elements**:
- Scene description
- Character appearance, clothing, posture
- Lighting atmosphere
- Camera parameters
- **Aspect ratio**

See [prompt-guide.md](prompt-guide.md) for image_prompt template details.

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

---

## Prompt Writing Suggestions

### Text-to-video Prompt Structure

```
[Subject description] + [Action/Motion] + [Scene/Environment] + [Style/Atmosphere] + [Camera language]
```

**Example**:
```
A 25-year-old Asian woman, long straight black hair, wearing a beige knit sweater,
sitting by the window in a cozy coffee shop, slowly opening her eyes with a gentle smile,
warm afternoon sunlight streaming through the floor-to-ceiling windows, cinematic color grading, shallow depth of field,
camera slowly pushing in, 9:16 vertical composition
```

### Image-to-video Prompt Structure

```
[Action] + [Atmosphere] + [Camera] + [Aspect Ratio Protection]
```

**Example**:
```
The person in the image slowly opens their eyes, revealing a gentle smile,
warm atmosphere, slight push in, keep 9:16 vertical composition
```

### Audio Generation

Veo 3 automatically generates audio, including:
- **Ambient Sounds**: Wind, rain, street noise, etc.
- **Sound Effects**: Footsteps, door opening, object collisions, etc.
- **Simple Dialogue**: Basic voice content

**Note**: For complex dialogue or specific lines, recommend using TTS dubbing in post-production.

---

## Error Handling

### API Error Codes

| Error Code | Meaning | Handling |
|------------|---------|----------|
| **401** | Invalid API Key | Check COMPASS_API_KEY configuration |
| **402** | Insufficient Balance | Remind user to top up |
| **429** | Rate Limit | Wait 60 seconds then retry |
| **500** | Server Error | Retry 2 times, then ask user if failed |

### Task Timeout

Veo 3 generation may take 1-5 minutes, depending on video length and resolution.
- Default timeout: 600 seconds (10 minutes)
- Long videos (30s+) recommend reserving more time

### Generation Failed

If generation fails:
1. Check if prompt is too complex or contains sensitive content
2. Try simplifying prompt or lowering resolution
3. Contact user to confirm if creative direction needs adjustment