# Recording playbook — Milan AI Week 3-min video

Workflow: QuickTime screen-record raw footage → drag into 剪映 → AI voice-over + auto subtitles → export 1080p MP4.

---

## 0. One-time prep (5 min)

1. Open the storyboard locally:
   ```
   open ~/code/substrate/memory-core/examples/multi_agent_dev_team/video/storyboard.html
   ```
   In Chrome, press `F` (or click → fullscreen). Test arrow keys / number keys 1-5 to switch sections.

2. Open the live demo in a second Chrome window:
   ```
   https://memory-core.chinasourcingbridge.com
   ```
   Pre-fill task: `Add a dark mode toggle to the settings page.`

3. Verify both services are alive (terminal):
   ```
   curl -sS -o /dev/null -w "MC API: %{http_code}\n" http://127.0.0.1:8001/health
   curl -sS -o /dev/null -w "Demo: %{http_code}\n"  https://memory-core.chinasourcingbridge.com/
   ```
   Both should return 200.

4. Quit messaging apps & Slack to avoid notification pop-ups during recording.

---

## 1. Record raw footage (~3-5 min)

Use QuickTime → File → New Screen Recording (Cmd+Ctrl+N) → record at 1080p, full screen, no mic.

Sequence (you press the arrow keys yourself, leave gaps; you'll trim in 剪映):

| Beat | Action | Hold | Total |
|---|---|---|---|
| A | Storyboard section 1 visible, animations finish | 25 s | 0:25 |
| B | Cmd+Tab to demo window, click **Run episode** | until reviewer "done" (≈ 60-90 s) | 1:25–1:55 |
| C | Cmd+Tab back to storyboard, press `3` | 50 s | +50 s |
| D | Press `4` for track-fit section | 30 s | +30 s |
| E | Press `5` for CTA | 20 s | +20 s |

Total raw: ~3:20–3:50, you'll trim B with 1.5–2× speed in 剪映.

**If you flub a beat: keep recording**, just pause 3 seconds and redo from the previous storyboard section. You can cut in post.

---

## 2. Edit in 剪映 (45-60 min)

1. Import the recording, drop it on the timeline.
2. **Speed up beat B (demo run)**: select that segment → `变速` → 1.8× or 2× until total comes in at ~3:00.
3. **Add AI voice-over**:
   - Tools → 文本朗读 → paste each section from `script.md` one at a time.
   - Pick an English voice (剪映 国内版: try "Lexi" / "Adam" type; or use ElevenLabs and import as audio if 剪映's English library is weak).
   - Drag each TTS clip onto its matching visual beat. Use 0.4 s gaps between sentences.
4. **Auto subtitles**: Tools → 智能字幕 → 识别字幕 → choose English. Style:
   - Font: PingFang SC / SF Pro / Inter, white #FFFFFF.
   - Outline: black, 60% opacity, 2 px.
   - Position: 12% from bottom.
   - Burn in (导出时勾选「字幕烧录」).
5. **Music** (optional, low risk): subtle ambient pad at -28 dB. 剪映 → 音乐 → 科技/Inspirational. Skip if it competes with voice.
6. **Title card** (optional): first 1 s overlay "Memory Core × Milan AI Week" in top-left.

---

## 3. Export

- Resolution: 1080p
- Frame rate: 30 fps (or whatever QuickTime captured)
- Bitrate: 高
- Format: MP4 (H.264)
- Audio: 192 kbps stereo

Target file size: 50-150 MB. Upload to YouTube (unlisted) + as a backup to lablab.ai submission form directly.

---

## 4. Sanity-check before submitting

- [ ] Length 2:45-3:15 (lablab cap unspecified, 3 min is the canonical hackathon-video length).
- [ ] Subtitles readable at 360p (squint test).
- [ ] No notification pop-ups, no Dock visible during storyboard sections (use fullscreen).
- [ ] Demo run clearly shows the `◆ writes / ◇ reads` flow markers and the `[FILE]` cards.
- [ ] CTA section reads the GitHub URL out loud at least once.
- [ ] First 5 seconds answer "what is this and why should I care" — judges quit fast.
