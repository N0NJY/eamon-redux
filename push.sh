#!/bin/bash
cd ~/git/Eamon

# Make changes (Claude Code writes files)

# Stage and push
git add .
git commit -m "[FEATURE] Description of what changed"
git push origin main

# Confirm success
echo "✅ Pushed to GitHub"
