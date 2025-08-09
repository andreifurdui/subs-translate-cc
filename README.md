# Subtitle Translation System

A movie-focused subtitle translation system using Claude Code for intelligent content analysis and Romanian translation.

## Quick Start

### Fully Automated Workflow
```bash
# 0. Install Claude Code and make sure it works

# 1. Setup movie
mkdir movies/Your_Movie_Name
cp your_subtitles.srt movies/Your_Movie_Name/Your_Movie_Name_EN.srt

# 2. Generate metadata (NEW!)
python tools/analyze_movie.py movies/Your_Movie_Name analyze

# 3. Prepare chunks and prompts  
python tools/prep_translation.py movies/Your_Movie_Name

# 4. Automated translation
python tools/translate_batch.py movies/Your_Movie_Name translate

# 5. Assemble final Romanian subtitles
python tools/reassemble_translation.py movies/Your_Movie_Name assemble
```

## Features

- **Fully automated pipeline** - From .srt to translated .srt with zero manual steps
- **Intelligent content analysis** - Automated metadata generation via Claude Code
- **Context-aware translation** - Rich story context improves translation quality
- **Movie-based organization** - Each project in its own folder
- **Progress tracking** - Resume from interruptions, monitor status
- **Works with any genre** - No hardcoded assumptions, adapts to any film
- **Professional results** - Context-aware Romanian translations

## Documentation

- `docs/COMPLETE_AUTOMATION.md` - **Zero-interaction automation guide (recommended)**
- `tools/analyze_subtitles_prompt.md` - Content analysis template

## Project Structure

```
subs-translate-cc/
├── tools/         # Translation tools
├── docs/          # Documentation  
└── movies/        # Your movie projects
```
