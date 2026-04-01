# Building Trust in AI: YouTube Transcript OpenAI Assistant
Building Trust in AI: YouTube Transcript OpenAI Assistant

App. https://youtube-transcript-openai-assistant-ytb.streamlit.app/

Blog. https://blogs.sap.com/2023/07/14/building-trust-in-ai-youtube-transcript-openai-assistant/

## Dependency Maintenance

This repository uses exact dependency pins in `requirements.txt` to keep installs reproducible and to avoid surprise breakage in the older `llama-index` based code.

- `main` should stay on known-good pinned versions.
- GitHub Dependabot is enabled for pip dependencies.
- GitHub Actions runs a lightweight smoke test on pushes and pull requests.
- Do not merge dependency PRs automatically just because they were opened.
- Merge only dependency updates whose smoke test passes and whose impact is understood.

The following packages are intentionally treated as manual-upgrade dependencies because major, minor, and even patch bumps can require code changes in this project:

- `openai`
- `youtube-transcript-api`
- `llama-index`
- `llama_hub`
- `langchain`
- `langchain_community`

When updating those packages, prefer a dedicated compatibility pass instead of a quick version bump.
