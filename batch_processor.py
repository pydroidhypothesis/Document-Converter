#!/usr/bin/env python3
"""
Batch processing script for document conversion
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime
from document_converter import DocumentConverter


class BatchProcessor:
    """Handle batch processing of documents"""
    
    def __init__(self, config_file=None):
        self.converter = DocumentConverter()
        self.config = self.load_config(config_file) if config_file else {}
        self.log_file = None
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config_file):
        """Save configuration to JSON file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def setup_logging(self, log_dir="logs"):
        """Setup logging for batch processing"""
        Path(log_dir).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = Path(log_dir) / f"batch_process_{timestamp}.log"
        return self.log_file
    
    def log(self, message, level="INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        print(log_entry)
        
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + "\n")
    
    def process_watch_folder(self, watch_folder, output_folder, rules=None):
        """Process files in a watch folder based on rules"""
        watch_path = Path(watch_folder)
        output_path = Path(output_folder)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Default rules if none provided
        if not rules:
            rules = {
                '.txt': {'action': 'convert', 'to': 'pdf'},
                '.jpg': {'action': 'convert', 'to': 'pdf'},
                '.png': {'action': 'convert', 'to': 'pdf'},
                '.csv': {'action': 'convert', 'to': 'xlsx'},
                '.docx': {'action': 'convert', 'to': 'pdf'},
                '.zip': {'action': 'decompress'},
            }
        
        processed = 0
        errors = 0
        
        for file in watch_path.iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                
                if ext in rules:
                    rule = rules[ext]
                    action = rule.get('action')
                    
                    try:
                        if action == 'convert':
                            to_format = rule.get('to', 'pdf')
                            output_file = output_path / f"{file.stem}.{to_format}"
                            
                            if to_format == 'pdf':
                                if ext in ['.txt', '.md']:
                                    success, msg = self.converter.convert_text_to_pdf(
                                        file, output_file)
                                elif ext in ['.jpg', '.jpeg', '.png']:
                                    success, msg = self.converter.convert_image_to_pdf(
                                        file, output_file)
                                elif ext == '.docx':
                                    success, msg = self.converter.convert_docx_to_pdf(
                                        file, output_file)
                                else:
                                    success, msg = False, f"Unsupported conversion"
                            
                            elif to_format == 'xlsx' and ext == '.csv':
                                success, msg = self.converter.convert_csv_to_excel(
                                    file, output_file)
                            
                            elif to_format == 'csv' and ext == '.xlsx':
                                success, msg = self.converter.convert_excel_to_csv(
                                    file, output_file)
                            
                            else:
                                success, msg = False, f"No conversion rule for {ext} to {to_format}"
                            
                            if success:
                                self.log(f"Converted: {file.name} -> {output_file.name}")
                                processed += 1
                            else:
                                self.log(f"Conversion failed: {file.name} - {msg}", "ERROR")
                                errors += 1
                        
                        elif action == 'compress':
                            method = rule.get('method', 'zip')
                            output_file = output_path / f"{file.stem}.{method}"
                            success, msg = self.converter.compress_file(
                                file, output_file, method)
                            
                            if success:
                                self.log(f"Compressed: {file.name} -> {output_file.name}")
                                processed += 1
                            else:
                                self.log(f"Compression failed: {file.name} - {msg}", "ERROR")
                                errors += 1
                        
                        elif action == 'decompress':
                            success, msg = self.converter.decompress_file(
                                file, output_path / file.stem)
                            
                            if success:
                                self.log(f"Decompressed: {file.name}")
                                processed += 1
                            else:
                                self.log(f"Decompression failed: {file.name} - {msg}", "ERROR")
                                errors += 1
                        
                        elif action == 'move':
                            # Simple file move
                            category = rule.get('category', 'other')
                            dest_folder = output_path / category
                            dest_folder.mkdir(exist_ok=True)
                            
                            dest_file = dest_folder / file.name
                            if not dest_file.exists():
                                file.rename(dest_file)
                                self.log(f"Moved: {file.name} -> {category}/")
                                processed += 1
                            else:
                                self.log(f"File exists: {file.name}", "WARNING")
                                errors += 1
                    
                    except Exception as e:
                        self.log(f"Error processing {file.name}: {str(e)}", "ERROR")
                        errors += 1
        
        self.log(f"\nBatch processing complete!")
        self.log(f"✅ Successfully processed: {processed} files")
        self.log(f"❌ Errors: {errors} files")
        
        return processed, errors
    
    def create_watch_service(self, watch_folder, output_folder, interval=60):
        """Create a continuous watching service"""
        import time
        
        self.log(f"Starting watch service on: {watch_folder}")
        self.log(f"Output folder: {output_folder}")
        self.log(f"Checking every {interval} seconds")
        
        processed_files = set()
        
        while True:
            try:
                current_files = set(Path(watch_folder).glob('*'))
                new_files = current_files - processed_files
                
                if new_files:
                    self.log(f"\nFound {len(new_files)} new files")
                    for file in new_files:
                        if file.is_file():
                            self.process_watch_folder(watch_folder, output_folder)
                            processed_files.add(file)
                
                time.sleep(interval)
            
            except KeyboardInterrupt:
                self.log("\nWatch service stopped by user")
                break
            except Exception as e:
                self.log(f"Error in watch service: {e}", "ERROR")
                time.sleep(interval)


def main():
    """Main entry point for batch processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch document processor')
    parser.add_argument('command', choices=['process', 'watch', 'create-config'],
                       help='Command to execute')
    parser.add_argument('--watch', '-w', help='Watch folder')
    parser.add_argument('--output', '-o', help='Output folder')
    parser.add_argument('--config', '-c', help='Configuration file')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Watch interval in seconds')
    
    args = parser.parse_args()
    
    processor = BatchProcessor(args.config)
    
    if args.command == 'create-config':
        # Create sample configuration
        sample_config = {
            '.txt': {'action': 'convert', 'to': 'pdf'},
            '.jpg': {'action': 'convert', 'to': 'pdf'},
            '.png': {'action': 'convert', 'to': 'pdf'},
            '.csv': {'action': 'convert', 'to': 'xlsx'},
            '.xlsx': {'action': 'convert', 'to': 'csv'},
            '.docx': {'action': 'convert', 'to': 'pdf'},
            '.zip': {'action': 'decompress'},
            '.pdf': {'action': 'compress', 'method': 'zip'},
            'photos': {'action': 'move', 'category': 'images'},
            'documents': {'action': 'move', 'category': 'docs'},
        }
        
        processor.config = sample_config
        config_file = args.config or 'processor_config.json'
        if processor.save_config(config_file):
            print(f"✅ Created sample config: {config_file}")
        return
    
    if not args.watch or not args.output:
        parser.error("--watch and --output required for process/watch commands")
    
    processor.setup_logging()
    
    if args.command == 'process':
        processor.process_watch_folder(args.watch, args.output)
    
    elif args.command == 'watch':
        processor.create_watch_service(args.watch, args.output, args.interval)


if __name__ == "__main__":
    main()