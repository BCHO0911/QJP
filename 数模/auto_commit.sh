#!/bin/bash
# 自动提交脚本 - 在每次重要修改后运行
cd "d:/GIT/private"
git add -A
CHANGES=$(git diff --cached --name-only 2>/dev/null)
if [ -n "$CHANGES" ]; then
    git commit -m "auto-commit: $(date '+%Y-%m-%d %H:%M:%S')
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
    echo "Committed: $CHANGES"
else
    echo "No changes to commit."
fi
