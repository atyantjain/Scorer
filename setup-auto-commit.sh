#!/bin/bash

# Setup script for daily auto-commit
# This will configure a cron job to run auto-commit every day at 11:30 PM

SCRIPT_PATH="/Users/atyantjain/Desktop/Personal Projects/Scorer/auto-commit.sh"
LOG_PATH="/Users/atyantjain/Desktop/Personal Projects/Scorer/auto-commit.log"

echo "Setting up daily auto-commit for Scorer project..."

# Create log file if it doesn't exist
touch "$LOG_PATH"

# Create the cron job entry
CRON_JOB="30 23 * * * $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_PATH"; then
    echo "Auto-commit cron job already exists!"
    echo "Current cron jobs:"
    crontab -l 2>/dev/null | grep "$SCRIPT_PATH" || echo "No matching cron jobs found"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Auto-commit cron job added successfully!"
    echo "Schedule: Every day at 11:30 PM"
    echo "Script: $SCRIPT_PATH"
    echo "Log: $LOG_PATH"
fi

echo ""
echo "To manage cron jobs:"
echo "  View all jobs: crontab -l"
echo "  Remove this job: crontab -l | grep -v '$SCRIPT_PATH' | crontab -"
echo "  View logs: tail -f $LOG_PATH"

echo ""
echo "Testing the auto-commit script now..."
"$SCRIPT_PATH"