#!/usr/bin/env python3
"""
Simple GUI launcher for document converter (requires tkinter)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
from pathlib import Path
from document_converter import DocumentConverter


class DocumentConverterGUI:
    """Simple GUI for document converter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Document Converter Toolkit")
        self.root.geometry("800x600")
        
        self.converter = DocumentConverter()
        self.current_file = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_convert_tab(notebook)
        self.create_compress_tab(notebook)
        self.create_pdf_tab(notebook)
        self.create_batch_tab(notebook)
        self.create_info_tab(notebook)
    
    def create_convert_tab(self, notebook):
        """Create conversion tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Convert")
        
        # File selection
        ttk.Label(tab, text="Input File:").grid(row=0, column=0, sticky='w', pady=5)
        self.convert_file_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.convert_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_convert_file).grid(row=0, column=2)
        
        # Conversion options
        ttk.Label(tab, text="Convert to:").grid(row=1, column=0, sticky='w', pady=5)
        self.convert_format = ttk.Combobox(tab, values=['pdf', 'csv', 'xlsx', 'txt'])
        self.convert_format.grid(row=1, column=1, sticky='w', padx=5)
        self.convert_format.set('pdf')
        
        # Output file
        ttk.Label(tab, text="Output File:").grid(row=2, column=0, sticky='w', pady=5)
        self.convert_output_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.convert_output_var, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_output_file).grid(row=2, column=2)
        
        # Convert button
        ttk.Button(tab, text="Convert", command=self.convert_file).grid(row=3, column=1, pady=20)
        
        # Status
        self.convert_status = ttk.Label(tab, text="")
        self.convert_status.grid(row=4, column=0, columnspan=3)
    
    def create_compress_tab(self, notebook):
        """Create compression tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Compress/Decompress")
        
        # File selection
        ttk.Label(tab, text="File/Folder:").grid(row=0, column=0, sticky='w', pady=5)
        self.compress_file_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.compress_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_compress_file).grid(row=0, column=2)
        
        # Operation
        ttk.Label(tab, text="Operation:").grid(row=1, column=0, sticky='w', pady=5)
        self.compress_op = ttk.Combobox(tab, values=['compress', 'decompress'])
        self.compress_op.grid(row=1, column=1, sticky='w', padx=5)
        self.compress_op.set('compress')
        
        # Method (for compression)
        ttk.Label(tab, text="Method:").grid(row=2, column=0, sticky='w', pady=5)
        self.compress_method = ttk.Combobox(tab, values=['zip', 'tar', 'gz', 'bz2'])
        self.compress_method.grid(row=2, column=1, sticky='w', padx=5)
        self.compress_method.set('zip')
        
        # Output
        ttk.Label(tab, text="Output:").grid(row=3, column=0, sticky='w', pady=5)
        self.compress_output_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.compress_output_var, width=50).grid(row=3, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_compress_output).grid(row=3, column=2)
        
        # Execute button
        ttk.Button(tab, text="Execute", command=self.compress_action).grid(row=4, column=1, pady=20)
        
        # Status
        self.compress_status = ttk.Label(tab, text="")
        self.compress_status.grid(row=5, column=0, columnspan=3)
    
    def create_pdf_tab(self, notebook):
        """Create PDF operations tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="PDF Tools")
        
        # Merge PDFs
        merge_frame = ttk.LabelFrame(tab, text="Merge PDFs", padding=10)
        merge_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(merge_frame, text="Files:").grid(row=0, column=0, sticky='w')
        self.pdf_files_list = tk.Text(merge_frame, height=4, width=50)
        self.pdf_files_list.grid(row=0, column=1, padx=5)
        ttk.Button(merge_frame, text="Add Files", command=self.add_pdf_files).grid(row=0, column=2)
        
        ttk.Label(merge_frame, text="Output:").grid(row=1, column=0, sticky='w', pady=5)
        self.pdf_merge_output = tk.StringVar()
        ttk.Entry(merge_frame, textvariable=self.pdf_merge_output, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(merge_frame, text="Browse", command=self.browse_pdf_output).grid(row=1, column=2)
        
        ttk.Button(merge_frame, text="Merge PDFs", command=self.merge_pdfs).grid(row=2, column=1, pady=10)
        
        # Split PDF
        split_frame = ttk.LabelFrame(tab, text="Split PDF", padding=10)
        split_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(split_frame, text="PDF File:").grid(row=0, column=0, sticky='w')
        self.split_pdf_var = tk.StringVar()
        ttk.Entry(split_frame, textvariable=self.split_pdf_var, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(split_frame, text="Browse", command=self.browse_split_pdf).grid(row=0, column=2)
        
        ttk.Label(split_frame, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.split_output_var = tk.StringVar()
        ttk.Entry(split_frame, textvariable=self.split_output_var, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(split_frame, text="Browse", command=self.browse_split_output).grid(row=1, column=2)
        
        ttk.Button(split_frame, text="Split PDF", command=self.split_pdf).grid(row=2, column=1, pady=10)
        
        # Status
        self.pdf_status = ttk.Label(tab, text="")
        self.pdf_status.pack(pady=10)
    
    def create_batch_tab(self, notebook):
        """Create batch processing tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Batch Process")
        
        # Input folder
        ttk.Label(tab, text="Input Folder:").grid(row=0, column=0, sticky='w', pady=5)
        self.batch_input_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.batch_input_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_batch_input).grid(row=0, column=2)
        
        # Output folder
        ttk.Label(tab, text="Output Folder:").grid(row=1, column=0, sticky='w', pady=5)
        self.batch_output_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.batch_output_var, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_batch_output).grid(row=1, column=2)
        
        # Target format
        ttk.Label(tab, text="Convert to:").grid(row=2, column=0, sticky='w', pady=5)
        self.batch_format = ttk.Combobox(tab, values=['pdf', 'csv', 'xlsx'])
        self.batch_format.grid(row=2, column=1, sticky='w', padx=5)
        self.batch_format.set('pdf')
        
        # Process button
        ttk.Button(tab, text="Start Batch Process", command=self.batch_process).grid(row=3, column=1, pady=20)
        
        # Log output
        self.batch_log = scrolledtext.ScrolledText(tab, height=15, width=80)
        self.batch_log.grid(row=4, column=0, columnspan=3, pady=10)
    
    def create_info_tab(self, notebook):
        """Create file info tab"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="File Info")
        
        # File selection
        ttk.Label(tab, text="File:").grid(row=0, column=0, sticky='w', pady=5)
        self.info_file_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.info_file_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(tab, text="Browse", command=self.browse_info_file).grid(row=0, column=2)
        
        # Get info button
        ttk.Button(tab, text="Get File Info", command=self.get_file_info).grid(row=1, column=1, pady=10)
        
        # Info display
        self.info_text = scrolledtext.ScrolledText(tab, height=20, width=80)
        self.info_text.grid(row=2, column=0, columnspan=3, pady=10)
    
    # ============= Browse functions =============
    
    def browse_convert_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.convert_file_var.set(filename)
            # Suggest output file
            path = Path(filename)
            self.convert_output_var.set(str(path.with_suffix(f'.{self.convert_format.get()}')))
    
    def browse_output_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=f".{self.convert_format.get()}")
        if filename:
            self.convert_output_var.set(filename)
    
    def browse_compress_file(self):
        path = filedialog.askopenfilename()
        if not path:
            path = filedialog.askdirectory()
        if path:
            self.compress_file_var.set(path)
    
    def browse_compress_output(self):
        if self.compress_op.get() == 'compress':
            filename = filedialog.asksaveasfilename(defaultextension=f".{self.compress_method.get()}")
        else:
            filename = filedialog.askdirectory()
        if filename:
            self.compress_output_var.set(filename)
    
    def add_pdf_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            current = self.pdf_files_list.get("1.0", tk.END).strip()
            new_files = "\n".join(files)
            self.pdf_files_list.delete("1.0", tk.END)
            self.pdf_files_list.insert("1.0", new_files if not current else current + "\n" + new_files)
    
    def browse_pdf_output(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf")
        if filename:
            self.pdf_merge_output.set(filename)
    
    def browse_split_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filename:
            self.split_pdf_var.set(filename)
    
    def browse_split_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.split_output_var.set(folder)
    
    def browse_batch_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_input_var.set(folder)
    
    def browse_batch_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.batch_output_var.set(folder)
    
    def browse_info_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.info_file_var.set(filename)
    
    # ============= Action functions =============
    
    def convert_file(self):
        input_file = self.convert_file_var.get()
        output_file = self.convert_output_var.get()
        to_format = self.convert_format.get()
        
        if not input_file:
            self.convert_status.config(text="Please select input file")
            return
        
        def convert():
            ext = Path(input_file).suffix.lower()
            
            if to_format == 'pdf':
                if ext in ['.txt', '.md']:
                    success, msg = self.converter.convert_text_to_pdf(input_file, output_file)
                elif ext in ['.jpg', '.jpeg', '.png']:
                    success, msg = self.converter.convert_image_to_pdf(input_file, output_file)
                elif ext == '.docx':
                    success, msg = self.converter.convert_docx_to_pdf(input_file, output_file)
                else:
                    success, msg = False, f"Cannot convert {ext} to PDF"
            
            elif to_format == 'csv' and ext == '.xlsx':
                success, msg = self.converter.convert_excel_to_csv(input_file, output_file)
            
            elif to_format == 'xlsx' and ext == '.csv':
                success, msg = self.converter.convert_csv_to_excel(input_file, output_file)
            
            else:
                success, msg = False, f"Unsupported conversion"
            
            self.root.after(0, lambda: self.convert_status.config(
                text=f"{'✅' if success else '❌'} {msg}"))
        
        threading.Thread(target=convert, daemon=True).start()
        self.convert_status.config(text="Converting...")
    
    def compress_action(self):
        path = self.compress_file_var.get()
        output = self.compress_output_var.get()
        op = self.compress_op.get()
        
        if not path:
            self.compress_status.config(text="Please select file/folder")
            return
        
        def action():
            if op == 'compress':
                if Path(path).is_dir():
                    success, msg = self.converter.compress_folder(
                        path, output, self.compress_method.get())
                else:
                    success, msg = self.converter.compress_file(
                        path, output, self.compress_method.get())
            else:
                success, msg = self.converter.decompress_file(path, output)
            
            self.root.after(0, lambda: self.compress_status.config(
                text=f"{'✅' if success else '❌'} {msg}"))
        
        threading.Thread(target=action, daemon=True).start()
        self.compress_status.config(text="Processing...")
    
    def merge_pdfs(self):
        files_text = self.pdf_files_list.get("1.0", tk.END).strip()
        output = self.pdf_merge_output.get()
        
        if not files_text or not output:
            self.pdf_status.config(text="Please select PDFs and output file")
            return
        
        files = files_text.split('\n')
        
        def merge():
            success, msg = self.converter.merge_pdfs(files, output)
            self.root.after(0, lambda: self.pdf_status.config(
                text=f"{'✅' if success else '❌'} {msg}"))
        
        threading.Thread(target=merge, daemon=True).start()
        self.pdf_status.config(text="Merging PDFs...")
    
    def split_pdf(self):
        input_file = self.split_pdf_var.get()
        output_dir = self.split_output_var.get()
        
        if not input_file:
            self.pdf_status.config(text="Please select PDF file")
            return
        
        def split():
            success, msg = self.converter.split_pdf(input_file, output_dir)
            self.root.after(0, lambda: self.pdf_status.config(
                text=f"{'✅' if success else '❌'} {msg}"))
        
        threading.Thread(target=split, daemon=True).start()
        self.pdf_status.config(text="Splitting PDF...")
    
    def batch_process(self):
        input_folder = self.batch_input_var.get()
        output_folder = self.batch_output_var.get()
        to_format = self.batch_format.get()
        
        if not input_folder or not output_folder:
            self.batch_log.insert(tk.END, "Please select input and output folders\n")
            return
        
        def batch():
            results = self.converter.batch_convert(input_folder, to_format, output_folder)
            
            self.root.after(0, lambda: self.display_batch_results(results))
        
        threading.Thread(target=batch, daemon=True).start()
        self.batch_log.insert(tk.END, "Batch processing started...\n")
    
    def display_batch_results(self, results):
        self.batch_log.delete("1.0", tk.END)
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        self.batch_log.insert(tk.END, f"Batch Processing Complete!\n")
        self.batch_log.insert(tk.END, f"✅ Successful: {successful}\n")
        self.batch_log.insert(tk.END, f"❌ Failed: {failed}\n\n")
        
        if failed > 0:
            self.batch_log.insert(tk.END, "Failed conversions:\n")
            for r in results:
                if not r['success']:
                    self.batch_log.insert(tk.END, f"  {r['file']}: {r['message']}\n")
    
    def get_file_info(self):
        file = self.info_file_var.get()
        
        if not file:
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert("1.0", "Please select a file")
            return
        
        info = self.converter.get_file_info(file)
        
        self.info_text.delete("1.0", tk.END)
        if info:
            for key, value in info.items():
                self.info_text.insert(tk.END, f"{key}: {value}\n")
        else:
            self.info_text.insert("1.0", "File not found or cannot be read")


def main():
    root = tk.Tk()
    app = DocumentConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()