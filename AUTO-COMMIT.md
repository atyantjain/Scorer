# Auto-Commit Setup

This directory contains scripts to automatically commit and push daily changes to your repository.

## Files

- `auto-commit.sh` - Script that commits and pushes changes
- `setup-auto-commit.sh` - One-time setup script for cron job

## Quick Setup

1. **Run the setup script once:**
   ```bash
   ./setup-auto-commit.sh
   ```

2. **That's it!** The script will now run automatically every day at 11:30 PM

## What it does

- Checks for any changes in your repository
- If changes exist, commits them with timestamp
- Pushes to your GitHub repository
- Logs all activity to `auto-commit.log`

## Manual Usage

You can also run the auto-commit script manually:
```bash
./auto-commit.sh
```

## Schedule

- **Default:** Every day at 11:30 PM
- **Log location:** `auto-commit.log`

## Managing Cron Jobs

- **View all cron jobs:** `crontab -l`
- **Remove auto-commit job:** `crontab -l | grep -v auto-commit.sh | crontab -`
- **View logs:** `tail -f auto-commit.log`
- **Edit cron jobs:** `crontab -e`

## Notes

- Only commits when there are actual changes
- Safely handles git operations with error checking
- Includes timestamps in commit messages
- Logs all activity for debugging