#!/bin/bash
# Claude Code stop notification script

# Get project directory name
PROJECT_NAME=$(basename "$PWD")

# Send notification
terminal-notifier \
  -title "Claude Code" \
  -message "Stopped: $PROJECT_NAME" \
  -subtitle "$PWD" \
  -sound Glass

# Also play sound directly as backup
afplay /System/Library/Sounds/Glass.aiff