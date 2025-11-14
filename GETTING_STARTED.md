# Getting Started with Context Engine

**Quick guide to delegating development via GitHub Issues**

---

## Project Status

**Repository:** https://github.com/RMSTrucks/context-engine
**Current Phase:** Setup
**Issues Created:** 7
**Ready to Delegate:** ✅ Yes

---

## Development Workflow

### 1. GitHub Issues = Work Delegation

All development tasks are tracked as GitHub Issues:

- **Issue #7:** Setup - Initial Project Structure (START HERE)
- **Issue #1:** Phase 1 - Vision Capture MCP Server
- **Issue #2:** Phase 2 - Audio Capture MCP Server
- **Issue #3:** Phase 3 - Context Engine MCP Server
- **Issue #4:** Phase 4 - VAPI Integration MCP Server
- **Issue #5:** Phase 5 - Polish & Production Deployment
- **Issue #6:** Phase 6 - Screenpipe Migration & Deprecation

### 2. How to Delegate

**Option A: Claude Code (Recommended)**
```bash
# In Claude Code chat:
"Read GitHub issue #7 and implement it"

# Claude will:
1. Fetch the issue via gh CLI
2. Create implementation plan
3. Write code
4. Create PR
5. Link PR to issue
```

**Option B: External Developer**
```bash
# Assign issue to developer
gh issue edit 7 --add-assignee username

# Developer works on it
# Creates PR referencing issue
# You review and merge
```

**Option C: Development Agent**
```bash
# Use Task tool to delegate to coding agent
# Agent reads issue, implements, creates PR
```

### 3. Issue Dependencies

**Start Here:**
- Issue #7 (Setup) - No dependencies

**Then in Order:**
- Issue #1 (Vision) - Requires: Setup complete
- Issue #2 (Audio) - Requires: Setup complete
- Issue #3 (Context) - Requires: Vision + Audio complete
- Issue #4 (VAPI) - Requires: Audio complete
- Issue #5 (Polish) - Requires: All core phases complete
- Issue #6 (Migration) - Requires: Everything production-ready

---

## Quick Start Commands

### View All Issues
```bash
cd C:/Users/Jake/WorkProjects/context-engine
gh issue list
```

### Start Setup Phase
```bash
# In Claude Code:
"Read issue #7 from context-engine repo and start implementing"

# Or manually:
gh issue view 7
```

### Check Progress
```bash
# See open issues
gh issue list --state open

# See completed
gh issue list --state closed

# Filter by phase
gh issue list --label "phase-1"
```

### Mark Issue Complete
```bash
# After implementation done
gh issue close 7 --comment "Setup complete. All dependencies installed and tested."
```

---

## Development Environment

### Prerequisites
- Python 3.10+
- Windows 10/11
- Git + GitHub CLI (gh)
- Claude Desktop/Code (for MCP integration)

### Installation (After Issue #7 Complete)
```bash
cd C:/Users/Jake/WorkProjects/context-engine
pip install -r requirements.txt
python setup.py install
```

### Running Tests
```bash
pytest
pytest tests/vision/  # Specific component
pytest -v             # Verbose output
```

---

## Project Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical specs.

**High-level:**
- **Layer 1:** Vision Capture (NormCap + MCP)
- **Layer 2:** Audio Capture (WhisperLive + MCP)
- **Layer 3:** Context Synthesis (Intelligence)
- **Layer 4:** VAPI Integration (REMUS/GENESIS)
- **Storage:** SQLite + FTS5 + ChromaDB

---

## Success Metrics

Track these as development progresses:

**Reliability:**
- [ ] Vision capture: >99% success rate
- [ ] Audio transcription: >95% word accuracy
- [ ] System uptime: 24/7 without restarts

**Performance:**
- [ ] Memory usage: <500MB active
- [ ] CPU usage: <15% during capture
- [ ] Capture latency: <2.5s (vision), <500ms (audio)

**Intelligence:**
- [ ] Stuck pattern detection: 90%+ precision
- [ ] Proactive suggestions: 5+ helpful/day
- [ ] Context synthesis: <500ms

---

## Communication

**For Development Questions:**
- Comment on the specific GitHub issue
- Tag @claude-2.0 if AI assistance needed
- Update issue description if scope changes

**For Architecture Questions:**
- See ARCHITECTURE.md
- Create new issue with question
- Tag as "documentation"

**For Bugs:**
- Create issue with "bug" label
- Include error logs
- Steps to reproduce

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Setup | 1-2 days | Ready to start |
| Phase 1 (Vision) | 5-7 days | Blocked by Setup |
| Phase 2 (Audio) | 5-7 days | Blocked by Setup |
| Phase 3 (Context) | 5-7 days | Blocked by P1+P2 |
| Phase 4 (VAPI) | 5-7 days | Blocked by P2 |
| Phase 5 (Polish) | 5-7 days | Blocked by P1-4 |
| Phase 6 (Migration) | 3-5 days | Blocked by P5 |
| **TOTAL** | **6 weeks** | **Not started** |

---

## Next Steps

1. **Read this document** ✅ (You're here!)
2. **Start Issue #7** - Setup project structure
3. **Validate installation** - Run tests, verify dependencies
4. **Begin Phase 1** - Vision capture MCP server
5. **Iterate through phases** - Follow dependency order

---

## Questions?

**Repository:** https://github.com/RMSTrucks/context-engine
**Issues:** https://github.com/RMSTrucks/context-engine/issues
**Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
**README:** [README.md](README.md)

Ready to build eyes and ears for AI! 🚀
