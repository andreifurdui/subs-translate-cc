#!/usr/bin/env python3
"""
Automated Subtitle Translation Script
Processes all translation prompts through Claude Code automatically.
"""

import os
import sys
import subprocess
import glob
import argparse
from typing import List
import time

class BatchTranslator:
    def __init__(self, movie_folder: str):
        self.movie_folder = movie_folder
        self.movie_name = os.path.basename(movie_folder.rstrip('/'))
        self.prompts_dir = os.path.join(movie_folder, 'translation_prompts')
        self.translated_dir = os.path.join(movie_folder, 'translated')
        self.claude_md_path = os.path.join(movie_folder, 'CLAUDE.md')
        
        # Create translated directory if it doesn't exist
        os.makedirs(self.translated_dir, exist_ok=True)
    
    def get_prompt_files(self) -> List[str]:
        """Get all prompt files in order."""
        if not os.path.exists(self.prompts_dir):
            raise FileNotFoundError(f"Translation prompts directory not found: {self.prompts_dir}")
        
        prompt_pattern = os.path.join(self.prompts_dir, "prompt_chunk_*.txt")
        prompt_files = glob.glob(prompt_pattern)
        
        if not prompt_files:
            raise FileNotFoundError(f"No prompt files found in {self.prompts_dir}")
        
        # Sort by chunk number
        prompt_files.sort(key=lambda x: int(x.split('_chunk_')[1].split('.')[0]))
        return prompt_files
    
    def get_existing_translations(self) -> List[str]:
        """Get list of existing translation files."""
        translation_pattern = os.path.join(self.translated_dir, "chunk_*_RO.txt")
        return glob.glob(translation_pattern)
    
    def extract_chunk_number(self, filepath: str) -> int:
        """Extract chunk number from filename."""
        if 'prompt_chunk_' in filepath:
            return int(filepath.split('prompt_chunk_')[1].split('.')[0])
        elif 'chunk_' in filepath and '_RO.txt' in filepath:
            return int(filepath.split('chunk_')[1].split('_RO.txt')[0])
        return 0
    
    def translate_chunk(self, prompt_file: str, output_file: str, claude_code_cmd: str = "claude-code") -> bool:
        """Translate a single chunk using Claude Code."""
        try:
            print(f"Translating {os.path.basename(prompt_file)}...")
            
            # Read the prompt content
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            
            # Convert output_file to absolute path before changing directories
            output_file = os.path.abspath(output_file)
            
            # Change to movie directory so Claude Code can read CLAUDE.md
            original_dir = os.getcwd()
            os.chdir(self.movie_folder)
            
            try:
                # Execute Claude Code with the prompt
                result = subprocess.run(
                    [claude_code_cmd],
                    input=prompt_content,
                    text=True,
                    capture_output=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode == 0:
                    # Save the translation (now using absolute path)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.stdout)
                    
                    print(f"✓ Saved translation to {os.path.basename(output_file)}")
                    return True
                else:
                    print(f"✗ Claude Code error: {result.stderr}")
                    return False
                    
            finally:
                os.chdir(original_dir)
                
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout translating {os.path.basename(prompt_file)}")
            return False
        except Exception as e:
            print(f"✗ Error translating {os.path.basename(prompt_file)}: {e}")
            return False
    
    def translate_all(self, claude_code_cmd: str = "claude-code", resume: bool = True) -> int:
        """Translate all chunks."""
        if not os.path.exists(self.claude_md_path):
            print(f"Warning: CLAUDE.md not found at {self.claude_md_path}")
            print("Context may not be available. Run prep_translation.py first.")
        
        prompt_files = self.get_prompt_files()
        existing_translations = self.get_existing_translations() if resume else []
        
        # Get chunk numbers of existing translations
        existing_chunks = {self.extract_chunk_number(f) for f in existing_translations}
        
        total_chunks = len(prompt_files)
        completed = len(existing_chunks)
        
        print(f"Found {total_chunks} chunks to translate")
        if resume and existing_chunks:
            print(f"Resuming: {completed} chunks already completed")
        
        successful = 0
        
        for prompt_file in prompt_files:
            chunk_num = self.extract_chunk_number(prompt_file)
            output_file = os.path.join(self.translated_dir, f"chunk_{chunk_num:02d}_RO.txt")
            
            # Skip if already translated and resuming
            if resume and chunk_num in existing_chunks:
                print(f"⏭  Skipping chunk {chunk_num:02d} (already translated)")
                successful += 1
                continue
            
            if self.translate_chunk(prompt_file, output_file, claude_code_cmd):
                successful += 1
            else:
                print(f"Failed to translate chunk {chunk_num:02d}")
                # Continue with next chunk instead of stopping
        
        print(f"\nTranslation complete: {successful}/{total_chunks} chunks successful")
        return successful
    
    def show_progress(self) -> None:
        """Show current translation progress."""
        try:
            prompt_files = self.get_prompt_files()
            existing_translations = self.get_existing_translations()
            
            total_chunks = len(prompt_files)
            completed_chunks = len(existing_translations)
            
            print(f"Translation Progress for {self.movie_name}:")
            print(f"Completed: {completed_chunks}/{total_chunks} ({completed_chunks/total_chunks*100:.1f}%)")
            
            if completed_chunks < total_chunks:
                completed_nums = {self.extract_chunk_number(f) for f in existing_translations}
                all_nums = {self.extract_chunk_number(f) for f in prompt_files}
                missing = sorted(all_nums - completed_nums)
                print(f"Missing chunks: {missing}")
            else:
                print("✓ All chunks completed! Ready for assembly.")
                
        except FileNotFoundError as e:
            print(f"Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Automated subtitle translation using Claude Code')
    parser.add_argument('movie_folder', help='Path to the movie folder')
    parser.add_argument('command', choices=['translate', 'progress'], 
                       help='Command: translate all chunks or show progress')
    parser.add_argument('--claude-cmd', default='claude', 
                       help='Claude Code command (default: claude-code)')
    parser.add_argument('--no-resume', action='store_true', 
                       help='Start fresh (don\'t resume from existing translations)')
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nExamples:")
        print("  python translate_batch.py movies/My_Movie translate")
        print("  python translate_batch.py movies/My_Movie progress")
        print("  python translate_batch.py movies/My_Movie translate --claude-cmd 'claude'")
        sys.exit(1)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.movie_folder):
        print(f"Error: Movie folder {args.movie_folder} not found")
        sys.exit(1)
    
    translator = BatchTranslator(args.movie_folder)
    
    try:
        if args.command == 'progress':
            translator.show_progress()
        elif args.command == 'translate':
            successful = translator.translate_all(
                claude_code_cmd=args.claude_cmd, 
                resume=not args.no_resume
            )
            
            if successful > 0:
                print(f"\nNext step: python tools/reassemble_translation.py {args.movie_folder} assemble")
            
    except KeyboardInterrupt:
        print("\nTranslation interrupted. Progress saved. Run again to resume.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()