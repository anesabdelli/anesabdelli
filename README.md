# GitHub Statistics Dashboard

Interactive GitHub Pages dashboard with **real GitHub data only**.

## What this project does

- Displays stats from `assets/stats.json`
- Never fabricates missing values
- Shows `Unavailable` when data is not accessible
- Updates stats automatically with GitHub Actions

## Authentication model (safe)

Do **not** put tokens in frontend code (`index.html` / `script.js`).

For private stats:

1. Create a Personal Access Token (classic or fine-grained)
2. Grant minimum read permissions to repositories and profile data
3. In your repository, add secret:
   - `Settings -> Secrets and variables -> Actions -> New repository secret`
   - Name: `GH_STATS_TOKEN`
   - Value: your token
4. (Optional) Add repository variable:
   - `Settings -> Secrets and variables -> Actions -> Variables`
   - Name: `GH_USERNAME`
   - Value: your GitHub username

If `GH_STATS_TOKEN` is missing or invalid, the workflow automatically falls back to **public-only** mode.

## Enable GitHub Pages

1. Push this project to a public repository
2. Go to `Settings -> Pages`
3. Set:
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/ (root)`
4. Save and wait for deployment URL

## Run stats update

- Go to `Actions -> Update GitHub Stats -> Run workflow`
- This generates or refreshes `assets/stats.json`

## How to give Copilot access (without sharing secrets)

Use your local authentication in VS Code/terminal:

1. Install GitHub CLI (`gh`) if needed
2. Run: `gh auth login`
3. Choose GitHub.com and complete browser auth
4. Keep token private; no need to paste it in chat

This allows git operations from your local environment while keeping credentials private.
