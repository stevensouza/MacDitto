# Session State: MacDitto

**Last Updated:** 2026-02-15

## Current Task
Requirements gathering and architecture design for MacDitto

## Status
**Completed:**
- Initial environment scan of source Mac
- Identified all Homebrew formulae (12 direct), casks (4), applications (20+ non-standard)
- Discovered Dock items, login startup items, shell configs, git config
- User answered all architecture questions
- Requirements document saved: `docs/REQUIREMENTS.md`

**In Progress:**
- Finalizing requirements before implementation

**Next Steps:**
1. User reviews requirements, suggests changes
2. Initialize git repo and create feature branch
3. Begin implementation (Scanner module first)

## Key Decisions Made
- App renamed from DevDitto to MacDitto
- Python + Flask web GUI
- Capture shell configs, git config, browser extensions, macOS prefs
- Manual instructions in both GUI and exported markdown
- JSON config files, Brewfile as backbone
- Profile snapshots with diff support

## Open Questions
- None currently blocking

## Project Location
`/Users/stevesouza/my/data/gitrepo/MacDitto/`
