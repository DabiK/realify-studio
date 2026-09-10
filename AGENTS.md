# Realify Studio

Read `docs/PRODUCT.md` before product changes. For Realify work also read `docs/CHANNEL.md`.

The product is a generic multi-project React app for desktop and mobile browsers. Only the Realify project is restricted to One Piece. The user wants automatic next-post generation, image feedback and corrections (including adding text), an optimized title/description/hashtags sheet, phone downloads, Mac first then VPS, and existing Codex subscription only. No A/B testing or experiments. Do not add a paid image API fallback. Do not publish to TikTok; marking published is a local bookkeeping action.

Sources are private TikTok CSV exports in `data/source`. Rebuild derived analytics with `python3 scripts/analyze.py`. Never infer a post's visual format or attribute a daily spike using caption/date alone. Never sum daily viewers as annual unique people.

Keep runtime databases, generated images, auth/session credentials, and Codex logs out of Git. The parent directory is a historical media archive; do not move or edit it.

User flow should show ready packs, short correction controls, downloads, and evidence. Hide model and prompt plumbing behind the workflow. Preserve old image versions. Always distinguish live generation from archived examples and fake-provider tests.
