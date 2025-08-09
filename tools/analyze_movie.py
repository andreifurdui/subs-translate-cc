#!/usr/bin/env python3
"""
Automated Movie Metadata Generation Script
Analyzes subtitle content using Claude Code to generate metadata.json automatically.
"""

import os
import sys
import subprocess
import argparse
import json
import glob
from typing import Optional, Dict

class MovieAnalyzer:
    def __init__(self, movie_folder: str):
        self.movie_folder = movie_folder
        self.movie_name = os.path.basename(movie_folder.rstrip('/'))
        self.metadata_path = os.path.join(movie_folder, 'metadata.json')
        self.srt_path = self._find_english_subtitle()
        
    def _find_english_subtitle(self) -> str:
        """Find the English subtitle file in the movie folder."""
        # Look for files ending with _EN.srt first
        en_pattern = os.path.join(self.movie_folder, '*_EN.srt')
        en_files = glob.glob(en_pattern)
        
        if en_files:
            return en_files[0]
        
        # Fallback to any .srt file
        srt_pattern = os.path.join(self.movie_folder, '*.srt')
        srt_files = glob.glob(srt_pattern)
        
        if srt_files:
            return srt_files[0]
        
        raise FileNotFoundError(f"No subtitle file found in {self.movie_folder}")
    
    def read_analysis_prompt_template(self) -> str:
        """Read the analysis prompt template."""
        template_path = os.path.join(os.path.dirname(__file__), 'analyze_subtitles_prompt.md')
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Analysis prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        return template_content
    
    def read_subtitle_content(self) -> str:
        """Read subtitle content with automatic encoding detection."""
        # Try common encodings in order of likelihood
        encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252', 'latin1']
        
        for encoding in encodings:
            try:
                with open(self.srt_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✓ Successfully read subtitle file using {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, try with error handling
        try:
            with open(self.srt_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            print("⚠ Warning: Some characters may be corrupted due to encoding issues")
            return content
        except Exception as e:
            raise ValueError(f"Unable to read subtitle file: {e}")
    
    def create_analysis_prompt(self) -> str:
        """Create the complete analysis prompt with subtitle content injected."""
        # Read the template
        template = self.read_analysis_prompt_template()
        
        # Read subtitle content with encoding detection
        subtitle_content = self.read_subtitle_content()
        
        # Create the analysis prompt by extracting the core prompt and injecting subtitle content
        analysis_prompt = """You are an expert film analyst. Analyze the provided English subtitle file and generate structured metadata for translation purposes. 

**TASK:** Create a comprehensive JSON metadata file with the following information:

```json
{
  "film_metadata": {
    "genre": "string - primary genre (drama, comedy, action, etc.)",
    "subgenres": ["list", "of", "secondary", "genres"],
    "setting": {
      "location": "string - geographic location/country",
      "time_period": "string - when story takes place",
      "environment": ["list", "of", "main", "settings"]
    },
    "tone": "string - overall emotional tone (serious, lighthearted, tense, etc.)"
  },
  "characters": {
    "main_characters": ["list", "of", "main", "character", "names"],
    "secondary_characters": ["list", "of", "secondary", "character", "names"],
    "character_relationships": "string - brief description of key relationships"
  },
  "themes": {
    "primary_themes": ["list", "of", "main", "themes"],
    "cultural_elements": ["list", "of", "cultural", "references"],
    "sensitive_topics": ["list", "of", "sensitive", "content", "areas"]
  },
  "translation_context": {
    "target_language": "Romanian",
    "register": "string - formal/informal/mixed appropriate for content",
    "special_terminology": {
      "proper_nouns": ["names", "places", "to", "preserve"],
      "cultural_terms": ["terms", "requiring", "careful", "translation"],
      "technical_terms": ["specialized", "vocabulary", "if", "any"]
    },
    "translation_notes": [
      "Specific guidance for Romanian translation",
      "Cultural adaptation notes",
      "Tone preservation guidelines"
    ]
  },
  "story_summary": "2-3 sentence summary of the plot for translation context"
}
```

**INSTRUCTIONS:**
1. Read through ALL the subtitle content carefully
2. Identify patterns in dialogue and character interactions  
3. Detect cultural, religious, or regional references
4. Note the emotional register and formality level
5. Create translation-specific guidance based on the content
6. Respond with ONLY valid JSON format, no additional explanation

**SUBTITLE CONTENT TO ANALYZE:**
```
{subtitle_content}
```

Respond with ONLY the JSON metadata, no additional explanation or markdown formatting."""
        
        # Use string replacement instead of format to avoid issues with braces in subtitle content
        analysis_prompt = analysis_prompt.replace("{subtitle_content}", subtitle_content)
        
        return analysis_prompt
    
    def extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from Claude response that may contain markdown formatting."""
        response_text = response_text.strip()
        
        # Look for JSON in ```json blocks
        import re
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # Look for JSON in ``` blocks
        code_match = re.search(r'```\s*\n(.*?)\n```', response_text, re.DOTALL)
        if code_match:
            potential_json = code_match.group(1).strip()
            if potential_json.startswith('{') and potential_json.endswith('}'):
                return potential_json
        
        # Look for content that starts and ends with braces
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            return brace_match.group(0)
        
        # Return original if no patterns found
        return response_text

    def validate_json_metadata(self, raw_response: str) -> Dict:
        """Extract and validate JSON metadata from Claude response."""
        try:
            # Extract JSON from markdown formatting
            json_text = self.extract_json_from_response(raw_response)
            
            # Try to parse the JSON
            metadata = json.loads(json_text)
            
            # Basic structure validation
            required_keys = ['film_metadata', 'characters', 'themes', 'translation_context', 'story_summary']
            for key in required_keys:
                if key not in metadata:
                    raise ValueError(f"Missing required key: {key}")
            
            # Validate film_metadata structure
            if 'genre' not in metadata['film_metadata']:
                raise ValueError("Missing genre in film_metadata")
            
            # Validate characters structure
            if 'main_characters' not in metadata['characters']:
                raise ValueError("Missing main_characters in characters")
            
            print("✓ JSON metadata validated successfully")
            return metadata
            
        except json.JSONDecodeError as e:
            print("Debug: Failed to parse JSON. Raw response preview:")
            print(raw_response[:300] + "..." if len(raw_response) > 300 else raw_response)
            print(f"Extracted JSON preview:")
            print(json_text[:300] + "..." if len(json_text) > 300 else json_text)
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Metadata validation failed: {e}")
    
    def analyze_movie(self, claude_code_cmd: str = "claude-code", force: bool = False) -> bool:
        """Analyze the movie and generate metadata.json."""
        
        # Check if metadata already exists
        if os.path.exists(self.metadata_path) and not force:
            print(f"✓ metadata.json already exists for {self.movie_name}")
            print("Use --force to regenerate")
            return True
        
        print(f"Analyzing movie: {self.movie_name}")
        print(f"Subtitle file: {os.path.basename(self.srt_path)}")
        
        try:
            # Create the analysis prompt
            prompt = self.create_analysis_prompt()
            
            # Execute Claude Code with the analysis prompt
            print("Running analysis with Claude Code...")
            result = subprocess.run(
                [claude_code_cmd],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=600  # 10 minutes timeout for analysis
            )
            
            if result.returncode == 0:
                # Validate and save the metadata
                metadata = self.validate_json_metadata(result.stdout)
                
                with open(self.metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                print(f"✓ Generated metadata.json for {self.movie_name}")
                return True
            else:
                print(f"✗ Claude Code error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Analysis timed out (10 minutes)")
            return False
    
    def show_metadata_info(self) -> None:
        """Show information about existing metadata."""
        if not os.path.exists(self.metadata_path):
            print(f"No metadata.json found for {self.movie_name}")
            return
        
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"Metadata for {self.movie_name}:")
            print(f"Genre: {metadata.get('film_metadata', {}).get('genre', 'Unknown')}")
            
            main_chars = metadata.get('characters', {}).get('main_characters', [])
            if main_chars:
                print(f"Main Characters: {', '.join(main_chars[:5])}")
            
            themes = metadata.get('themes', {}).get('primary_themes', [])
            if themes:
                print(f"Primary Themes: {', '.join(themes[:3])}")
            
            story = metadata.get('story_summary', '')
            if story:
                print(f"Story: {story[:100]}{'...' if len(story) > 100 else ''}")
                
        except Exception as e:
            print(f"Error reading metadata: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Automated movie metadata generation using Claude Code')
    parser.add_argument('movie_folder', help='Path to the movie folder')
    parser.add_argument('command', choices=['analyze', 'info'], 
                       help='Command: analyze movie or show metadata info')
    parser.add_argument('--claude-cmd', default='claude', 
                       help='Claude Code command (default: claude-code)')
    parser.add_argument('--force', action='store_true', 
                       help='Force regeneration even if metadata.json exists')
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\\nExamples:")
        print("  python analyze_movie.py movies/My_Movie analyze")
        print("  python analyze_movie.py movies/My_Movie info")
        print("  python analyze_movie.py movies/My_Movie analyze --force")
        sys.exit(1)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.movie_folder):
        print(f"Error: Movie folder {args.movie_folder} not found")
        sys.exit(1)
    
    analyzer = MovieAnalyzer(args.movie_folder)
    
    if args.command == 'analyze':
        success = analyzer.analyze_movie(
            claude_code_cmd=args.claude_cmd,
            force=args.force
        )
        
        if success:
            print(f"\\nNext step: python tools/prep_translation.py {args.movie_folder}")
        else:
            sys.exit(1)
            
    elif args.command == 'info':
        analyzer.show_metadata_info()
    else:
        print("Invalid command. Use 'analyze' or 'info'.")
        sys.exit(1)

if __name__ == "__main__":
    main()