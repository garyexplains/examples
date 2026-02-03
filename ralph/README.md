# Ralph for OpenAI codex

See https://github.com/snarktank/ralph

## Setup

### Copy to your project

Copy the ralph files into your project:

```bash
# From your project root
mkdir -p scripts/ralph
cp /path/to/ralph/ralph.sh scripts/ralph/

# Copy the prompt template for your AI tool of choice:
cp /path/to/ralph/prompt.md scripts/ralph/prompt.md    # For Amp
# OR
cp /path/to/ralph/CLAUDE.md scripts/ralph/CLAUDE.md    # For Claude Code
# OR
cp /path/to/ralph/CODEX.md scripts/ralph/CODEX.md    # For Codex

chmod +x scripts/ralph/ralph.sh
```

### Install skills

Copy the skills to your Amp or Claude or Codex config for use across all projects:

For AMP
```bash
cp -r skills/prd ~/.config/amp/skills/
cp -r skills/ralph ~/.config/amp/skills/
```

For Claude Code (manual)
```bash
cp -r skills/prd ~/.claude/skills/
cp -r skills/ralph ~/.claude/skills/
```

For Codex
```bash
cp -r skills/prd ~/.codex/skills/
cp -r skills/ralph ~/.codex/skills/
```
