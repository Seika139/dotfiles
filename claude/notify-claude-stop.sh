#!/bin/bash

# Get current directory name
DIR_NAME=$(basename "$PWD")

# Get process PID
PID=$$

# Send notification with project info
terminal-notifier \
  -title "Claude Code [PID: $PID]" \
  -message "Stopped: $DIR_NAME" \
  -subtitle "Path: $PWD" \
  -sound Glass \
  -group "claude-$PID"
