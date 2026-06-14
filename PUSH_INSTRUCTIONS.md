# Push instructions

This repo is committed locally but **not pushed**. To publish it as the
calling-card repo under `hmatrades`, run these yourself.

## 1. Create the GitHub repo and push (one command)

```bash
cd /Users/amh/Developer/_public-staging/agent-memory-bench

gh repo create hmatrades/agent-memory-bench \
  --public \
  --source . \
  --remote origin \
  --description "Reproduce ACE's agent-memory compression — verify the claim with your own corpus. ACE vs claude-mem vs raw across 3 public corpora (tokens · recall@k · cost-USD)." \
  --push
```

That creates the public repo, wires `origin`, and pushes the current branch.

> The local default branch is `main` (matches the workflows' `on: push: branches: [main]`).
> If your local branch is named otherwise, rename before pushing:
> `git branch -M main`.

## 2. After it's live (2 minutes)

- **Topics** (Settings → top of repo, or):
  ```bash
  gh repo edit hmatrades/agent-memory-bench \
    --add-topic llm --add-topic agents --add-topic memory \
    --add-topic compression --add-topic context-engineering \
    --add-topic benchmark --add-topic claude
  ```
- **Social preview**: Settings → Social preview → upload a 1280×640 PNG built to
  `docs/hero.md` § "OG / social-preview image".
- **Pin it**: add to your profile's pinned repos (it's calling-card slot 3 in the
  GitHub audit).
- **Sponsors**: `.github/FUNDING.yml` already points at `github: [hmatrades]` —
  enable GitHub Sponsors on the account for the badge to resolve.

## 3. Optional — publish to PyPI so `uvx agent-memory-bench` works for everyone

```bash
pip install build twine
python -m build
twine upload dist/*
```

Until published, users run it from source:
`uvx --from git+https://github.com/hmatrades/agent-memory-bench agent-memory-bench`.

## 4. Distribution (from the GitHub audit)

The single highest-leverage tag is **Greg Kamradt (@gkamradt)** — the
needle-in-haystack benchmark author. The launch tweet writes itself:
*"someone said ACE compresses agent context 195×. so I made it reproducible.
`uvx agent-memory-bench`. it's 503× on Anthropic docs — and it loses on kernel
commits. numbers, not vibes."* Then a PR to `anthropics/anthropic-cookbook`
referencing it.
