#!/usr/bin/env python3
"""
Subtitle Translation Reassembly Script
Combines translated chunks back into a complete Romanian SRT file.
"""

import os
import re
import glob
from typing import List, Dict, Optional

class TranslationAssembler:
    def __init__(self, movie_folder: str):
        self.movie_folder = movie_folder
        self.movie_name = os.path.basename(movie_folder.rstrip('/'))
        self.translated_chunks_dir = os.path.join(movie_folder, 'translated')
        self.chunks_dir = os.path.join(movie_folder, 'chunks')
        self.output_chunks = []
        
    def collect_translated_chunks(self) -> List[Dict]:
        """Collect all translated chunk files in order."""
        if not os.path.exists(self.translated_chunks_dir):
            raise FileNotFoundError(f"Translated chunks directory '{self.translated_chunks_dir}' not found")
        
        # Find all translated chunk files
        chunk_pattern = os.path.join(self.translated_chunks_dir, "chunk_*_RO.txt")
        chunk_files = glob.glob(chunk_pattern)
        
        if not chunk_files:
            raise FileNotFoundError(f"No translated chunk files found in '{self.translated_chunks_dir}'\nExpected pattern: chunk_XX_RO.txt")
        
        # Sort files by chunk number
        chunk_files.sort(key=lambda x: int(re.search(r'chunk_(\d+)_RO', x).group(1)))
        
        chunks = []
        for chunk_file in chunk_files:
            chunk_num = int(re.search(r'chunk_(\d+)_RO', chunk_file).group(1))
            
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            chunks.append({
                'chunk_number': chunk_num,
                'file_path': chunk_file,
                'content': content
            })
        
        return chunks
    
    def parse_srt_content(self, srt_text: str) -> List[Dict]:
        """Parse SRT content into subtitle entries."""
        # Remove BOM if present
        srt_text = srt_text.lstrip('\ufeff')
        
        # Split by double newlines to get subtitle blocks
        blocks = re.split(r'\n\s*\n', srt_text.strip())
        
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
                        'text': text
                    })
                except ValueError:
                    print(f"Warning: Could not parse subtitle block: {block[:50]}...")
                    continue
        
        return subtitles
    
    def validate_translation(self, chunks: List[Dict]) -> bool:
        """Validate that translation maintains proper SRT structure."""
        all_subtitles = []
        
        for chunk in chunks:
            chunk_subtitles = self.parse_srt_content(chunk['content'])
            all_subtitles.extend(chunk_subtitles)
        
        if not all_subtitles:
            print("Error: No valid subtitles found in translated chunks")
            return False
        
        # Check sequence numbering
        expected_seq = 1
        for sub in all_subtitles:
            if sub['sequence'] != expected_seq:
                print(f"Warning: Sequence number gap at {expected_seq}, found {sub['sequence']}")
            expected_seq = sub['sequence'] + 1
        
        # Check timing format
        timing_pattern = r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}'
        for sub in all_subtitles:
            if not re.match(timing_pattern, sub['timing']):
                print(f"Warning: Invalid timing format in sequence {sub['sequence']}: {sub['timing']}")
        
        print(f"Validation complete: {len(all_subtitles)} subtitles found")
        return True
    
    def assemble_final_srt(self, output_file: Optional[str] = None) -> str:
        """Assemble all translated chunks into final Romanian SRT file."""
        if output_file is None:
            output_file = os.path.join(self.movie_folder, f"{self.movie_name}_RO.srt")
        
        chunks = self.collect_translated_chunks()
        
        if not chunks:
            raise ValueError("No translated chunks found")
        
        print(f"Found {len(chunks)} translated chunks")
        
        # Validate before assembly
        if not self.validate_translation(chunks):
            print("Warning: Validation found issues, but proceeding with assembly")
        
        # Combine all chunks
        all_subtitles = []
        for chunk in chunks:
            chunk_subtitles = self.parse_srt_content(chunk['content'])
            all_subtitles.extend(chunk_subtitles)
        
        # Sort by sequence number to ensure proper order
        all_subtitles.sort(key=lambda x: x['sequence'])
        
        # Generate final SRT content
        final_srt = ""
        for sub in all_subtitles:
            final_srt += f"{sub['sequence']}\n{sub['timing']}\n{sub['text']}\n\n"
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_srt)
        
        print(f"Final Romanian subtitle file created: {output_file}")
        print(f"Total subtitles: {len(all_subtitles)}")
        
        return output_file
    
    def create_translation_progress_report(self) -> str:
        """Create a report showing translation progress."""
        try:
            chunks = self.collect_translated_chunks()
        except FileNotFoundError:
            return "No translated chunks found yet."
        
        # Count expected vs actual chunks
        original_chunks_pattern = os.path.join(self.chunks_dir, "chunk_*.txt")
        original_chunk_files = glob.glob(original_chunks_pattern)
        expected_chunks = len(original_chunk_files)
        
        report = f"""TRANSLATION PROGRESS REPORT
===========================
Expected chunks: {expected_chunks}
Translated chunks: {len(chunks)}
Progress: {len(chunks)}/{expected_chunks} ({len(chunks)/expected_chunks*100:.1f}%)

Completed chunks:
"""
        for chunk in chunks:
            report += f"  ✓ Chunk {chunk['chunk_number']}\n"
        
        if len(chunks) < expected_chunks:
            missing_nums = set(range(1, expected_chunks + 1)) - set(chunk['chunk_number'] for chunk in chunks)
            report += f"\nMissing chunks: {sorted(missing_nums)}\n"
        
        return report

def main():
    """Main function to reassemble translated subtitles."""
    import sys
    import argparse
    from typing import Optional
    
    parser = argparse.ArgumentParser(description='Reassemble translated movie subtitles')
    parser.add_argument('movie_folder', help='Path to the movie folder')
    parser.add_argument('command', choices=['progress', 'assemble'], help='Command to execute')
    parser.add_argument('--output', '-o', help='Output filename (optional for assemble)')
    
    if len(sys.argv) == 1:
        parser.print_help()
        print("\nExamples:")
        print("  python reassemble_translation.py movies/My_Movie_2023 progress")
        print("  python reassemble_translation.py movies/My_Movie_2023 assemble")
        print("  python reassemble_translation.py movies/My_Movie_2023 assemble --output custom_name.srt")
        sys.exit(1)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.movie_folder):
        print(f"Error: Movie folder {args.movie_folder} not found")
        sys.exit(1)
    
    try:
        assembler = TranslationAssembler(args.movie_folder)
        
        if args.command == "progress":
            print(assembler.create_translation_progress_report())
        elif args.command == "assemble":
            output_file = args.output
            assembler.assemble_final_srt(output_file)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()