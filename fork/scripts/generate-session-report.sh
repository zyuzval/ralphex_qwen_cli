#!/bin/bash
# generate-session-report.sh
# Генерирует стандартизированный отчёт для параллельной сессии

set -e

echo "=============================================="
echo "  TG-STATS Fix Session Report Generator"
echo "=============================================="
echo ""

# 1. Git diff
echo "## Git Diff"
echo ""
echo '```diff'
git diff --stat
echo ""
git diff
echo '```'
echo ""

# 2. Test results
echo "## Test Results"
echo ""
echo '```bash'
echo "Running pytest..."
cd /d/DevLab/tg-stats-fork_qwen || cd "$(dirname "$0")/.."
python -m pytest tests/ -v --tb=short 2>&1 || true
echo '```'
echo ""

# 3. Build results
echo "## Build Results"
echo ""
echo '```bash'
echo "Running npm build..."
cd web
npm run build 2>&1 || true
echo '```'
echo ""

# 4. TypeScript check
echo "## TypeScript Check"
echo ""
echo '```bash'
npx tsc --noEmit 2>&1 || true
echo '```'
echo ""

# 5. Files modified
echo "## Files Modified"
echo ""
echo '```'
git diff --name-only
echo '```'
echo ""

# 6. Verification checklist
echo "## Verification Checklist"
echo ""
echo "- [ ] All tests pass"
echo "- [ ] Build succeeds"
echo "- [ ] No new TypeScript errors"
echo "- [ ] Specific fixes verified (see below)"
echo ""

echo "=============================================="
echo "  Report generated: $(date)"
echo "=============================================="
