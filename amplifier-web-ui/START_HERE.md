# 🎨 Amplifier Studio - START HERE

**Your web UI is ready!** Here's how to see it in action.

## ⚡ Quick Start (3 Steps)

### Step 1: Install (first time only)
```bash
cd amplifier-web-ui/frontend
npm install
```

### Step 2: Start Servers

**Terminal 1:**
```bash
cd amplifier-web-ui
make dev-backend
```

**Terminal 2:**
```bash
cd amplifier-web-ui
make dev-frontend
```

### Step 3: Open Browser

Navigate to: **http://localhost:5173**

## ✨ What You'll See

### Landing Page
```
┌─────────────────────────────────────────┐
│  🎨 Amplifier Studio                    │
│  Where AI agents bring ideas to life    │
├─────────────────────────────────────────┤
│                                         │
│  [Blog Writer]    [Transcribe]          │
│  [Knowledge]      [Illustrate]          │
│  [+ more scenarios]                     │
│                                         │
└─────────────────────────────────────────┘
```

### Click a Scenario → See Details
```
┌─────────────────────────────────────────┐
│  Blog Writer                            │
│  Transform rough ideas into polished    │
│  blog posts                             │
├─────────────────────────────────────────┤
│  Parameters:                            │
│  • idea*: Path to markdown file         │
│  • writings_dir*: Your blog directory   │
│  • instructions: Additional guidance    │
│                                         │
│  [▶ Run Scenario]                       │
└─────────────────────────────────────────┘
```

### During Execution → Watch Agents Work
```
┌─────────────────────────────────────────┐
│  Execution in Progress        [●] Live │
├─────────────────────────────────────────┤
│  Active Agents:                         │
│                                         │
│  ⟳ Research Agent                      │
│  │  Finding recent AI articles...      │
│  └─ ████████░░░░ 80%                   │
│                                         │
│  ⏸ Writer Agent                        │
│  │  Waiting for research...            │
│                                         │
│  Logs:                                  │
│  [info] Started blog_writer             │
│  [info] Analyzing writing style...      │
│  [info] Generating draft...             │
└─────────────────────────────────────────┘
```

## 🎯 Try It Now

### Run Blog Writer

1. Click "Blog Writer" card
2. Enter paths:
   ```
   idea: scenarios/blog_writer/tests/sample_brain_dump.md
   writings_dir: scenarios/blog_writer/tests/sample_writings/
   ```
3. Click "▶ Run Scenario"
4. Watch the magic happen!

### What You'll See
- 🔍 Research agent analyzing your writing style
- ✍️ Writer agent creating the draft
- 📊 Editor agent polishing
- Real-time logs streaming
- Progress bars updating
- Final blog post when complete

## 📚 Documentation

- **BUILT.md** - Complete feature list and file structure
- **README.md** - Comprehensive setup guide
- **QUICK_START.md** - Alternative quick start
- **IMPLEMENTATION_PROGRESS.md** - Technical details

## 🔧 Troubleshooting

**Port already in use?**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn backend.api.main:app --port 8001
```

**Dependencies not installing?**
```bash
# Backend
cd .. && uv sync

# Frontend
cd frontend && rm -rf node_modules && npm install
```

**No scenarios showing?**
- Make sure you're running from the amplifier repo root context
- Check that `../scenarios/` exists relative to amplifier-web-ui
- Backend should show: "✅ Found X scenarios" on startup

## 🚀 That's It!

Your web UI is complete and ready to use. Open http://localhost:5173 and start visualizing your AI workflows!

Questions? Check the other docs or the detailed specs in `ai_working/web-ui-specs/`.

**Enjoy your new Amplifier Studio! 🎨**
