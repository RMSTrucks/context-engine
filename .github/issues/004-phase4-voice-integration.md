# Issue #4: Phase 4 - Voice Integration (Self-Hosted)

**Status:** Open
**Priority:** Medium
**Labels:** phase-4, audio, priority-medium
**Created:** 2025-11-14
**Updated:** 2025-11-14 (Changed from VAPI to self-hosted)

---

## Goal
Self-hosted phone system for REMUS/GENESIS with call transcripts integrated into context engine

**Changed:** Using self-hosted SIP/VoIP instead of VAPI for full local control

---

## Deliverables

### 1. Self-Hosted Phone Infrastructure

**Options to evaluate:**
- **Asterisk** - Full-featured PBX (most powerful)
- **FreeSWITCH** - Modern, developer-friendly
- **Twilio Programmable Voice** - SIP trunking + local control
- **SIP.js + WebRTC** - Browser-based calls

**Choose based on:**
- Windows compatibility
- Local deployment (no cloud dependency)
- Call recording capability
- Transcription integration
- Cost (prefer open source)

**Deliverables:**
- [ ] Evaluate phone system options
- [ ] Choose and install self-hosted solution
- [ ] Configure SIP trunking for phone numbers
- [ ] Set up call recording
- [ ] Test inbound/outbound calls

### 2. MCP Server Infrastructure
- [ ] Create `mcp-servers/voice-integration/` directory
- [ ] Implement MCP stdio server boilerplate
- [ ] Define tool schemas for call operations

### 3. Call Recording & Transcription

**Pipeline:**
```
Phone Call → Recording (WAV/MP3)
           → Whisper (from Phase 2)
           → Transcript
           → Context Engine Storage
```

**Deliverables:**
- [ ] Integrate phone system with call recording
- [ ] Hook recordings into WhisperLive from Phase 2
- [ ] Real-time transcription during calls
- [ ] Post-call transcription for quality
- [ ] Store audio files + transcripts

### 4. Call Processing
- [ ] Save call transcripts to `audio_transcripts` table
- [ ] Tag with agent (remus/genesis)
- [ ] Store caller ID, duration, direction (inbound/outbound)
- [ ] Extract action items from transcript
- [ ] Link to contact_id in Close CRM
- [ ] Store call metadata (cost, quality metrics)

### 5. MCP Tools

#### `make_call`
```python
{
    "name": "make_call",
    "description": "Initiate outbound call (REMUS/GENESIS)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "phone_number": {"type": "string"},
            "agent": {"enum": ["remus", "genesis"]},
            "context": {"type": "string"}  # Why calling
        }
    }
}
```

#### `search_calls`
```python
{
    "name": "search_calls",
    "description": "Search call transcripts",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "agent": {"enum": ["remus", "genesis", "both"]},
            "days_back": {"type": "number"}
        }
    }
}
```

#### `get_call_transcript`
```python
{
    "name": "get_call_transcript",
    "description": "Get full transcript of call",
    "inputSchema": {
        "type": "object",
        "properties": {
            "call_id": {"type": "string"}
        }
    }
}
```

#### `get_recent_calls`
```python
{
    "name": "get_recent_calls",
    "description": "List recent calls",
    "inputSchema": {
        "type": "object",
        "properties": {
            "agent": {"enum": ["remus", "genesis", "both"]},
            "limit": {"type": "number"}
        }
    }
}
```

#### `extract_action_items`
```python
{
    "name": "extract_action_items",
    "description": "Extract action items from call",
    "inputSchema": {
        "type": "object",
        "properties": {
            "call_id": {"type": "string"}
        }
    }
}
```

### 6. Agent Integration

**REMUS (Trucking Compliance):**
- Answer inbound calls about compliance
- Make outbound calls for follow-ups
- Auto-update Close CRM after calls
- Extract compliance action items

**GENESIS (Meta-AI Thinking Partner):**
- Answer calls for brainstorming
- Transcribe thinking sessions
- Extract insights and decisions
- No CRM integration (personal use)

**Deliverables:**
- [ ] REMUS phone number provisioning
- [ ] GENESIS phone number provisioning
- [ ] Call routing (different numbers → different agents)
- [ ] Agent-specific prompts/context
- [ ] Agent-specific post-call processing

### 7. CRM Integration (REMUS only)
- [ ] Auto-update Close CRM from REMUS calls
- [ ] Create follow-up tasks from action items
- [ ] Link transcript to contact record
- [ ] Log call duration, outcome
- [ ] Tag opportunities based on call content

### 8. Testing
- [ ] Mock call scenarios
- [ ] Test call recording
- [ ] Test transcription accuracy
- [ ] Test CRM auto-update
- [ ] Load testing (multiple simultaneous calls)
- [ ] Quality testing (audio clarity, transcription)

### 9. Documentation
- [ ] Phone system setup guide
- [ ] SIP configuration instructions
- [ ] Call flow diagrams
- [ ] Agent configuration
- [ ] Troubleshooting guide
- [ ] Example call queries

---

## Technical Architecture

### Self-Hosted Phone System

**Recommended: FreeSWITCH** (Windows compatible, modern)

```
Phone Call (SIP)
    ↓
FreeSWITCH (local)
    ↓
Call Recording (WAV)
    ↓
WhisperLive (Phase 2)
    ↓
Transcript
    ↓
Context Engine Storage (SQLite + ChromaDB)
```

**Alternative: Asterisk** (more features, steeper learning curve)

### Storage Schema

```sql
-- Extends audio_transcripts from Phase 2
ALTER TABLE audio_transcripts ADD COLUMN call_direction TEXT; -- 'inbound', 'outbound'
ALTER TABLE audio_transcripts ADD COLUMN caller_id TEXT;
ALTER TABLE audio_transcripts ADD COLUMN call_duration INTEGER; -- seconds
ALTER TABLE audio_transcripts ADD COLUMN call_quality REAL; -- 0.0-1.0
ALTER TABLE audio_transcripts ADD COLUMN recording_path TEXT;
```

### Call Flow

**Inbound Call:**
```
1. Phone rings (caller ID captured)
2. FreeSWITCH routes to REMUS or GENESIS
3. Agent answers with context-aware greeting
4. Call recorded automatically
5. WhisperLive transcribes in real-time
6. Agent responds using transcript context
7. Call ends → full transcript saved
8. Post-processing: action items, CRM update
```

**Outbound Call:**
```
1. MCP tool: make_call(phone_number, agent, context)
2. FreeSWITCH initiates SIP call
3. Agent introduces itself
4. Conversation proceeds (recorded + transcribed)
5. Call ends → saved to database
6. Post-processing: outcome logged
```

---

## Success Criteria
- [ ] Self-hosted phone system operational 24/7
- [ ] 100% of REMUS/GENESIS calls recorded
- [ ] >95% transcription accuracy
- [ ] Searchable within seconds of call end
- [ ] CRM auto-updated for REMUS calls
- [ ] Action items extracted with >80% accuracy
- [ ] No cloud dependencies (fully local)

---

## Timeline
Week 4 (5-7 days)

**Breakdown:**
- Day 1-2: Evaluate and install phone system
- Day 3-4: Integrate recording + transcription
- Day 5: MCP tools + agent integration
- Day 6: CRM integration (REMUS)
- Day 7: Testing + documentation

---

## Dependencies
- **Phase 2 complete** - WhisperLive transcription ready
- **SIP trunk provider** - For phone numbers (Twilio, Bandwidth.com, etc.)
- **Local server** - Running FreeSWITCH or Asterisk

---

## Cost Estimates

**Self-Hosted Solution:**
- Phone numbers: $1-2/month per number (2 numbers = $4/month)
- SIP trunk: $0.01-0.02/minute
- Server: Already have (local machine)
- Software: Free (open source)

**Total: ~$10-20/month** vs VAPI's ~$100-200/month

---

## Alternatives Considered

### ❌ VAPI (Original Plan)
**Pros:** Managed service, easy setup
**Cons:** Cloud dependency, expensive, less control
**Decision:** Rejected for self-hosted

### ✅ FreeSWITCH (Recommended)
**Pros:** Modern, Windows compatible, developer-friendly
**Cons:** Learning curve
**Decision:** Primary choice

### ⚠️ Asterisk (Fallback)
**Pros:** More features, mature, well-documented
**Cons:** Steeper learning curve, older tech
**Decision:** Use if FreeSWITCH doesn't work

### ⚠️ Twilio Programmable Voice (Hybrid)
**Pros:** SIP trunking + local control, good docs
**Cons:** Still some cloud dependency
**Decision:** Use for SIP trunking only, not call handling

---

## Integration with Context Engine

**Voice calls become searchable context:**

```python
# Example: Search what customer said about insurance
context_engine.search_calls(
    query="insurance quotes",
    agent="remus",
    days_back=30
)

# Returns: Call transcripts mentioning insurance
```

**Example queries:**
- "What did Tyler say about cargo coverage?"
- "Show me all calls about DOT compliance this week"
- "Find the call where we discussed the new driver"

**Proactive intelligence:**
- Detect repeated questions → create FAQ
- Identify common issues → suggest solutions
- Track customer sentiment → flag concerns

---

## Notes

**Why self-hosted:**
- Full control over data (privacy)
- No cloud dependency (works offline)
- Lower cost (no per-minute charges to VAPI)
- More customization (can modify behavior)
- Better integration (direct access to call data)

**Why not VAPI:**
- Expensive ($100-200/month)
- Cloud dependency (requires internet)
- Less control (black box)
- Harder to debug (remote service)

**Phone numbers:**
- Still need SIP trunk provider (Twilio, Bandwidth.com)
- But only for call routing, not AI handling
- Much cheaper ($1-2/month per number)

---

## Related Issues

- **Issue #2** - Audio capture (WhisperLive integration)
- **Issue #3** - Context synthesis (where calls feed into)
- **Issue #5** - Polish (monitoring, reliability)

---

**Updated from VAPI to self-hosted for full local control and lower cost.**
