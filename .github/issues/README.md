# GitHub Issues (Offline Access)

This directory contains markdown copies of all GitHub issues for offline access.

## Why This Exists

When working offline or when GitHub CLI isn't available, these files provide full access to issue details without needing to copy/paste from GitHub.

## Files

- `007-setup-initial-structure.md` - **START HERE** - Initial project structure
- `001-phase1-vision.md` - Phase 1: Vision Capture MCP Server
- `002-phase2-audio.md` - Phase 2: Audio Capture MCP Server
- `003-phase3-context.md` - Phase 3: Context Engine MCP Server
- `004-phase4-vapi.md` - Phase 4: VAPI Integration MCP Server
- `005-phase5-polish.md` - Phase 5: Polish & Production Deployment
- `006-phase6-migration.md` - Phase 6: Screenpipe Migration

## Usage

### When Implementing an Issue

```bash
# Read the issue file
cat .github/issues/007-setup-initial-structure.md

# Or in Claude Code:
"Read .github/issues/007-setup-initial-structure.md and implement it"
```

### Keeping in Sync

These files are snapshots. If the GitHub issue is updated:

```bash
# Re-export from GitHub
gh issue view 7 --json title,body --jq '{title, body}' > .github/issues/007-setup-initial-structure.md
```

Or manually edit the markdown file and update GitHub issue.

## Format

Each file contains:
- Issue title
- Status, priority, labels
- Full description
- Deliverables (checkboxes)
- Success criteria
- Timeline
- Dependencies

Same content as GitHub issue, just in markdown for offline access.
