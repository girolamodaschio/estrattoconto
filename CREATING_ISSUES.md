# Creating GitHub Issues for Roadmap Tasks

This guide explains how to create all 27 GitHub issues for the estrattoconto enhancement roadmap without merging the documentation PR first.

## Prerequisites

You need a GitHub Personal Access Token with `repo` scope.

### Creating a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "estrattoconto-issues"
4. Select scopes: **✅ repo** (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

## Method 1: Using the Bash Script (Recommended - All 27 Issues)

The bash script `create_issues.sh` contains all 27 issues fully defined.

```bash
# Navigate to repository
cd /home/user/estrattoconto

# Make script executable (already done)
chmod +x create_issues.sh

# Run with your token
./create_issues.sh YOUR_GITHUB_TOKEN_HERE

# Or set environment variable
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
./create_issues.sh
```

### What It Does

- Creates all 27 issues with:
  - Proper titles: `[TASK-XXX] Description`
  - Complete descriptions with code examples
  - Acceptance criteria checklists
  - References to detailed documentation
  - Proper labels: `phase-1`, `priority: critical`, `bug`, etc.

- Issues are organized by phase:
  - **Phase 1**: Tasks 001-006 (Bug fixes)
  - **Phase 2**: Tasks 007-012 (Provider architecture)
  - **Phase 3**: Tasks 013-018 (Performance)
  - **Phase 4**: Tasks 019-021 (ML features)
  - **Phase 5**: Tasks 022-024 (Django integration)
  - **Phase 6**: Tasks 025-027 (Production readiness)

## Method 2: Using Python Script

```bash
# Install requests if needed
pip install requests

# Run script
python create_issues.py YOUR_GITHUB_TOKEN_HERE

# Or with environment variable
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN_HERE
python create_issues.py
```

**Note:** The Python script currently only has 2 example issues defined. Use the bash script for all 27 issues.

## Method 3: Manual Creation via GitHub UI

If you prefer to create issues manually:

1. Go to: https://github.com/girolamodaschio/estrattoconto/issues/new
2. For each task in `TASKS.md`:
   - Copy the title (e.g., `[TASK-001] Fix extract_document_type() Loop Bug`)
   - Copy the description from the task section
   - Add labels (phase-1, priority, etc.)
   - Click "Submit new issue"

This method takes more time but gives you full control.

## Method 4: Using GitHub CLI (if installed)

```bash
# Install GitHub CLI if not available
# See: https://cli.github.com/

# Authenticate
gh auth login

# Create issues from script
# (Would need to adapt the script for gh CLI format)
```

## After Creating Issues

Once issues are created, you can:

1. **Assign to agents:**
   ```
   @agent please work on issue #1
   ```

2. **Create project board:**
   - Go to Projects tab
   - Create "Enhancement Roadmap" project
   - Add all issues
   - Organize by phase

3. **Start implementation:**
   - Pick highest priority issues (TASK-001 to TASK-006)
   - Create branches: `claude/task-001-<session-id>`
   - Implement according to acceptance criteria
   - Create PRs referencing issue numbers

## Verifying Issues Were Created

Check: https://github.com/girolamodaschio/estrattoconto/issues

You should see 27 new issues with proper labels and formatting.

## Troubleshooting

### "401 Unauthorized"
- Token is invalid or expired
- Token doesn't have `repo` scope

### "404 Not Found"
- Repository name is incorrect
- Token doesn't have access to the repository

### "422 Validation Failed"
- Issue format is incorrect
- Label doesn't exist (will be created automatically)

## Security Note

**Never commit your GitHub token to the repository!**

The token is only passed as a command-line argument or environment variable.

## Labels That Will Be Created

The script will automatically create these labels if they don't exist:
- `phase-1`, `phase-2`, `phase-3`, `phase-4`, `phase-5`, `phase-6`
- `priority: critical`, `priority: high`, `priority: medium`, `priority: low`
- `bug`, `enhancement`, `documentation`, `performance`, `ml`, `django`
- `architecture`, `refactor`, `api`, `ci-cd`, `benchmarks`, `dependencies`

## Next Steps After Issues Are Created

1. Review the issues to ensure they're correct
2. Optionally create GitHub Project board
3. Start with Phase 1 (critical priorities)
4. Assign issues to yourself or spawn agents
5. Track progress in TASKS.md

## Questions?

- Check `ROADMAP.md` for high-level overview
- Check `TASKS.md` for task details
- Check `docs/implementation/` for detailed specifications
