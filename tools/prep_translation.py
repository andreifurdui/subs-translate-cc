#!/usr/bin/env python3
"""
Subtitle Translation Preparation Script
Prepares SRT files for translation using Claude Code by chunking and generating context.
"""

import re
import os
import json
from typing import List, Dict

class SRTProcessor:
    def __init__(self, movie_folder: str):
        self.movie_folder = movie_folder
        self.movie_name = os.path.basename(movie_folder.rstrip('/'))
        self.srt_path = self._find_english_subtitle()
        self.metadata_path = os.path.join(movie_folder, 'metadata.json')
        self.chunks_dir = os.path.join(movie_folder, 'chunks')
        self.prompts_dir = os.path.join(movie_folder, 'translation_prompts')
        self.subtitles = []
        self.story_context = ""
        self.metadata = None
        
        # Create directories if they don't exist
        os.makedirs(self.chunks_dir, exist_ok=True)
        os.makedirs(self.prompts_dir, exist_ok=True)
        
    def read_srt_with_encoding_detection(self) -> str:
        """Read SRT file content with automatic encoding detection."""
        encodings = ['utf-8', 'utf-16-le', 'utf-8-sig', 'iso-8859-1', 'cp1252', 'latin1', 'windows-1252']
        
        for encoding in encodings:
            try:
                with open(self.srt_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✓ Successfully read subtitle file using {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
        
        # Fallback with error handling
        try:
            with open(self.srt_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Unable to read subtitle file: {e}")
    
    def parse_srt(self) -> List[Dict]:
        """Parse SRT file into structured subtitle blocks."""
        content = self.read_srt_with_encoding_detection()
        print(content[:300] + "...")  # Debug: print first 300 chars of content
        
        # Remove BOM if present
        content = content.lstrip('\ufeff')
        
        # Split by double newlines to get subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        subtitles = []
        for block in blocks:
            if not block.strip():
                continue
                
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                try:
                    seq_num = int(lines[0].strip())
                    timing = lines[1].strip()
                    text = '\n'.join(lines[2:]).strip()
                    
                    subtitles.append({
                        'sequence': seq_num,
                        'timing': timing,
                        'text': text,
                        'original_block': block
                    })
                except ValueError:
                    continue
        
        self.subtitles = subtitles
        return subtitles
    
    def _find_english_subtitle(self) -> str:
        """Find the English subtitle file in the movie folder."""
        # Look for files ending with _EN.srt first
        en_pattern = os.path.join(self.movie_folder, '*_EN.srt')
        import glob
        en_files = glob.glob(en_pattern)
        
        if en_files:
            return en_files[0]
        
        # Fallback to any .srt file
        srt_pattern = os.path.join(self.movie_folder, '*.srt')
        srt_files = glob.glob(srt_pattern)
        
        if srt_files:
            return srt_files[0]
        
        raise FileNotFoundError(f"No subtitle file found in {self.movie_folder}")
    
    def load_metadata(self) -> Dict:
        """Load metadata from JSON file."""
        if not self.metadata_path:
            raise ValueError("No metadata file specified. Use --metadata option or provide metadata.json")
        
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        return self.metadata
    
    def generate_story_context(self) -> str:
        """Generate story context from metadata for translation context."""
        if not self.metadata:
            if not os.path.exists(self.metadata_path):
                # Fallback to basic analysis if no metadata provided
                return self._generate_basic_context()
            self.load_metadata()
        
        meta = self.metadata
        
        # Extract information from metadata
        genre = meta.get('film_metadata', {}).get('genre', 'Unknown')
        setting = meta.get('film_metadata', {}).get('setting', {})
        characters = meta.get('characters', {})
        themes = meta.get('themes', {})
        translation_context = meta.get('translation_context', {})
        
        # Build context string
        context_parts = []
        context_parts.append("STORY CONTEXT for Translation:")
        context_parts.append("")
        
        # Basic film info
        if meta.get('story_summary'):
            context_parts.append(f"STORY: {meta['story_summary']}")
            context_parts.append("")
        
        context_parts.append(f"GENRE: {genre.title()}")
        if meta.get('film_metadata', {}).get('subgenres'):
            subgenres = ', '.join(meta['film_metadata']['subgenres'])
            context_parts.append(f"SUBGENRES: {subgenres}")
        context_parts.append("")
        
        # Characters
        main_chars = characters.get('main_characters', [])
        if main_chars:
            context_parts.append(f"MAIN CHARACTERS: {', '.join(main_chars)}")
        
        secondary_chars = characters.get('secondary_characters', [])
        if secondary_chars:
            context_parts.append(f"SECONDARY CHARACTERS: {', '.join(secondary_chars)}")
        
        if characters.get('character_relationships'):
            context_parts.append(f"RELATIONSHIPS: {characters['character_relationships']}")
        context_parts.append("")
        
        # Setting
        if setting.get('location'):
            context_parts.append(f"LOCATION: {setting['location']}")
        if setting.get('time_period'):
            context_parts.append(f"TIME PERIOD: {setting['time_period']}")
        if setting.get('environment'):
            env = ', '.join(setting['environment'])
            context_parts.append(f"ENVIRONMENTS: {env}")
        context_parts.append("")
        
        # Themes
        primary_themes = themes.get('primary_themes', [])
        if primary_themes:
            context_parts.append("THEMES:")
            for theme in primary_themes:
                context_parts.append(f"- {theme}")
            context_parts.append("")
        
        # Cultural elements
        cultural_elements = themes.get('cultural_elements', [])
        if cultural_elements:
            context_parts.append("KEY CULTURAL ELEMENTS:")
            for element in cultural_elements:
                context_parts.append(f"- {element}")
            context_parts.append("")
        
        # Translation notes
        context_parts.append("TRANSLATION NOTES:")
        
        # Add proper nouns to preserve
        proper_nouns = translation_context.get('special_terminology', {}).get('proper_nouns', [])
        if proper_nouns:
            context_parts.append(f"- Preserve these names/terms exactly: {', '.join(proper_nouns)}")
        
        # Add cultural terms
        cultural_terms = translation_context.get('special_terminology', {}).get('cultural_terms', [])
        if cultural_terms:
            context_parts.append(f"- Handle these cultural terms carefully: {', '.join(cultural_terms)}")
        
        # Add register information
        register = translation_context.get('register', '')
        if register:
            context_parts.append(f"- Use {register} register/tone in Romanian")
        
        # Add specific translation notes
        translation_notes = translation_context.get('translation_notes', [])
        for note in translation_notes:
            context_parts.append(f"- {note}")
        
        # Always add formatting preservation
        context_parts.append("- Preserve formatting (dashes for dialogue, ellipses, etc.)")
        
        context = "\n".join(context_parts)
        self.story_context = context
        return context
    
    def _generate_basic_context(self) -> str:
        """Fallback basic context generation when no metadata provided."""
        if not self.subtitles:
            self.parse_srt()
        
        all_text = ' '.join([sub['text'] for sub in self.subtitles])
        
        # Basic character name detection
        character_mentions = re.findall(r'\b[A-Z][a-z]{2,}\b', all_text)
        # Filter out common English words
        common_words = {'The', 'And', 'But', 'You', 'Are', 'Can', 'Was', 'Not', 'Now', 'Get', 'Got', 'Let', 'Put', 'How', 'Why', 'Who', 'What', 'When', 'Where', 'They', 'She', 'Him', 'Her', 'His', 'All', 'One', 'Two', 'Yes', 'Out', 'Off', 'Run', 'Come', 'Take', 'Make', 'Look', 'See', 'Know', 'Think', 'Want', 'Like', 'Time', 'Good', 'Bad', 'Big', 'Old', 'New', 'Right', 'Left', 'Long', 'Last', 'Next', 'First', 'Best', 'Day', 'Night', 'Here', 'There', 'Back', 'Down', 'Over', 'After', 'Before'}
        common_names = [name for name in set(character_mentions) if character_mentions.count(name) >= 3 and name not in common_words]
        
        context = f"""STORY CONTEXT for Translation:
        
WARNING: No metadata file provided. Using basic analysis.

MAIN CHARACTERS: {', '.join(common_names[:10]) if common_names else 'Unknown'}

TRANSLATION NOTES:
- Preserve character names exactly as shown
- Maintain appropriate cultural and emotional tone
- Preserve formatting (dashes for dialogue, ellipses, etc.)
- For best results, use metadata analysis (see analyze_subtitles_prompt.md)
"""
        
        self.story_context = context
        return context
    
    def create_chunks(self, chunk_size: int = 15) -> List[Dict]:
        """Split subtitles into manageable chunks for translation."""
        if not self.subtitles:
            self.parse_srt()
        
        chunks = []
        for i in range(0, len(self.subtitles), chunk_size):
            chunk_subtitles = self.subtitles[i:i + chunk_size]
            chunk = {
                'chunk_id': len(chunks) + 1,
                'start_sequence': chunk_subtitles[0]['sequence'],
                'end_sequence': chunk_subtitles[-1]['sequence'],
                'subtitles': chunk_subtitles,
                'srt_format': self._format_chunk_as_srt(chunk_subtitles)
            }
            chunks.append(chunk)
        
        return chunks
    
    def _format_chunk_as_srt(self, chunk_subtitles: List[Dict]) -> str:
        """Format a chunk of subtitles as SRT format for translation."""
        srt_text = ""
        for sub in chunk_subtitles:
            srt_text += f"{sub['sequence']}\n{sub['timing']}\n{sub['text']}\n\n"
        return srt_text.strip()
    
    def save_chunks_for_translation(self):
        """Save chunks and context to files for Claude Code translation."""
        
        # Generate story context
        story_context = self.generate_story_context()
        
        # Save story context
        context_file = os.path.join(self.chunks_dir, '00_context.txt')
        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(story_context)
        
        # Create CLAUDE.md for persistent context
        claude_md_content = f"""# Translation Context for {self.movie_name}

{story_context}

---

You are an expert English-to-Romanian subtitle translator. The above context provides important information about this film for accurate translation. When translating subtitle chunks, maintain the exact SRT timing format, preserve character names, and follow the cultural guidance provided."""
        
        claude_md_file = os.path.join(self.movie_folder, 'CLAUDE.md')
        with open(claude_md_file, 'w', encoding='utf-8') as f:
            f.write(claude_md_content)
        
        # Save translation prompt template (for reference)
        prompt_template = """You are an expert English-to-Romanian subtitle translator specializing in film dialogue.

TASK: Translate the following English subtitles to Romanian while:
1. Preserving the exact SRT timing format (XX:XX:XX,XXX --> XX:XX:XX,XXX)
2. Keeping sequence numbers identical
3. Maintaining dialogue formatting (dashes, ellipses, etc.)
4. Preserving character names exactly as shown
5. Using natural Romanian that matches the emotional tone
6. Properly translating idioms and cultural references
7. Maintaining the same line structure where possible

Translate this chunk:

{srt_chunk}

Respond with ONLY the translated SRT format, no additional explanation."""

        template_file = os.path.join(self.chunks_dir, 'prompt_template.txt')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(prompt_template)
        
        # Save chunks and generate individual prompts
        chunks = self.create_chunks()
        for chunk in chunks:
            # Save chunk data
            chunk_filename = os.path.join(self.chunks_dir, f"chunk_{chunk['chunk_id']:02d}.txt")
            with open(chunk_filename, 'w', encoding='utf-8') as f:
                f.write(f"CHUNK {chunk['chunk_id']}\n")
                f.write(f"Sequences {chunk['start_sequence']}-{chunk['end_sequence']}\n")
                f.write("="*50 + "\n\n")
                f.write(chunk['srt_format'])
            
            # Generate individual translation prompt
            individual_prompt = f"""Translate the following English subtitles to Romanian while:
1. Preserving the exact SRT timing format (XX:XX:XX,XXX --> XX:XX:XX,XXX)
2. Keeping sequence numbers identical
3. Maintaining dialogue formatting (dashes, ellipses, etc.)
4. Preserving character names exactly as shown
5. Using natural Romanian that matches the emotional tone
6. Properly translating idioms and cultural references
7. Maintaining the same line structure where possible

Translate this chunk:

{chunk['srt_format']}

Respond with ONLY the translated SRT format, no additional explanation."""
            
            # Save individual prompt file
            prompt_filename = os.path.join(self.prompts_dir, f"prompt_chunk_{chunk['chunk_id']:02d}.txt")
            with open(prompt_filename, 'w', encoding='utf-8') as f:
                f.write(individual_prompt)
        
        return chunks

def main():
    """Main function to process movie folder."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare movie subtitles for translation')
    parser.add_argument('movie_folder', help='Path to the movie folder containing subtitle file')
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nExample: python prep_translation.py movies/My_Movie_2023")
        sys.exit(1)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.movie_folder):
        print(f"Error: Movie folder {args.movie_folder} not found")
        sys.exit(1)
    
    if not os.path.isdir(args.movie_folder):
        print(f"Error: {args.movie_folder} is not a directory")
        sys.exit(1)
    
    try:
        processor = SRTProcessor(args.movie_folder)
        movie_name = processor.movie_name
        
        print(f"Processing movie: {movie_name}")
        print(f"Subtitle file: {os.path.basename(processor.srt_path)}")
        
        if os.path.exists(processor.metadata_path):
            print(f"Using metadata: metadata.json")
        else:
            print("WARNING: No metadata.json found. Using basic analysis.")
            print("For better results, create metadata.json using analyze_subtitles_prompt.md")
        
        subtitles = processor.parse_srt()
        print(f"Found {len(subtitles)} subtitle entries")
        
        chunks = processor.save_chunks_for_translation()
        print(f"Created {len(chunks)} translation chunks in /chunks")
        
        print("\nNext steps:")
        print(f"AUTOMATED: python tools/translate_batch.py movies/{processor.movie_name} translate")
        print("OR MANUAL:")
        print("1. Review the context in CLAUDE.md (provides persistent context)")
        print("2. Translate chunks using translation_prompts/prompt_chunk_XX.txt with Claude Code")
        print("3. Save translations as translated/chunk_XX_RO.txt")
        print("4. Run reassemble script to create final Romanian subtitles")
        
        if not os.path.exists(processor.metadata_path):
            print("\nRECOMMENDATION: Generate metadata.json for better translation quality")
            print(f"AUTOMATED: python tools/analyze_movie.py movies/{processor.movie_name} analyze")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()