# Potential OpenRGB contribution

**Development disclosure:** this work was substantially generated or revised
with the OpenAI Codex LLM assistant. See [AI_ASSISTANCE.md](../AI_ASSISTANCE.md).
That fact must be disclosed explicitly in any potential upstream contribution;
these notes are not a claim of independent human authorship or review.

## Existing upstream work

The open device ticket is
[Function Tenkeyless #2395](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/2395).
It contains the annotated USB captures used for this work.

The current upstream controller tree has no dedicated Function keyboard
controller. Its
[NZXT Lift controller](https://gitlab.com/CalcProgrammer1/OpenRGB/-/tree/master/Controllers/NZXTMouseController)
already uses the `0x43` vendor protocol and a detector constrained by interface,
usage page `0xffca` and usage 1. It registers PID `0x2100`, not this keyboard.
Adding a keyboard PID to the mouse driver would not provide keyboard support.

## Useful evidence from this project

- Physical MiniTKL `1e71:2105`, vendor HID interface 1 and exact report descriptor.
- Static and off commands, active-profile addressing and native reactive reports.
- `0x44` reads the active FN profile index, confirmed with physical key presses.
- `0x31`/`0x38` read base/reactive definitions; they do not clear them.
- Acknowledgement success is one byte. Treating `01 03` as a 16-bit error
  incorrectly rejects a successful operation targeting profile 4.
- Sanitized report fixtures, bounded response handling and physical readbacks.

An initial upstream driver could focus on verified static/off lighting for this
PID, then add native modes after physical testing. It should use OpenRGB's
existing RGBController and HID detection interfaces. Our personal F1/F4 policy,
theme-file integration and systemd watcher belong in the standalone tool rather
than in a generic OpenRGB controller. Per-key layout support needs separate
verification; do not infer it from the whole-keyboard mask.

## Upstream process

Read [CONTRIBUTING.md](https://gitlab.com/CalcProgrammer1/OpenRGB/-/blob/master/CONTRIBUTING.md)
before preparing an upstream change. Keep it to one functional area and test on
physical hardware. Their current policy generally disallows AI-generated
submissions and expects developers to fully understand and manually vet any
AI-assisted work. This evidence note is a handoff for human review, not an
automatically submitted issue or merge request. Any proposal must disclose the
LLM involvement and respect the maintainers' decision about eligibility. Nothing
has been posted upstream.
