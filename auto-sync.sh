#!/bin/bash
# Auto commit and push script
# This script will automatically commit and push changes

cd "$(dirname "$0")"

# Add all changes
git add .

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes to commit"
else
    # Commit with timestamp
    git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Push to GitHub
    git push origin main
    
    echo "Changes pushed to GitHub successfully!"
fi
