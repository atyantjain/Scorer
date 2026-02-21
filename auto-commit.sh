#!/bin/bash

# Auto-commit script for daily changes
# Usage: ./auto-commit.sh

set -e

REPO_PATH="/Users/atyantjain/Desktop/Personal Projects/Scorer"
cd "$REPO_PATH"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not a git repository"
    exit 1
fi

# Check for any changes (staged, unstaged, or untracked)
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
    echo "$(date): No changes to commit"
    exit 0
fi

# Add all changes
git add .

# Check if there are any staged changes
if git diff --cached --quiet; then
    echo "$(date): No staged changes after git add"
    exit 0
fi

# Create commit message with timestamp
COMMIT_MSG="Auto-commit: Daily changes - $(date '+%Y-%m-%d %H:%M:%S')"

# Commit changes
git commit -m "$COMMIT_MSG"

# Push to remote (with error handling)
if git push; then
    echo "$(date): Successfully committed and pushed changes"
    echo "Commit message: $COMMIT_MSG"
else
    echo "$(date): Committed locally but failed to push to remote"
    exit 1
fi