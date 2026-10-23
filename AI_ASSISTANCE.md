# LLM assistance disclosure

This project was developed with substantial assistance from **OpenAI Codex**, an
LLM-based coding assistant, in collaboration with the keyboard owner. It should
not be described as wholly human-written software.

## What the LLM contributed

The assistant generated or revised the Python driver and CLI, shell installers,
systemd integration, protocol interpretation, test code, fixtures extracted from
published reports, and project documentation. It also operated development tools
and analysed command responses from the attached keyboard.

The owner supplied the goal, preferences, hardware access, visual observations
and corrections. In particular, feedback exposed incorrect profile targeting
and unsuitable F2/F3 overrides during development. Those problems were corrected
and regression checks were added. Hardware responses and passing tests were not
treated as substitutes for the owner's visual assessment.

## Evidence and limits

Protocol work uses publicly linked USB captures and observations from one
original NZXT Function MiniTKL (`1e71:2105`). Tests include sanitized independent
lighting reports, mocked failures, profile-addressing regressions, theme changes
and readbacks. Their existence is not a claim of independent human code review,
complete protocol knowledge, or support for untested hardware.

The runtime is a local Python/HID tool. It does not call an LLM service or require
model credentials. LLM involvement concerns development, not operation.

## Sharing and upstream contributions

Any issue, merge request or other proposed upstream contribution derived from
this work should explicitly disclose its substantial LLM assistance and link to
this document. Do not imply that the implementation was independently written
or fully reviewed by a human when that has not happened.

OpenRGB's current contribution guidelines generally do not permit AI-generated
submissions and require developers to understand and manually vet AI-assisted
work. That restriction must be respected; this repository is not evidence of
upstream approval. No OpenRGB issue comment or merge request has been submitted
by this project. Protocol observations can be offered transparently for human
review, subject to the maintainers' policy.
