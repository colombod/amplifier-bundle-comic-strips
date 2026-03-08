#!/usr/bin/env bash
# Structural verification for comic-strips interactive modes + recipe quality hardening.
# Run from the amplifier-bundle-comic-strips/ directory.
# Exit 0 on all-pass, non-zero on any failure.

set -euo pipefail

PASS=0
FAIL=0
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

pass() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

echo "=== Mode File Existence ==="

for mode in comic-brainstorm comic-design comic-plan comic-review comic-publish; do
  if [[ -f "$SCRIPT_DIR/modes/${mode}.md" ]]; then
    pass "modes/${mode}.md exists"
  else
    fail "modes/${mode}.md MISSING"
  fi
done

echo ""
echo "=== Mode YAML Parsing ==="

for mode in comic-brainstorm comic-design comic-plan comic-review comic-publish; do
  FILE="$SCRIPT_DIR/modes/${mode}.md"
  if [[ ! -f "$FILE" ]]; then
    fail "${mode}.md not found, skipping parse check"
    continue
  fi
  if python3 -c "
import yaml, sys
text = open('$FILE').read()
parts = text.split('---')
if len(parts) < 3:
    print('No YAML frontmatter found')
    sys.exit(1)
data = yaml.safe_load(parts[1])
if data is None:
    print('YAML parsed to None')
    sys.exit(1)
" 2>/dev/null; then
    pass "${mode}.md YAML parses correctly"
  else
    fail "${mode}.md YAML parse FAILED"
  fi
done

echo ""
echo "=== Mode Required Keys ==="

for mode in comic-brainstorm comic-design comic-plan comic-review comic-publish; do
  FILE="$SCRIPT_DIR/modes/${mode}.md"
  if [[ ! -f "$FILE" ]]; then
    fail "${mode}.md not found, skipping key check"
    continue
  fi
  python3 -c "
import yaml, sys
text = open('$FILE').read()
data = yaml.safe_load(text.split('---')[1])
m = data.get('mode', {})
missing = []
for key in ['name', 'default_action', 'allowed_transitions', 'allow_clear']:
    if key not in m:
        missing.append(key)
# tools.safe is nested
if 'tools' not in m or 'safe' not in m.get('tools', {}):
    missing.append('tools.safe')
if missing:
    print(','.join(missing))
    sys.exit(1)
" 2>/dev/null
  if [[ $? -eq 0 ]]; then
    pass "${mode}.md has all required keys"
  else
    fail "${mode}.md MISSING keys"
  fi
done

echo ""
echo "=== default_action: block on all modes ==="

for mode in comic-brainstorm comic-design comic-plan comic-review comic-publish; do
  FILE="$SCRIPT_DIR/modes/${mode}.md"
  if [[ ! -f "$FILE" ]]; then
    fail "${mode}.md not found"
    continue
  fi
  VAL=$(python3 -c "
import yaml
text = open('$FILE').read()
data = yaml.safe_load(text.split('---')[1])
print(data.get('mode', {}).get('default_action', ''))
" 2>/dev/null)
  if [[ "$VAL" == "block" ]]; then
    pass "${mode}: default_action is block"
  else
    fail "${mode}: default_action is '${VAL}', expected 'block'"
  fi
done

echo ""
echo "=== allow_clear: true ONLY on comic-publish ==="

for mode in comic-brainstorm comic-design comic-plan comic-review; do
  FILE="$SCRIPT_DIR/modes/${mode}.md"
  if [[ ! -f "$FILE" ]]; then
    fail "${mode}.md not found"
    continue
  fi
  VAL=$(python3 -c "
import yaml
text = open('$FILE').read()
data = yaml.safe_load(text.split('---')[1])
print(data.get('mode', {}).get('allow_clear', False))
" 2>/dev/null)
  if [[ "$VAL" == "False" ]]; then
    pass "${mode}: allow_clear is false"
  else
    fail "${mode}: allow_clear is '${VAL}', expected False"
  fi
done

FILE="$SCRIPT_DIR/modes/comic-publish.md"
if [[ -f "$FILE" ]]; then
  VAL=$(python3 -c "
import yaml
text = open('$FILE').read()
data = yaml.safe_load(text.split('---')[1])
print(data.get('mode', {}).get('allow_clear', False))
" 2>/dev/null)
  if [[ "$VAL" == "True" ]]; then
    pass "comic-publish: allow_clear is true"
  else
    fail "comic-publish: allow_clear is '${VAL}', expected True"
  fi
fi

echo ""
echo "=== Transition Graph Consistency ==="

# Every mode listed in any allowed_transitions must exist as a file
ALL_TRANSITIONS=$(python3 -c "
import yaml, glob, os
transitions = set()
for f in glob.glob('$SCRIPT_DIR/modes/comic-*.md'):
    text = open(f).read()
    parts = text.split('---')
    if len(parts) < 3:
        continue
    data = yaml.safe_load(parts[1])
    for t in data.get('mode', {}).get('allowed_transitions', []):
        transitions.add(t)
for t in sorted(transitions):
    print(t)
" 2>/dev/null)

for trans in $ALL_TRANSITIONS; do
  if [[ -f "$SCRIPT_DIR/modes/${trans}.md" ]]; then
    pass "transition target '${trans}' exists as modes/${trans}.md"
  else
    fail "transition target '${trans}' has NO corresponding file modes/${trans}.md"
  fi
done

echo ""
echo "=== comic_create blocked in brainstorm and design ==="

for mode in comic-brainstorm comic-design; do
  FILE="$SCRIPT_DIR/modes/${mode}.md"
  if [[ ! -f "$FILE" ]]; then
    fail "${mode}.md not found"
    continue
  fi
  FOUND=$(python3 -c "
import yaml
text = open('$FILE').read()
data = yaml.safe_load(text.split('---')[1])
tools = data.get('mode', {}).get('tools', {})
safe = tools.get('safe', [])
warn = tools.get('warn', [])
if 'comic_create' in safe or 'comic_create' in warn:
    print('FOUND')
else:
    print('BLOCKED')
" 2>/dev/null)
  if [[ "$FOUND" == "BLOCKED" ]]; then
    pass "${mode}: comic_create is blocked (not in safe or warn)"
  else
    fail "${mode}: comic_create is NOT blocked — found in safe or warn list"
  fi
done

echo ""
echo "=== Recipe YAML Parsing ==="

for recipe in issue-art issue-retry issue-compose saga-plan session-to-comic design-characters; do
  FILE="$SCRIPT_DIR/recipes/${recipe}.yaml"
  if [[ ! -f "$FILE" ]]; then
    fail "recipes/${recipe}.yaml not found"
    continue
  fi
  if python3 -c "import yaml; yaml.safe_load(open('$FILE'))" 2>/dev/null; then
    pass "recipes/${recipe}.yaml parses correctly"
  else
    fail "recipes/${recipe}.yaml YAML parse FAILED"
  fi
done

echo ""
echo "=== Recipe Quality Hardening Checks ==="

# B1: character-designer contains review_asset
if grep -q "review_asset" "$SCRIPT_DIR/agents/character-designer.md" 2>/dev/null; then
  pass "character-designer.md contains review_asset (self-review loop)"
else
  fail "character-designer.md does NOT contain review_asset"
fi

# B2: issue-art.yaml contains inspect-flagged-panels step
if grep -q "inspect-flagged-panels" "$SCRIPT_DIR/recipes/issue-art.yaml" 2>/dev/null; then
  pass "issue-art.yaml contains inspect-flagged-panels step"
else
  fail "issue-art.yaml does NOT contain inspect-flagged-panels step"
fi

# B3: issue-art.yaml generate-panels prompt mentions content_policy_notes accumulation
if grep -q "content_policy_notes" "$SCRIPT_DIR/recipes/issue-art.yaml" 2>/dev/null; then
  pass "issue-art.yaml references content_policy_notes"
else
  fail "issue-art.yaml does NOT reference content_policy_notes"
fi

# B4: issue-retry.yaml contains review-panel-compositions step
if grep -q "review-panel-compositions" "$SCRIPT_DIR/recipes/issue-retry.yaml" 2>/dev/null; then
  pass "issue-retry.yaml contains review-panel-compositions step"
else
  fail "issue-retry.yaml does NOT contain review-panel-compositions step"
fi

# B4: issue-compose.yaml contains review-panel-compositions step
if grep -q "review-panel-compositions" "$SCRIPT_DIR/recipes/issue-compose.yaml" 2>/dev/null; then
  pass "issue-compose.yaml contains review-panel-compositions step"
else
  fail "issue-compose.yaml does NOT contain review-panel-compositions step"
fi

# B5: saga-plan.yaml mechanical steps have model_role annotation
for step_id in check-existing init-project lookup-existing-characters store-storyboard validate-storyboard create-issues prepare-review; do
  # Check that the step's block (from its id to the next step or end) contains model_role
  if python3 -c "
import yaml
data = yaml.safe_load(open('$SCRIPT_DIR/recipes/saga-plan.yaml'))
for stage in data.get('stages', []):
    for step in stage.get('steps', []):
        if step.get('id') == '${step_id}':
            if 'model_role' in step:
                exit(0)
            else:
                exit(1)
exit(1)
" 2>/dev/null; then
    pass "saga-plan step '${step_id}' has model_role annotation"
  else
    fail "saga-plan step '${step_id}' MISSING model_role annotation"
  fi
done

echo ""
echo "==============================="
echo "PASSED: $PASS"
echo "FAILED: $FAIL"
echo "==============================="

if [[ $FAIL -gt 0 ]]; then
  exit 1
else
  echo "All checks passed!"
  exit 0
fi
