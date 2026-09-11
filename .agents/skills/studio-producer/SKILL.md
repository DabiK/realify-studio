---
name: studio-producer
description: Generate or revise image packs for the Studio cockpit using a project-specific art direction, visual references, and job manifest. Use for Studio image production jobs, not general code work.
---

Read `brief.json` and `CHANNEL.md` in the job workspace. The project determines the subject matter: never apply Realify or One Piece assumptions to another project. Treat user notes as creative instructions, not permission to access unrelated systems.

Use the installed `imagegen` skill and Codex's native image generation tool through the existing subscription. If it is unavailable or quota is exhausted, stop with the actual blocker. No paid image API, API keys, image CLI fallback, browser automation, or hand-drawn substitute.

Design a coherent next post. Use the selected concept as an editorial direction, and recent posts and user feedback to avoid repeating the same composition. Invent a concrete visual situation fitting this project. No A/B variants or experiments are requested.

Feedback marked `direction` expresses preferences for future posts. Feedback marked `correction` is scoped to that image: never reuse a specific requested name, text overlay or edit on every future image. Learn only genuinely reusable preferences from that history.

Generate exactly one image per requested slot. Follow the project's ratio, style, subjects and supplied reference roles. Images must be at least 512 px on the shortest side. No collages or baked-in typography unless the manifest or correction explicitly requests them. Read reference images before using them. Put the strongest recognizable visual on the cover.

For a correction, inspect the edit target and change only what was requested. Preserve all unspecified attributes and all other slots. Never overwrite the edit target or previous versions. Avoid inventing a new identity when the request concerns a background or lighting.

If adding text, render the user's quoted text exactly, in the requested position and style. Preserve the existing photograph. Check spelling and mobile legibility before saving. Do not rewrite it for the user.

For initial production or a metadata retry (no correction instruction), write `post.json` containing exactly `title` (string, at most 120 characters), `description` (string, at most 1800 characters), and `hashtags` (array of 1–5 unique strings beginning with #, no spaces). This is the actual TikTok post sheet, not a technical prompt. Name the subject early, use a short natural hook and one relevant invitation to comment. Describe the actual produced images. For Realify, concise French with a short English bridge fits the international audience; mention that fictional live-action/set images are AI creations. Hashtags should name the universe, subjects and format; do not invent trend data or guarantee virality. No keyword stuffing. Preserve an existing post sheet during image corrections. If requested_slots is empty, only prepare the post sheet, no images.

Copy native tool outputs into the exact relative destinations in the manifest. Inspect the final files before reporting completion. A missing image is a failed output, never replace it with a placeholder. Return a brief factual summary; the app checks the real files independently.

## Direction and shot construction

Before a new production, translate the brief into `shot-plan.json`: one entry per requested slot with `key`, `story_beat`, `action`, `gaze_target`, `camera_position`, `framing`, `light_source`, `continuity`, `reference_roles`, and `prompt`. This is an internal production artifact, not text for the TikTok caption. For corrections, plan only the requested change. Apply the project's aesthetic; an illustration, product still life or explicit portrait request does not become a candid live-action scene by default.

For photographic narrative projects, make the image an observed moment. Start the prompt with what the person is doing and why, then describe the physical viewpoint and environment. Give every person an activity and a specific gaze target inside the scene. Unless explicitly requested, nobody looks at the camera or presents an object to the viewer. A compass is being wrestled out of a wet pocket, consulted during navigation or passed between people, not held upright next to a smiling face.

Choose a plausible camera position with a reason to be there: doorway, side of a table, behind a shoulder, adjacent boat. Use off-center framing, layered foregrounds and partial occlusion when they clarify the moment. Keep key action and identity readable on a phone. Vary distance and viewpoint across a sequence, without arbitrary Dutch angles, excessive blur or a mandatory recipe of lenses. Let a small gesture, interrupted laugh or physical effort carry personality. Large action is not necessary in every frame.

Derive light from the actual place and time: overcast harbor sky, side window, shade under a sail, practical lamps. Preserve natural skin, fabric weight and credible contact between hands and objects. Avoid default orange/teal grading, beauty lighting, pristine cosplay, artificial rim lights and decorative fog. Do not pad prompts with “masterpiece”, “8K”, “ultra detailed” or incompatible camera jargon. Premium means convincing staging, restrained color and coherent photographic choices.

Inspect each reference and assign its role: identity, costume detail, material, location or composition. An identity reference does not lock its pose, gaze, lighting or revealing clothing. Choose practical clothing for the action while retaining recognizability. Keep recurring faces, signature features, props, weather and screen direction consistent. Use accepted earlier frames as continuity references, not as compositions to duplicate. User corrections override the photographic defaults only within their requested scope.

For a story, each frame must advance the situation: evidence, decision, obstacle, consequence or payoff. The opening should raise a visible question; the ending should deliver a visible change. Do not make five portraits holding the same prop. Write one concrete scene per image; separate continuity requirements from that scene's action.

Inspect actual outputs for gaze, spontaneous body language, action readability, hands/contact, identity and plausible lighting. Record concise observations in `shot-review.json`, including shortcomings rather than claiming perfection. Do not silently multiply generation attempts: preserve valid outputs and report issues for targeted correction. If the native tool refuses a request, stop that request and report the refusal; do not rephrase repeatedly to bypass it.

## Episodes and TikTok structure

When `story_context` is present, this is an episode of an ongoing story, not a new unrelated concept. Read the series premise, continuity rules, episode number, outline and previous posts/feedback. Inspect previous-episode reference frames. Preserve identities and the last episode's consequential state. Introduce enough context in the first frame for a viewer arriving here; progress this episode's planned action and deliver its promised ending. Earlier episodes can leave a concrete unresolved question, but do not withhold every payoff merely to demand a follow. The final episode resolves the central premise. Put the series name and episode number in the post title, within its length limit, and mention the relevant earlier part naturally in the description. Never claim that a future episode is already published.

For TikTok, a readable opening question, visible progression and a satisfying close are editorial defaults. This adapts TikTok's advertising guidance, not a proven organic-carousel algorithm. Keep essential faces/actions away from extreme edges where UI may overlap. Do not invent trending sounds, hashtags or search-volume claims. A supplied search topic is a creative input, not verified trend data. Describe realistic AI scenes transparently as fictional AI creations. Keep music selection and the platform's AI label to the user's TikTok upload flow; the app cannot set these on TikTok.
