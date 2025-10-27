# Amplifier Studio - Complete User Experience

## User Flow: Two Main Paths

### Path 1: Execute Existing Scenario
**Time**: 60 seconds from landing to running

### Path 2: Create New Scenario
**Time**: 5-10 minutes conversational design

---

## Path 1: Execute Existing Scenario

### Step 1: Landing Page (0-5 seconds)
```
User opens http://localhost:5173

Sees:
┌─────────────────────────────────────────────────────────┐
│ 🎨 Amplifier Studio                    [Scenarios] [💬 Create New] │
│ Where AI agents bring ideas to life                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ╔═══════════════╗  ╔═══════════════╗  ╔══════════════╗ │
│  ║ Blog Writer   ║  ║ Transcribe    ║  ║ Article      ║ │
│  ║               ║  ║               ║  ║ Illustrator  ║ │
│  ║ Transform     ║  ║ Convert audio ║  ║ Generate     ║ │
│  ║ rough ideas   ║  ║ to text with  ║  ║ images for   ║ │
│  ║ into polished ║  ║ AI enhancement║  ║ articles     ║ │
│  ║ blog posts    ║  ║               ║  ║              ║ │
│  ║               ║  ║               ║  ║              ║ │
│  ║ 2 parameters  ║  ║ 1 parameter   ║  ║ 3 parameters ║ │
│  ╚═══════════════╝  ╚═══════════════╝  ╚══════════════╝ │
│                                                          │
│  ╔═══════════════╗                                       │
│  ║ Tips          ║                                       │
│  ║ Synthesizer   ║                                       │
│  ║ ...           ║                                       │
│  ╚═══════════════╝                                       │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Browse scenarios
- See descriptions at a glance
- Click any card to learn more

### Step 2: Scenario Details (5-10 seconds)
```
User clicks "Blog Writer"

Sees:
┌─────────────────────────────────────────────────────────┐
│ ← Back to scenarios                                      │
├─────────────────────────────────────────────────────────┤
│ Blog Writer                                              │
│ Transform rough ideas into polished blog posts           │
│                                                          │
│ Parameters:                                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ idea *                                              │ │
│ │ Path to your idea/brain dump file                  │ │
│ │ [~/ideas/ai-agents.md                    ] [Browse]│ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ writings_dir *                                      │ │
│ │ Directory with your existing blog posts             │ │
│ │ [~/blog/                                 ] [Browse]│ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ instructions (optional)                             │ │
│ │ Additional guidance for the AI                      │ │
│ │ [Keep it under 1000 words                        ] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Examples:                                                │
│ make blog-write IDEA=rough_idea.md WRITINGS=my_blog/    │
│                                                          │
│                              [▶ Run Scenario]            │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Fill in required parameters
- Optionally add instructions
- Click Run

### Step 3: Real-Time Execution (2-5 minutes)
```
User clicks "▶ Run Scenario"

Redirects to: /executions/{id}

Sees (LEFT SIDE - Main View):
┌─────────────────────────────────────────────────────────┐
│ Execution in Progress                      [●] Connected │
├─────────────────────────────────────────────────────────┤
│ Active Agents:                                           │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⟳ style_analyzer                                   │ │
│ │ Analyzing writing patterns from 5 posts...          │ │
│ │ ████████████░░░░░░░░ 60%                           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⏸ writer_agent                                     │ │
│ │ Waiting for style analysis...                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⏸ editor_agent                                     │ │
│ │ Ready to review when draft complete                 │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Execution Logs:                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [info] Starting blog_writer...                      │ │
│ │ [info] Found 5 existing posts                       │ │
│ │ [info] Extracting writing style...                  │ │
│ │ [info] Identified key patterns: conversational,     │ │
│ │        technical, example-driven                     │ │
│ │ [info] Generating draft...                          │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

RIGHT SIDE - Chat Sidebar:
┌─────────────────────────────────┐
│ Scenario Feedback               │
│ Provide feedback and input      │
├─────────────────────────────────┤
│                                 │
│ 👋 How can I help?              │
│ Type your feedback when the     │
│ scenario asks for input         │
│                                 │
│ [Type your feedback...    ] [Send] │
└─────────────────────────────────┘
```

**What Happens**:
1. Agent cards appear as agents start
2. Cards pulse when active (⟳ icon animates)
3. Progress bars fill smoothly
4. Logs stream in real-time
5. When scenario needs input, yellow banner appears: "💬 Scenario is waiting for your input"
6. User types feedback in chat
7. Scenario continues with user's input

### Step 4: Completion & Results (immediate)
```
When scenario completes:

┌─────────────────────────────────────────────────────────┐
│ ✓ Execution Complete                                    │
├─────────────────────────────────────────────────────────┤
│ Active Agents:                                           │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✓ style_analyzer                                    │ │
│ │ Completed: Extracted 12 style patterns              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✓ writer_agent                                      │ │
│ │ Completed: Generated 1,247-word draft               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ✓ editor_agent                                      │ │
│ │ Completed: Polished and finalized                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Results:                                                 │
│ 📄 building-with-ai-agents.md (3.2 KB)      [Download]  │
│ 📄 draft_iter_1.md (2.8 KB)                 [Download]  │
│                                                          │
│ Summary:                                                 │
│ • 1,247 words generated                                 │
│ • 5 sources analyzed                                    │
│ • 3 agents collaborated                                 │
│ • 2m 34s total time                                     │
│                                                          │
│ [Run Again] [← Back to Scenarios]                       │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Download results
- Review execution summary
- Run again with different parameters
- Go back to browse more scenarios

---

## Path 2: Create New Scenario

### Step 1: Open Create Page (Click "💬 Create New")
```
User clicks "💬 Create New" in navigation

Sees:
┌─────────────────────────────────────────────────────────┐
│ Create New Scenario                                      │
│ Chat with Ultrathink to design and build custom scenarios│
├─────────────────────────────────────────────────────────┤
│                                                          │
│          👋 How can I help?                              │
│                                                          │
│    Describe what you want to create and I'll help       │
│              build it step by step                       │
│                                                          │
│                                                          │
│                                                          │
│ [Describe what you want to create...       ] [Send]     │
│                                                          │
│ Quick ideas:                                             │
│ [💡 Create blog summarizer] [💡 Meeting notes tool]     │
│ [💡 Research analyzer]                                   │
└─────────────────────────────────────────────────────────┘
```

**User Actions**:
- Type their goal: "Help me create a tool that summarizes meeting transcripts"
- Or click a suggestion button

### Step 2: Conversational Design (5-10 minutes)
```
User types: "Help me create a tool that summarizes meeting transcripts"

Chat evolves:
┌─────────────────────────────────────────────────────────┐
│ [You] Help me create a tool that summarizes meeting     │
│       transcripts                                        │
│                                                          │
│ [AI] Great idea! Let me help you build a meeting        │
│      summarizer. I'll break this down:                  │
│                                                          │
│      1. Parse transcript structure                       │
│      2. Extract action items via AI                      │
│      3. Generate executive summary                       │
│      4. Format output                                    │
│                                                          │
│      Quick questions:                                    │
│      • What format are your transcripts? (Zoom, Teams,  │
│        plain text, etc.)                                 │
│      • Do you want to extract action items, or just     │
│        summarize discussion?                             │
│                                                          │
│ [You] Zoom transcripts. Extract action items and        │
│       summarize key decisions                            │
│                                                          │
│ [AI] Perfect! I'll create a scenario that:              │
│      ✓ Parses Zoom VTT format                           │
│      ✓ Identifies speakers and timestamps               │
│      ✓ Extracts action items (who, what, when)         │
│      ✓ Summarizes key decisions                         │
│      ✓ Generates markdown report                        │
│                                                          │
│      Creating the scenario now...                        │
│                                                          │
│      [Creating files...]                                 │
│      ✓ Created scenarios/meeting_summarizer/            │
│      ✓ Created README.md                                 │
│      ✓ Created __main__.py                              │
│      ✓ Created tests/                                    │
│                                                          │
│      Your scenario is ready!                             │
│      [Go to Meeting Summarizer →]                        │
└─────────────────────────────────────────────────────────┘

Session ID: ut_20251022_195500
```

**What Happens Behind the Scenes**:
1. User message → Backend → Ultrathink agent
2. Ultrathink orchestrates sub-agents to design scenario
3. Files are generated in `scenarios/meeting_summarizer/`
4. Scenario immediately appears in the main list
5. User can click to run it immediately

### Step 3: Test New Scenario (immediate)
```
User clicks "Go to Meeting Summarizer →"

Returns to main scenarios list, new card appears:
┌─────────────────────────────────────────────────────────┐
│  ╔═══════════════╗  ← NEW!                              │
│  ║ Meeting       ║                                       │
│  ║ Summarizer    ║                                       │
│  ║               ║                                       │
│  ║ Extract action║                                       │
│  ║ items from    ║                                       │
│  ║ Zoom meetings ║                                       │
│  ║               ║                                       │
│  ║ [NEW] 1 param ║                                       │
│  ╚═══════════════╝                                       │
└─────────────────────────────────────────────────────────┘
```

User clicks it, fills in transcript path, runs it immediately!

---

## Interactive Features

### Real-Time Feedback During Execution

**Scenario**: Blog Writer asks for feedback on draft

```
LEFT: Agent Activity
┌─────────────────────────────────┐
│ ✓ style_analyzer                │
│ ✓ writer_agent                  │
│   Generated draft (1,247 words) │
│                                 │
│ ⏸ editor_agent                 │
│   Waiting for your review...    │
└─────────────────────────────────┘

RIGHT: Chat Sidebar
┌─────────────────────────────────┐
│ ⚠️ Scenario is waiting for     │
│    your input                   │
├─────────────────────────────────┤
│ [AI] I've created a draft!      │
│      Review it and provide      │
│      feedback with [comments]   │
│      or type 'approve'          │
│                                 │
│ 📄 View draft_iter_1.md         │
│                                 │
│ [Type feedback...    ] [Send]   │
│                                 │
│ Quick actions:                  │
│ [Approve] [Needs work]          │
│ [Make shorter] [Add examples]   │
└─────────────────────────────────┘
```

**User Types**:
- "approve" → Editor agent continues
- "Make it more technical and add code examples" → Writer revises
- Quick button: Click "Add examples" → Sends predefined feedback

### Progress Visualization States

**Starting**:
```
⏸ agent_name
Ready to start...
```

**Running**:
```
⟳ agent_name (pulses)
Processing your request...
████████░░░░░░░░ 60%
```

**Completed**:
```
✓ agent_name
Completed: Generated 1,247 words
```

**Error**:
```
✗ agent_name
Error: File not found
```

---

## Ultrathink Scenario Creation - Detailed Flow

### Conversation Example

```
[You] Help me create a code review assistant

[AI] I'll help you build a code review assistant! Let me understand your needs:

     What should this tool do?
     • Analyze code quality?
     • Check for bugs/vulnerabilities?
     • Suggest improvements?
     • All of the above?

[You] All of the above, plus check if it follows our coding standards

[AI] Perfect! I'll create a comprehensive code reviewer that:

     ✓ Analyzes code quality (complexity, maintainability)
     ✓ Detects potential bugs and security issues
     ✓ Suggests improvements
     ✓ Checks against your coding standards

     What programming languages should it support?

[You] Python primarily, but TypeScript would be nice too

[AI] Got it! Creating your scenario with:

     Inputs:
     • code_file: Path to file to review
     • standards_doc: Your coding standards (optional)
     • language: Python or TypeScript

     Agents:
     • analyzer: Checks code quality and complexity
     • security_checker: Finds vulnerabilities
     • standards_validator: Compares to your guidelines
     • suggester: Provides improvement recommendations

     Output:
     • Review report (markdown)
     • Issues list (JSON)
     • Suggested fixes

     Creating files now...

     [Progress bar animates]

     ✓ Created scenarios/code_reviewer/
     ✓ Generated README.md
     ✓ Generated __main__.py with CLI interface
     ✓ Generated review_agents.py
     ✓ Generated tests/

     Your Code Reviewer scenario is ready!

     [View Scenario] [Run It Now]
```

---

## UI Layout Specs

### Main Views

**1. Home (Scenarios List)**
- Grid layout: 3 columns on desktop, 2 on tablet, 1 on mobile
- Card size: ~300px x 250px
- Hover effect: Lift with shadow
- Click: Navigate to scenario detail

**2. Scenario Detail/Form**
- Single column, max 800px wide
- Form fields stack vertically
- File inputs have [Browse] buttons
- Submit button: Full width, prominent
- Back button: Top left

**3. Execution View**
- Two-column on desktop: 2/3 execution, 1/3 chat
- Single column on mobile: Stack execution on top, chat below
- Sticky chat sidebar (scrolls independently)
- Agent cards: Stack vertically
- Logs: Fixed height, scrollable

**4. Create View (Ultrathink)**
- Full height chat interface
- Session ID badge at bottom
- Suggestion pills at bottom of input

### Color Scheme

**Light Mode**:
- Background: Gray-50
- Cards: White with gray-200 borders
- Primary: Indigo-600
- Success: Green-500
- Warning: Yellow-500
- Error: Red-500

**Dark Mode**:
- Background: Gray-900
- Cards: Gray-800 with gray-700 borders
- Primary: Indigo-500
- Success: Green-400
- Warning: Yellow-400
- Error: Red-400

### Animations

**Agent Cards**:
- Appear: Fade in + slide up (0.3s ease-out)
- Active: Pulse animation on icon (2s infinite)
- Complete: Icon changes + green flash (0.2s)

**Progress Bars**:
- Fill: Elastic easing (0.5s)
- Color: Gradient from indigo to green as approaches 100%

**Chat Messages**:
- Appear: Fade in + slide up (0.2s)
- User: From right
- AI: From left

**Logs**:
- Auto-scroll: Smooth scroll to bottom (0.3s)
- New line: Slight highlight flash (0.1s)

---

## User Interaction Patterns

### Keyboard Shortcuts (Future Enhancement)
- `Cmd/Ctrl + K`: Command palette
- `Cmd/Ctrl + /`: Focus chat input
- `Esc`: Close modals/go back
- `Enter`: Submit forms/chat
- `↑/↓`: Navigate suggestions

### Mouse Interactions
- **Hover**: Cards lift, show more details
- **Click card**: Navigate to detail
- **Click agent card**: Expand to show full logs
- **Click log line**: Copy to clipboard
- **Click file**: Download or preview

### Touch Interactions (Mobile)
- **Swipe right**: Go back
- **Pull down**: Refresh scenarios
- **Long press**: Show context menu

---

## Error Handling UX

### Friendly Error Messages

**Backend Connection Lost**:
```
⚠️ Connection Lost
Trying to reconnect...
[Reconnecting... ⟳]
```

**Scenario Failed**:
```
❌ Execution Failed
The scenario encountered an error:
"File not found: /path/to/file.md"

What to try:
• Check the file path exists
• Verify file permissions
• Review parameters

[Try Again] [← Back]
```

**Parameter Validation**:
```
⚠️ Invalid Parameter
Field 'idea' is required
Please provide a path to your markdown file

[Fix It]
```

---

## Success Celebrations

### Micro-Interactions

**Scenario Completes**:
- Green checkmark on all agent cards
- Subtle confetti animation (1 second)
- Success toast: "✓ Blog post created!" (3 seconds)

**New Scenario Created**:
- Success modal: "🎉 Your scenario is ready!"
- Confetti animation
- "Go to Scenario" button pulses

**First Execution**:
- Special badge: "🌟 First Run!"
- Encouragement message: "You're getting the hang of it!"

---

## Mobile Experience

### Responsive Adaptations

**Home (Mobile)**:
- Single column card list
- Larger tap targets (min 44px)
- Swipe gestures enabled

**Execution (Mobile)**:
- Stack layout: Agents → Logs → Chat
- Collapsible sections
- Floating chat button (bottom-right)
- Tap to expand agent details

**Create (Mobile)**:
- Full-screen chat
- Suggestion chips scroll horizontally
- Virtual keyboard doesn't cover input

---

## Accessibility

### Screen Reader Support
- All buttons have aria-labels
- Agent status announced: "Research agent: running, 60% complete"
- Form validation errors announced
- Success messages announced

### Keyboard Navigation
- Tab through all interactive elements
- Focus visible (outline)
- Skip to main content
- Esc to close/go back

### Color Contrast
- AA minimum for all text
- AAA for important text (headers, labels)
- No color-only indicators (icons + text)

---

## Performance Targets

- **First Paint**: <1s
- **Interactive**: <2s
- **WebSocket Connection**: <500ms
- **Agent Card Animation**: 60fps
- **Log Streaming**: <100ms latency
- **Message Send**: <200ms response

---

## Complete User Journey Map

```
Landing (0s)
  ↓ Browse
Scenario Card (5s)
  ↓ Click
Scenario Form (10s)
  ↓ Fill + Run
Execution View (15s)
  ↓ Watch
Agent Activity (2-5min)
  ↓ Provide feedback via chat
Completion (5min)
  ↓ Download
Results (immediate)
  ↓ Done or Run Again

OR

Landing (0s)
  ↓ Click "Create New"
Ultrathink Chat (5s)
  ↓ Describe goal
Conversation (5-10min)
  ↓ Answer questions
Scenario Generated (10min)
  ↓ Auto-navigate
New Scenario Card (immediate)
  ↓ Fill + Run
First Execution!
```

---

**This UX design makes Amplifier accessible, delightful, and powerful!** 🎨
