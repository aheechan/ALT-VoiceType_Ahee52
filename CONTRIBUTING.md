# Contributing

Thanks for taking the time to contribute.

## License of contributions

This repository is released under **Apache-2.0** (see `LICENSE` and `NOTICE`).

By submitting a pull request, patch, or any other contribution, you agree that
your contribution is licensed under the same license as this repository
(inbound = outbound). You keep your copyright; you do not transfer it.

If you cannot agree to this, please open an issue first instead of sending code.

## Practical guidelines

- Keep changes focused; one topic per pull request.
- Match the existing style and keep both README languages in sync.
- New third-party components must be recorded in `NOTICE` and
  `THIRD_PARTY-MODELS.md` with their license.
- Do not add dependencies that are incompatible with Apache-2.0.
- Run the project's self-checks before submitting.

## FFmpeg note

Installers bundle a GPL-enabled FFmpeg build. If your change adds or replaces
FFmpeg binaries, update `NOTICE` and keep the GPL source offer accurate.
