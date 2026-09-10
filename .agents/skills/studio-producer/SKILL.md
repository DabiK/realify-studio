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
