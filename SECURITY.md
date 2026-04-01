# Security Maintenance Notes

## Current Approach

This repository uses exact dependency pins in `requirements.txt` to keep deployments reproducible and to reduce surprise breakage in the current codebase.

GitHub Dependabot and GitHub Actions smoke tests are enabled to:

- detect security advisories
- propose dependency updates
- prevent incompatible dependency bumps from being merged blindly

## Open Dependency Alert Strategy

Open alerts are reviewed in three groups:

### 1. Dependencies that require a real compatibility pass

These are not treated as quick version-bump fixes because the application depends on older APIs and import paths.

- `llama-index`
- `langchain`
- `langchain_community`
- `openai`
- `youtube-transcript-api`

For these dependencies, security or maintenance upgrades should be handled as dedicated refactor tasks with code changes and validation.

### 2. Dependencies that may be upgradeable with targeted validation

These may be fixable without a full refactor, but only after a passing smoke test and deployment check.

- `setuptools`
- `streamlit`
- `streamlit-extras`

### 3. Dependabot pull requests

Dependabot PRs should not be merged automatically.

Merge only when:

- the smoke test passes
- dependency resolution is stable
- runtime behavior is understood

Close PRs that are clearly incompatible with the current pinned stack, and revisit them later during intentional modernization work.

## Maintenance Principle

The goal is to keep `main` stable and deployable while handling security upgrades deliberately. A noisy stream of failed dependency bumps is not treated as progress; validated upgrades are.
