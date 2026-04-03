# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0b1] - 2026-04-03

### Added
- `AWSSettingsConfigDict` — extends pydantic-settings' `SettingsConfigDict` with typed, autocomplete-friendly keys for all AWS-specific configuration (`secrets_name`, `secrets_client`, `ssm_client`, `aws_region`, etc.)
- Thread-safe boto3 client cache using `threading.Lock`, safe for free-threaded (no-GIL) Python builds
- Thread safety tests and free-threaded build detection test
- Free-threaded Python support: `3.13t` and `3.14t` added to CI matrix
- Agent skill file at `pydantic_settings_aws/.agents/skills/SKILL.md` for LLM agent discoverability
- `SECURITY.md` with vulnerability reporting instructions
- `CITATION.cff` for academic citation
- Separate `docs.yml` GitHub Actions workflow with manual trigger (`workflow_dispatch`) and path-based auto-deploy
- Explicit least-privilege permissions on all CI workflows

### Changed
- Dropped support for Python 3.8 and 3.9
- Minimum Python version is now 3.10
- `PythonVersionDeprecationWarning` now targets Python 3.10 (end-of-life October 2026)
- Replaced bare exception re-raises with `raise` to preserve tracebacks
- Fixed `AwsSession.session_key()` to access `model_fields` from the class, not the instance (fixes `PydanticDeprecatedSince211` warning)
- Pinned `pydantic < 3.0.0` to prevent accidental upgrade to an incompatible major version
- Updated all documentation and examples to use `AWSSettingsConfigDict`
- Upgraded CI actions to v6
- Ruff `target-version` updated from `py38` to `py310`

### Fixed
- Removed `print(key)` debug statement from `AwsSession.session_key()`
- Fixed log message typo: "caugth" → "caught"

## [0.1.2] - 2026-01-17

### Added
- Deprecation warning (`PythonVersionDeprecationWarning`) for Python 3.8 and 3.9, announcing their removal in a future version
- Support for Python 3.13 and 3.14 in CI matrix

## [0.1.1] - 2026-01-17

### Security
- Removed retrieved secret values from debug and info logs to prevent accidental secret exposure

## [0.1.0] - 2024-07-27

### Added
- `AWSBaseSettings` — load settings from both Secrets Manager and Parameter Store using `Annotated` field metadata with `{"service": "secrets"}` or `{"service": "ssm"}`
- boto3 client cache to reuse clients across multiple settings instantiations
- Multi-region and multi-account support via per-field `ssm_client` in `Annotated` metadata

## [0.0.2] - 2024-07-20

### Added
- `ParameterStoreBaseSettings` — load settings from AWS Systems Manager Parameter Store
- Support for annotating fields with a parameter name string or a dict with `ssm` and `ssm_client` keys

## [0.0.1] - 2024-07-11

### Added
- Initial release
- `SecretsManagerBaseSettings` — load settings from AWS Secrets Manager (JSON secrets)
- boto3 session configuration via `model_config`: `aws_region`, `aws_profile`, `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`
- Support for passing a pre-built boto3 client via `secrets_client`

[Unreleased]: https://github.com/ceb10n/pydantic-settings-aws/compare/v1.0.0b1...HEAD
[1.0.0b1]: https://github.com/ceb10n/pydantic-settings-aws/compare/v0.1.2...v1.0.0b1
[0.1.2]: https://github.com/ceb10n/pydantic-settings-aws/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ceb10n/pydantic-settings-aws/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ceb10n/pydantic-settings-aws/compare/v0.0.2...v0.1.0
[0.0.2]: https://github.com/ceb10n/pydantic-settings-aws/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/ceb10n/pydantic-settings-aws/releases/tag/v0.0.1
