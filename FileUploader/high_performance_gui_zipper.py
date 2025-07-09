#!/usr/bin/env python3
"""
High-Performance GUI Zipper with Advanced Features
A modern Tkinter-based GUI for the high-performance file zipper with real-time monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import queue
import re
import shutil

# Import GitHub manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from github_push import GitHubManager
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("Note: GitHub functionality not available. github_push.py not found.")

# Try to import drag and drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    print("Note: tkinterdnd2 not available. Drag and drop will be disabled.")
    print("Install with: pip install tkinterdnd2")

# Load credentials from credentials.json if available
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
CREDENTIALS = {}
if os.path.exists(CREDENTIALS_PATH):
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            CREDENTIALS = json.load(f)
    except Exception as e:
        print(f"Failed to load credentials.json: {e}")

@dataclass
class ProcessingStats:
    """Data class for processing statistics"""
    files_processed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    total_files: int = 0
    total_input_size: int = 0
    total_output_size: int = 0
    processing_time: float = 0.0
    throughput: float = 0.0
    compression_ratio: float = 0.0

class HighPerformanceZipperGUI:
    def __init__(self, root):
        # Initialize with drag and drop support if available
        if DRAG_DROP_AVAILABLE:
            self.root = TkinterDnD.Tk() if not isinstance(root, TkinterDnD.Tk) else root
        else:
            self.root = root
            
        self.root.title("MyStorage - High-Performance File Zipper")
        self.root.geometry("1000x700")  # Better initial size
        self.root.minsize(800, 600)
        
        # Set application icon with better handling for large icons
        try:
            icon_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try to use a specific sized icon first (better for GUI)
            icon_sizes_to_try = ['icon_128.png', 'icon_256.png', 'icon_64.png', 'icon.png']
            
            icon_loaded = False
            for icon_name in icon_sizes_to_try:
                icon_path = os.path.join(icon_dir, icon_name)
                if os.path.exists(icon_path):
                    try:
                        # For Linux/Unix systems
                        if hasattr(self.root, 'iconphoto'):
                            icon_image = tk.PhotoImage(file=icon_path)
                            self.root.iconphoto(True, icon_image)
                            print(f"Successfully loaded icon: {icon_name}")
                            icon_loaded = True
                            break
                        # For Windows systems  
                        elif hasattr(self.root, 'iconbitmap'):
                            self.root.iconbitmap(icon_path)
                            print(f"Successfully loaded icon: {icon_name}")
                            icon_loaded = True
                            break
                    except Exception as e:
                        print(f"Failed to load {icon_name}: {e}")
                        continue
            
            if not icon_loaded:
                print("Could not load any application icon")
                
        except Exception as e:
            print(f"Error setting application icon: {e}")
        
        # Make window resizable and fit screen
        self.root.state('normal')
        self.setup_responsive_layout()
        
        # Configure style
        self.setup_styles()
        
        # Variables
        self.source_folder = tk.StringVar(value="input")  # Single source selection
        self.output_folder = tk.StringVar(value="../MyStorage/files")
        self.password = tk.StringVar(value="")  # No default password - user must enter
        self.use_parallel = tk.BooleanVar(value=True)
        self.max_threads = tk.IntVar(value=8)
        
        # File management - simplified to single source
        self.selected_files = []  # List of individually selected files from source
        self.source_mode = tk.StringVar(value="folder")  # "folder" or "files"
        
        # Processing state
        self.is_processing = False
        self.process = None
        self.stats_queue = queue.Queue()
        
        # GitHub functionality
        self.github_manager = None
        if GITHUB_AVAILABLE:
            try:
                # Initialize GitHub manager for MyStorage directory
                mystorage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MyStorage")
                github_token = CREDENTIALS.get("github_token")
                github_user = CREDENTIALS.get("github_user")
                github_email = CREDENTIALS.get("github_email")
                # Pass credentials if available
                self.github_manager = GitHubManager(mystorage_path, token=github_token, user=github_user, email=github_email)
            except Exception as e:
                print(f"Failed to initialize GitHub manager: {e}")
        
        # Create GUI
        self.create_widgets()
        
        # Center window after creation
        self.center_window()
        
    def setup_responsive_layout(self):
        """Setup responsive layout that adapts to screen size"""
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate optimal window size (80% of screen, but not larger than comfortable sizes)
        optimal_width = min(int(screen_width * 0.8), 1200)
        optimal_height = min(int(screen_height * 0.8), 800)
        
        # Ensure minimum sizes
        optimal_width = max(optimal_width, 800)
        optimal_height = max(optimal_height, 600)
        
        self.root.geometry(f"{optimal_width}x{optimal_height}")
        
    def setup_styles(self):
        """Configure modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Helvetica', 10, 'italic'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
        
    def center_window(self):
        """Center the window on screen after all widgets are created"""
        self.root.update_idletasks()  # Ensure all widgets are rendered
        
        # Get actual window size
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate center position
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Ensure window is not positioned off-screen
        x = max(0, x)
        y = max(0, y)
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
    def create_source_section(self, parent):
        """Create source selection section"""
        # Source mode selection
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="Process All Files from Folder", variable=self.source_mode, 
                       value="folder", command=self.on_source_mode_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Select Individual Files", variable=self.source_mode, 
                       value="files", command=self.on_source_mode_change).pack(side=tk.LEFT)
        
        # Source folder
        folder_frame = ttk.Frame(parent)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        entry_frame = ttk.Frame(folder_frame)
        entry_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        entry_frame.columnconfigure(0, weight=1)
        
        self.source_entry = ttk.Entry(entry_frame, textvariable=self.source_folder)
        self.source_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(entry_frame, text="Browse", command=self.browse_source_folder).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(entry_frame, text="View", command=self.view_source_files).grid(row=0, column=2)
        
    def create_config_section(self, parent):
        """Create output configuration section"""
        # Output folder
        output_frame = ttk.Frame(parent)
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        entry_frame = ttk.Frame(output_frame)
        entry_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        entry_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(entry_frame, textvariable=self.output_folder)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(entry_frame, text="Browse", command=self.browse_output_folder).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(entry_frame, text="View", command=self.view_output_files).grid(row=0, column=2)
        
        # Password
        pass_frame = ttk.Frame(parent)
        pass_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(15, 5))
        pass_frame.columnconfigure(1, weight=1)
        
        ttk.Label(pass_frame, text="Password:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        pass_entry_frame = ttk.Frame(pass_frame)
        pass_entry_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        pass_entry_frame.columnconfigure(0, weight=1)
        
        self.password_entry = ttk.Entry(pass_entry_frame, textvariable=self.password, show="*")
        self.password_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(pass_entry_frame, text="Show", command=self.toggle_password).grid(row=0, column=1)
        
    def create_file_selection_section(self, parent):
        """Create file selection section"""
        # File selection buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(button_frame, text="Add Files", command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Add Folder Contents", command=self.add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_from_source_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT)
        
        # File list display
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(list_frame, height=5, selectmode=tk.EXTENDED)
        file_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        file_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Add context menu for file list
        self.create_file_list_context_menu()
        
        # Drag and drop area
        self.create_drag_drop_area(parent)
        
    def create_performance_section(self, parent):
        """Create performance options section"""
        self.parallel_check = ttk.Checkbutton(parent, text="Enable parallel processing", variable=self.use_parallel)
        self.parallel_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        thread_frame = ttk.Frame(parent)
        thread_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(thread_frame, text="Max threads:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.threads_spin = ttk.Spinbox(thread_frame, from_=1, to=16, textvariable=self.max_threads, width=10)
        self.threads_spin.grid(row=0, column=1, sticky=tk.W)
        
        # Storage location info
        self.storage_info_label = ttk.Label(parent, text="ZIP files will be saved to: ../MyStorage/files/", 
                                          style='Subtitle.TLabel')
        self.storage_info_label.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        # Update storage info when output folder changes
        self.output_folder.trace_add('write', self.update_storage_info)
        
    def create_control_buttons(self, parent):
        """Create control buttons in right panel"""
        button_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Processing", command=self.start_processing)
        self.start_button.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state='disabled')
        self.stop_button.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Output", command=self.clear_output)
        self.clear_button.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # GitHub controls section
        if GITHUB_AVAILABLE and self.github_manager:
            github_frame = ttk.LabelFrame(button_frame, text="GitHub Integration", padding="5")
            github_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
            github_frame.columnconfigure(0, weight=1)
            
            # Commit message entry
            ttk.Label(github_frame, text="Commit Message:").grid(row=0, column=0, sticky=tk.W, pady=(0, 2))
            self.commit_message = tk.StringVar(value="Update MyStorage files via GUI")
            self.commit_entry = ttk.Entry(github_frame, textvariable=self.commit_message, width=30)
            self.commit_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            
            # GitHub buttons
            self.github_status_button = ttk.Button(github_frame, text="Check Status", 
                                                 command=self.check_github_status)
            self.github_status_button.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 2))
            
            self.github_push_button = ttk.Button(github_frame, text="Push to GitHub", 
                                               command=self.push_to_github)
            self.github_push_button.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 2))
            
            # GitHub status label
            self.github_status_var = tk.StringVar(value="Ready")
            self.github_status_label = ttk.Label(github_frame, textvariable=self.github_status_var, 
                                                font=('Helvetica', 8))
            self.github_status_label.grid(row=4, column=0, sticky=tk.W, pady=(2, 0))
        
    def create_progress_section(self, parent):
        """Create progress section in right panel"""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to process files")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def create_stats_section(self, parent):
        """Create statistics section in right panel"""
        stats_frame = ttk.LabelFrame(parent, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create statistics display
        self.create_stats_display(stats_frame)
        
    def create_output_section(self, parent):
        """Create output section in right panel"""
        output_frame = ttk.LabelFrame(parent, text="Output Log", padding="5")
        output_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(output_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.output_text = tk.Text(text_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
    def create_widgets(self):
        """Create and arrange GUI widgets with scrollable layout"""
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create main container with horizontal layout
        main_container = ttk.Frame(self.root)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        main_container.columnconfigure(0, weight=2)  # Left panel gets more space
        main_container.columnconfigure(1, weight=1)  # Right panel for controls
        main_container.rowconfigure(0, weight=1)
        
        # Left panel with scrollable content
        self.create_left_panel(main_container)
        
        # Right panel with controls and output
        self.create_right_panel(main_container)
        
    def create_left_panel(self, parent):
        """Create left panel with main configuration"""
        # Create scrollable frame for left panel
        left_canvas = tk.Canvas(parent, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=left_canvas.yview)
        self.left_scrollable_frame = ttk.Frame(left_canvas)
        
        # Configure scrolling
        self.left_scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        left_canvas.create_window((0, 0), window=self.left_scrollable_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Grid layout
        left_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure scrollable frame
        self.left_scrollable_frame.columnconfigure(0, weight=1)
        
        # Add main content to scrollable frame
        self.create_main_content(self.left_scrollable_frame)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_canvas.bind("<MouseWheel>", _on_mousewheel)
        
    def create_right_panel(self, parent):
        """Create right panel with controls and output"""
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(3, weight=1)  # Output section gets most space
        
        # Control buttons
        self.create_control_buttons(right_frame)
        
        # Progress section
        self.create_progress_section(right_frame)
        
        # Statistics section
        self.create_stats_section(right_frame)
        
        # Output section (expandable)
        self.create_output_section(right_frame)
        
    def create_main_content(self, parent):
        """Create main content in the scrollable left panel"""
        row = 0
        
        # Title
        title_label = ttk.Label(parent, text="MyStorage", style='Title.TLabel')
        title_label.grid(row=row, column=0, pady=(0, 5), sticky=tk.W)
        row += 1
        
        subtitle_label = ttk.Label(parent, text="High-performance file compression and secure storage", style='Subtitle.TLabel')
        subtitle_label.grid(row=row, column=0, pady=(0, 15), sticky=tk.W)
        row += 1
        
        # Source Selection section
        source_frame = ttk.LabelFrame(parent, text="Source Selection", padding="10")
        source_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        source_frame.columnconfigure(0, weight=1)
        self.create_source_section(source_frame)
        row += 1
        
        # Individual File Selection (conditionally shown - right after source selection)
        self.file_selection_frame = ttk.LabelFrame(parent, text="Selected Files", padding="10")
        self.file_selection_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.file_selection_frame.columnconfigure(0, weight=1)
        self.create_file_selection_section(self.file_selection_frame)
        self.file_selection_frame.grid_remove()  # Initially hidden
        row += 1
        
        # Output Configuration section
        config_frame = ttk.LabelFrame(parent, text="Output Configuration", padding="10")
        config_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(0, weight=1)
        self.create_config_section(config_frame)
        row += 1
        
        # Performance Options section
        perf_frame = ttk.LabelFrame(parent, text="Performance Options", padding="10")
        perf_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        perf_frame.columnconfigure(0, weight=1)
        self.create_performance_section(perf_frame)
        row += 1
        
    def create_stats_display(self, parent):
        """Create statistics display widgets"""
        self.stats_vars = {
            'processed': tk.StringVar(value="0"),
            'failed': tk.StringVar(value="0"),
            'total': tk.StringVar(value="0"),
            'input_size': tk.StringVar(value="0 B"),
            'output_size': tk.StringVar(value="0 B"),
            'compression': tk.StringVar(value="0%"),
            'time': tk.StringVar(value="0 ms"),
            'throughput': tk.StringVar(value="0 B/s")
        }
        
        # Row 0
        ttk.Label(parent, text="Processed:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(parent, textvariable=self.stats_vars['processed']).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(parent, text="Failed:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(parent, textvariable=self.stats_vars['failed']).grid(row=0, column=3, sticky=tk.W)
        
        # Row 1
        ttk.Label(parent, text="Total:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(parent, textvariable=self.stats_vars['total']).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(parent, text="Time:").grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(parent, textvariable=self.stats_vars['time']).grid(row=1, column=3, sticky=tk.W)
        
        # Row 2
        ttk.Label(parent, text="Input Size:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(parent, textvariable=self.stats_vars['input_size']).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(parent, text="Compression:").grid(row=2, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(parent, textvariable=self.stats_vars['compression']).grid(row=2, column=3, sticky=tk.W)
        
        # Row 3
        ttk.Label(parent, text="Output Size:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(parent, textvariable=self.stats_vars['output_size']).grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(parent, text="Throughput:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Label(parent, textvariable=self.stats_vars['throughput']).grid(row=3, column=3, sticky=tk.W)
        
    def browse_source_folder(self):
        """Browse for source folder"""
        folder = filedialog.askdirectory(title="Select Source Folder", initialdir=self.source_folder.get())
        if folder:
            self.source_folder.set(folder)
            
    def view_source_files(self):
        """View files in source folder"""
        folder_path = self.source_folder.get()
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showwarning("Warning", "Please select a valid source folder first")
            return
        self.show_folder_contents("Source Folder Contents", folder_path)
        
    def view_output_files(self):
        """View files in output folder"""
        folder_path = self.output_folder.get()
        if not folder_path:
            messagebox.showwarning("Warning", "Please specify an output folder first")
            return
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            messagebox.showinfo("Info", f"Created output folder: {folder_path}")
        self.show_folder_contents("Output Folder Contents", folder_path)
        
    def show_folder_contents(self, title, folder_path):
        """Show contents of a folder in a popup window with delete functionality"""
        try:
            # Create popup window
            popup = tk.Toplevel(self.root)
            popup.title(title)
            popup.geometry("700x500")  # Slightly larger for better layout
            popup.transient(self.root)
            popup.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(popup, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title and path
            ttk.Label(main_frame, text=title, font=('Helvetica', 12, 'bold')).pack(pady=(0, 5))
            ttk.Label(main_frame, text=f"Path: {folder_path}", style='Subtitle.TLabel').pack(pady=(0, 10))
            
            # File list frame
            list_frame = ttk.Frame(main_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            # Treeview for file details
            columns = ('Name', 'Type', 'Size', 'Modified')
            tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
            
            # Configure columns
            tree.heading('#0', text='', anchor=tk.W)
            tree.column('#0', width=20, minwidth=20, stretch=False)
            tree.heading('Name', text='Name', anchor=tk.W)
            tree.column('Name', width=300, minwidth=200)
            tree.heading('Type', text='Type', anchor=tk.W)
            tree.column('Type', width=80, minwidth=80)
            tree.heading('Size', text='Size', anchor=tk.E)
            tree.column('Size', width=100, minwidth=80)
            tree.heading('Modified', text='Modified', anchor=tk.W)
            tree.column('Modified', width=120, minwidth=120)
            
            # Scrollbars
            v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            # Grid layout
            tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
            
            list_frame.columnconfigure(0, weight=1)
            list_frame.rowconfigure(0, weight=1)
            
            # Store tree and folder path for delete operations
            tree.folder_path = folder_path
            tree.popup_window = popup
            tree.popup_title = title
            
            # Create context menu for tree
            tree_context_menu = tk.Menu(popup, tearoff=0)
            tree_context_menu.add_command(label="Delete Selected", 
                                         command=lambda: self.delete_selected_from_tree(tree))
            tree_context_menu.add_separator()
            tree_context_menu.add_command(label="Show in Explorer", 
                                         command=lambda: self.show_selected_in_explorer(tree))
            
            def show_tree_context_menu(event):
                """Show context menu for tree items"""
                item = tree.selection()
                if item:  # Only show menu if an item is selected
                    try:
                        tree_context_menu.tk_popup(event.x_root, event.y_root)
                    finally:
                        tree_context_menu.grab_release()
            
            tree.bind("<Button-3>", show_tree_context_menu)  # Right-click
            
            # Populate tree
            total_files = 0
            total_size = 0
            
            def add_directory(parent_item, dir_path, is_root=False):
                nonlocal total_files, total_size
                try:
                    items = list(Path(dir_path).iterdir())
                    # Sort: directories first, then files, alphabetically
                    items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                    
                    for item in items:
                        try:
                            if item.is_file():
                                total_files += 1
                                file_size = item.stat().st_size
                                total_size += file_size
                                file_type = item.suffix.upper()[1:] if item.suffix else "File"
                                modified = time.strftime("%Y-%m-%d %H:%M", time.localtime(item.stat().st_mtime))
                                
                                tree.insert(parent_item, tk.END, text="📄",
                                           values=(item.name, file_type, self.format_bytes(file_size), modified))
                            elif item.is_dir():
                                # Directory
                                dir_item = tree.insert(parent_item, tk.END, text="📁",
                                                     values=(item.name, "Folder", "", ""))
                                # Recursively add subdirectory contents
                                add_directory(dir_item, item, False)
                        except (PermissionError, OSError):
                            # Skip files/folders we can't access
                            continue
                except (PermissionError, OSError):
                    pass
            
            # Add all items
            add_directory("", folder_path, True)
            
            # Expand root level
            for child in tree.get_children():
                tree.item(child, open=True)
            
            # Statistics
            stats_frame = ttk.Frame(main_frame)
            stats_frame.pack(fill=tk.X, pady=(10, 0))
            
            stats_text = f"Total Files: {total_files} | Total Size: {self.format_bytes(total_size)}"
            ttk.Label(stats_frame, text=stats_text, style='Subtitle.TLabel').pack()
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(button_frame, text="Refresh", 
                      command=lambda: self.refresh_folder_view(popup, title, folder_path)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Open in Explorer", 
                      command=lambda: self.open_folder_in_explorer(folder_path)).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Close", command=popup.destroy).pack(side=tk.RIGHT)
            
            # Center popup
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display folder contents: {str(e)}")
            
    def refresh_folder_view(self, popup, title, folder_path):
        """Refresh folder view popup"""
        popup.destroy()
        self.show_folder_contents(title, folder_path)
        
    def open_folder_in_explorer(self, folder_path):
        """Open folder in system file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
            
    def toggle_password(self):
        """Toggle password visibility"""
        if self.password_entry['show'] == '*':
            self.password_entry['show'] = ''
        else:
            self.password_entry['show'] = '*'
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)
            
    def update_storage_info(self, *args):
        """Update the storage location information display"""
        output_path = self.output_folder.get()
        if len(output_path) > 50:
            output_path = "..." + output_path[-47:]
        self.storage_info_label.config(text=f"ZIP files will be saved to: {output_path}")
            
    def create_drag_drop_area(self, parent):
        """Create drag and drop area"""
        # Drag and drop info
        dnd_frame = ttk.Frame(parent)
        dnd_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        if DRAG_DROP_AVAILABLE:
            # Create drag and drop area
            self.dnd_label = ttk.Label(dnd_frame, text="🎯 Drag and drop files/folders here", 
                                     style='Subtitle.TLabel', 
                                     background='lightblue', 
                                     relief='ridge', padding=10)
            self.dnd_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
            dnd_frame.columnconfigure(0, weight=1)
            
            # Configure drag and drop
            self.dnd_label.drop_target_register(DND_FILES)
            self.dnd_label.dnd_bind('<<Drop>>', self.on_drop)
            
            # Visual feedback for drag and drop
            self.dnd_label.bind('<Enter>', lambda e: self.dnd_label.configure(background='lightgreen'))
            self.dnd_label.bind('<Leave>', lambda e: self.dnd_label.configure(background='lightblue'))
        else:
            # Show info about missing drag and drop
            ttk.Label(dnd_frame, text="💡 Install tkinterdnd2 for drag and drop support", 
                     style='Subtitle.TLabel').grid(row=0, column=0, sticky=tk.W)
                     
    def create_file_list_context_menu(self):
        """Create context menu for file list"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Remove from List", command=self.remove_selected_files)
        self.context_menu.add_command(label="Delete from Disk", command=self.delete_from_source_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear All", command=self.clear_files)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        
        # Bind right-click to listbox
        self.file_listbox.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """Show context menu at cursor position"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def on_source_mode_change(self):
        """Handle source selection mode change"""
        if self.source_mode.get() == "files":
            self.file_selection_frame.grid()
            if DRAG_DROP_AVAILABLE:
                self.dnd_label.configure(text="🎯 Drag and drop files/folders here or use buttons above")
        else:
            self.file_selection_frame.grid_remove()
            self.clear_files()
            if DRAG_DROP_AVAILABLE:
                self.dnd_label.configure(text="🎯 Using source folder mode - all files will be processed")
                
        # Update the scrollable area
        self.left_scrollable_frame.update_idletasks()
                
    def add_files(self):
        """Add individual files"""
        files = filedialog.askopenfilenames(
            title="Select Files to Zip",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx")
            ]
        )
        
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
        
        self.update_file_list()
        
    def add_folder(self):
        """Add all files from a folder"""
        folder = filedialog.askdirectory(title="Select Folder to Add Files From")
        if folder:
            try:
                folder_path = Path(folder)
                added_files = []
                
                # Add all files from folder (recursively)
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        file_str = str(file_path)
                        if file_str not in self.selected_files:
                            self.selected_files.append(file_str)
                            added_files.append(file_path.name)
                
                if added_files:
                    self.log_message(f"Added {len(added_files)} files from folder: {folder}", "INFO")
                    self.update_file_list()
                else:
                    messagebox.showinfo("No New Files", "No new files found in the selected folder.")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add folder: {str(e)}")
                
    def clear_files(self):
        """Clear all selected files"""
        self.selected_files.clear()
        self.update_file_list()
        
    def remove_selected_files(self):
        """Remove selected files from the list"""
        selection = self.file_listbox.curselection()
        if selection:
            # Remove in reverse order to maintain indices
            for index in reversed(selection):
                if index < len(self.selected_files):
                    removed_file = self.selected_files.pop(index)
                    self.log_message(f"Removed: {Path(removed_file).name}", "INFO")
            self.update_file_list()
        else:
            messagebox.showinfo("No Selection", "Please select files to remove from the list.")
            
    def show_in_explorer(self):
        """Show selected file in file explorer"""
        selection = self.file_listbox.curselection()
        if selection and selection[0] < len(self.selected_files):
            file_path = self.selected_files[selection[0]]
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(os.path.dirname(file_path))
                elif os.name == 'posix':  # Linux/Mac
                    subprocess.run(['xdg-open', os.path.dirname(file_path)])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file location: {str(e)}")
                
    def update_file_list(self):
        """Update the file list display"""
        self.file_listbox.delete(0, tk.END)
        
        if not self.selected_files:
            self.file_listbox.insert(0, "No files selected")
            return
            
        for file_path in self.selected_files:
            # Show just filename with path info
            path_obj = Path(file_path)
            display_name = f"{path_obj.name} ({path_obj.parent})"
            if len(display_name) > 80:
                display_name = f"{path_obj.name} (...{str(path_obj.parent)[-40:]})"
            self.file_listbox.insert(tk.END, display_name)
            
        # Update summary
        total_size = 0
        for file_path in self.selected_files:
            try:
                total_size += Path(file_path).stat().st_size
            except:
                pass
                
        size_str = self.format_bytes(total_size) if total_size > 0 else "Unknown"
        summary = f"{len(self.selected_files)} files selected ({size_str})"
        
        # Add summary at the end
        self.file_listbox.insert(tk.END, "")
        self.file_listbox.insert(tk.END, f"📊 {summary}")
        
    def on_drop(self, event):
        """Handle drag and drop events"""
        if not DRAG_DROP_AVAILABLE:
            return
            
        # Parse dropped files
        files = self.root.tk.splitlist(event.data)
        added_files = []
        
        for file_path in files:
            path_obj = Path(file_path)
            
            if path_obj.is_file():
                # Single file
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    added_files.append(path_obj.name)
            elif path_obj.is_dir():
                # Directory - add all files recursively
                for sub_file in path_obj.rglob('*'):
                    if sub_file.is_file():
                        sub_file_str = str(sub_file)
                        if sub_file_str not in self.selected_files:
                            self.selected_files.append(sub_file_str)
                            added_files.append(sub_file.name)
        
        if added_files:
            # Switch to files mode if not already
            self.source_mode.set("files")
            self.on_source_mode_change()
            
            self.update_file_list()
            self.log_message(f"Added {len(added_files)} files via drag and drop", "INFO")
            
            # Visual feedback
            self.dnd_label.configure(background='lightgreen')
            self.root.after(1000, lambda: self.dnd_label.configure(background='lightblue'))
        else:
            messagebox.showinfo("No New Files", "No new files were found in the dropped items.")
            
    @staticmethod
    def format_bytes(bytes_size):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
            
    def clear_output(self):
        """Clear the output text"""
        self.output_text.delete(1.0, tk.END)
        self.reset_stats()
        
    def check_github_status(self):
        """Check and display GitHub repository status"""
        if not self.github_manager:
            messagebox.showerror("GitHub Error", "GitHub functionality not available")
            return
        
        def check_status_thread():
            try:
                status = self.github_manager.get_repository_status()
                
                # Update UI in main thread
                def update_ui():
                    if "error" in status:
                        self.github_status_var.set(f"Error: {status['error']}")
                        self.log_message(f"GitHub Error: {status['error']}", "ERROR")
                    else:
                        branch = status.get('branch', 'unknown')
                        has_changes = status.get('has_changes', False)
                        modified = len(status.get('modified_files', []))
                        untracked = len(status.get('untracked_files', []))
                        staged = len(status.get('staged_files', []))
                        deleted = len(status.get('deleted_files', []))
                        revert_in_progress = status.get('revert_in_progress', False)
                        
                        status_text = f"Branch: {branch}"
                        if revert_in_progress:
                            status_text += " | Revert in progress"
                        elif has_changes:
                            status_text += f" | Changes: {modified}M {untracked}U {staged}S {deleted}D"
                        else:
                            status_text += " | No changes"
                        
                        self.github_status_var.set(status_text)
                        
                        # Log detailed status
                        self.log_message(f"GitHub Status - Branch: {branch}", "INFO")
                        if revert_in_progress:
                            self.log_message("  Revert operation in progress", "WARNING")
                        if has_changes:
                            self.log_message(f"  Modified: {modified}, Untracked: {untracked}, Staged: {staged}, Deleted: {deleted}", "INFO")
                            if status.get('modified_files'):
                                self.log_message(f"  Modified files: {', '.join(status['modified_files'][:3])}", "INFO")
                            if status.get('untracked_files'):
                                self.log_message(f"  Untracked files: {', '.join(status['untracked_files'][:3])}", "INFO")
                            if status.get('deleted_files'):
                                self.log_message(f"  Deleted files: {', '.join(status['deleted_files'][:3])}", "INFO")
                        else:
                            self.log_message("  No changes to commit", "INFO")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                def show_error():
                    self.github_status_var.set(f"Error: {str(e)}")
                    self.log_message(f"GitHub Status Error: {str(e)}", "ERROR")
                self.root.after(0, show_error)
        
        # Run in background thread
        threading.Thread(target=check_status_thread, daemon=True).start()
        self.github_status_var.set("Checking...")
    
    def push_to_github(self):
        """Push changes to GitHub repository"""
        if not self.github_manager:
            messagebox.showerror("GitHub Error", "GitHub functionality not available")
            return
        
        commit_msg = self.commit_message.get().strip()
        if not commit_msg:
            messagebox.showerror("GitHub Error", "Please enter a commit message")
            self.commit_entry.focus()
            return
        
        # Confirm push operation
        result = messagebox.askyesno(
            "Confirm Push", 
            f"This will add all changes, commit with message:\n\n'{commit_msg}'\n\nand push to GitHub. Continue?",
            icon='question'
        )
        
        if not result:
            return
        
        def push_thread():
            try:
                # Disable button during operation
                def disable_button():
                    self.github_push_button.config(state='disabled', text="Pushing...")
                    self.github_status_var.set("Pushing to GitHub...")
                self.root.after(0, disable_button)
                
                # Perform git operations
                success, message = self.github_manager.full_push_workflow(commit_msg, auto_add=True, handle_revert=True)
                
                # Update UI in main thread
                def update_ui():
                    self.github_push_button.config(state='normal', text="Push to GitHub")
                    
                    if success:
                        self.github_status_var.set("Push successful!")
                        self.log_message("GitHub Push Success:", "SUCCESS")
                        for line in message.split('\n'):
                            if line.strip():
                                self.log_message(f"  {line.strip()}", "INFO")
                        
                        # Clear commit message after successful push
                        self.commit_message.set("Update MyStorage files via GUI")
                        
                        messagebox.showinfo("Success", "Changes successfully pushed to GitHub!")
                    else:
                        self.github_status_var.set("Push failed")
                        self.log_message(f"GitHub Push Failed: {message}", "ERROR")
                        messagebox.showerror("GitHub Error", f"Failed to push changes:\n\n{message}")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                def show_error():
                    self.github_push_button.config(state='normal', text="Push to GitHub")
                    self.github_status_var.set(f"Error: {str(e)}")
                    self.log_message(f"GitHub Push Error: {str(e)}", "ERROR")
                    messagebox.showerror("GitHub Error", f"An error occurred:\n\n{str(e)}")
                self.root.after(0, show_error)
        
        # Run in background thread
        threading.Thread(target=push_thread, daemon=True).start()
        
    def reset_stats(self):
        """Reset statistics display"""
        for var in self.stats_vars.values():
            if 'size' in str(var):
                var.set("0 B")
            elif '%' in str(var):
                var.set("0%")
            elif 'ms' in str(var) or 's' in str(var):
                var.set("0 ms")
            else:
                var.set("0")
                
    def log_message(self, message, level="INFO"):
        """Add message to output log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_stats_from_output(self, line):
        """Parse output line and update statistics"""
        # Parse processing summary
        if "Files processed:" in line:
            match = re.search(r"Files processed: (\d+)", line)
            if match:
                self.stats_vars['processed'].set(match.group(1))
                
        elif "Files failed:" in line:
            match = re.search(r"Files failed: (\d+)", line)
            if match:
                self.stats_vars['failed'].set(match.group(1))
                
        elif "Total files:" in line:
            match = re.search(r"Total files: (\d+)", line)
            if match:
                self.stats_vars['total'].set(match.group(1))
                
        elif "Total input size:" in line:
            match = re.search(r"Total input size: ([\d.]+ \w+)", line)
            if match:
                self.stats_vars['input_size'].set(match.group(1))
                
        elif "Total output size:" in line:
            match = re.search(r"Total output size: ([\d.]+ \w+)", line)
            if match:
                self.stats_vars['output_size'].set(match.group(1))
                
        elif "Overall compression:" in line:
            match = re.search(r"Overall compression: ([\d.]+%)", line)
            if match:
                self.stats_vars['compression'].set(match.group(1))
                
        elif "Processing time:" in line:
            match = re.search(r"Processing time: (\d+ ms)", line)
            if match:
                self.stats_vars['time'].set(match.group(1))
                
        elif "Throughput:" in line:
            match = re.search(r"Throughput: ([\d.]+ \w+/s)", line)
            if match:
                self.stats_vars['throughput'].set(match.group(1))
                
    def start_processing(self):
        """Start the file processing"""
        if self.is_processing:
            return
            
        # Validate inputs
        if self.source_mode.get() == "files":
            if not self.selected_files:
                messagebox.showerror("Error", "Please select files to process or switch to folder mode")
                return
        else:
            if not self.source_folder.get().strip():
                messagebox.showerror("Error", "Please specify a source folder")
                return
            
        if not self.password.get().strip():
            messagebox.showerror("Error", "Please specify a password")
            return
            
        # Determine final output folder
        final_output_folder = self.get_final_output_folder()
            
        # Check if executable exists
        executable = "./high_performance_zipper"
        if not os.path.exists(executable):
            # Try to build it
            self.log_message("High-performance zipper not found, attempting to build...", "INFO")
            try:
                build_result = subprocess.run(["make", "performance"], 
                                            capture_output=True, text=True, timeout=30)
                if build_result.returncode != 0:
                    self.log_message(f"Build failed: {build_result.stderr}", "ERROR")
                    messagebox.showerror("Error", "Failed to build high-performance zipper")
                    return
                else:
                    self.log_message("Build successful!", "SUCCESS")
            except subprocess.TimeoutExpired:
                self.log_message("Build timed out", "ERROR")
                messagebox.showerror("Error", "Build process timed out")
                return
            except Exception as e:
                self.log_message(f"Build error: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Failed to build: {str(e)}")
                return
                
        # Start processing
        self.is_processing = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        self.progress_var.set("Processing files...")
        
        # Reset statistics
        self.reset_stats()
        
        self.log_message("Starting high-performance file processing...", "INFO")
        
        if self.source_mode.get() == "files":
            self.log_message(f"Processing {len(self.selected_files)} selected files", "INFO")
            total_size = sum(Path(f).stat().st_size for f in self.selected_files if Path(f).exists())
            self.log_message(f"Total size: {self.format_bytes(total_size)}", "INFO")
        else:
            self.log_message(f"Source folder: {self.source_folder.get()}", "INFO")
            
        self.log_message(f"Output folder: {final_output_folder}", "INFO")
        self.log_message(f"Parallel processing: {'Enabled' if self.use_parallel.get() else 'Disabled'}", "INFO")
        
        # Start processing thread
        threading.Thread(target=self.run_processing, daemon=True).start()
        
    def run_processing(self):
        """Run the processing in a separate thread"""
        try:
            # Prepare environment
            env = os.environ.copy()
            
            # Handle different processing modes
            if self.source_mode.get() == "files":
                # Process individual files
                success = self.process_individual_files()
            else:
                # Process folder using C++ backend
                success = self.process_folder_mode(env)
                
            # No need to copy files - they're already in the final location!
            
            # Update GUI from main thread
            if success:
                final_location = self.get_final_output_folder()
                self.root.after(0, lambda: self.log_message("Processing completed successfully! ✅", "SUCCESS"))
                self.root.after(0, lambda: self.log_message(f"ZIP files saved to: {final_location}", "SUCCESS"))
                self.root.after(0, lambda: self.progress_var.set("Processing completed successfully"))
            else:
                self.root.after(0, lambda: self.log_message("Processing failed ❌", "ERROR"))
                self.root.after(0, lambda: self.progress_var.set("Processing failed"))
                
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error during processing: {str(e)}", "ERROR"))
            self.root.after(0, lambda: self.progress_var.set("Processing error"))
        finally:
            # Clean up
            self.root.after(0, self.processing_finished)
            
    def process_individual_files(self):
        """Process individually selected files"""
        try:
            # Create final output directory (not temporary)
            final_output_path = Path(self.get_final_output_folder())
            final_output_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files to input directory temporarily for processing
            temp_input = final_output_path / "temp_input"
            temp_input.mkdir(exist_ok=True)
            
            # Copy selected files to temp input
            self.root.after(0, lambda: self.log_message("Preparing files for processing...", "INFO"))
            
            copied_files = []
            for i, file_path in enumerate(self.selected_files):
                if not self.is_processing:
                    break
                    
                source_path = Path(file_path)
                if source_path.exists():
                    # Create unique filename to avoid conflicts
                    dest_name = source_path.name
                    counter = 1
                    while (temp_input / dest_name).exists():
                        stem = source_path.stem
                        suffix = source_path.suffix
                        dest_name = f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    dest_path = temp_input / dest_name
                    shutil.copy2(source_path, dest_path)
                    copied_files.append(dest_name)
                    
                    # Update progress
                    progress = f"Prepared {i+1}/{len(self.selected_files)} files"
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda f=source_path.name: self.log_message(f"Prepared: {f}", "INFO"))
            
            if not copied_files:
                self.root.after(0, lambda: self.log_message("No valid files to process", "ERROR"))
                return False
                
            # Update environment to use temp input directory
            old_source = self.source_folder.get()
            self.source_folder.set(str(temp_input))
            
            # Process using C++ backend
            self.root.after(0, lambda: self.log_message("Starting compression...", "INFO"))
            success = self.run_cpp_backend()
            
            # Restore original source folder
            self.source_folder.set(old_source)
            
            # Clean up temp directory
            try:
                shutil.rmtree(temp_input)
            except:
                pass  # Best effort cleanup
                
            return success
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error processing individual files: {str(e)}", "ERROR"))
            return False
            
    def process_folder_mode(self, env):
        """Process folder using original C++ backend"""
        # Create directories if they don't exist
        source_path = Path(self.source_folder.get())
        final_output_path = Path(self.get_final_output_folder())
        
        if not source_path.exists():
            source_path.mkdir(parents=True, exist_ok=True)
            self.root.after(0, lambda: self.log_message(f"Created source directory: {source_path}", "INFO"))
            
        if not final_output_path.exists():
            final_output_path.mkdir(parents=True, exist_ok=True)
            self.root.after(0, lambda: self.log_message(f"Created final output directory: {final_output_path}", "INFO"))
            
        return self.run_cpp_backend()
        
    def run_cpp_backend(self):
        """Run the C++ backend process"""
        try:
            # Set environment variables for the C++ program
            env = os.environ.copy()
            env['ZIPPER_INPUT_FOLDER'] = self.source_folder.get()
            
            # Use final output destination directly - no copying needed!
            final_output = self.get_final_output_folder()
            env['ZIPPER_OUTPUT_FOLDER'] = final_output
            env['ZIPPER_PASSWORD'] = self.password.get()
            
            self.root.after(0, lambda: self.log_message(f"ZIP files will be saved directly to: {final_output}", "INFO"))
            
            # Run the high-performance zipper
            cmd = ["./high_performance_zipper"]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # Read output line by line
            for line in self.process.stdout:
                if not self.is_processing:
                    break
                    
                line = line.strip()
                if line:
                    # Update GUI from main thread
                    self.root.after(0, lambda l=line: self.log_message(l, "OUTPUT"))
                    self.root.after(0, lambda l=line: self.update_stats_from_output(l))
            
            # Wait for process to complete
            return_code = self.process.wait()
            return return_code == 0
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Backend process error: {str(e)}", "ERROR"))
            return False
            
    def stop_processing(self):
        """Stop the current processing"""
        if self.is_processing and self.process:
            self.log_message("Stopping processing...", "WARNING")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.log_message("Process forcefully terminated", "WARNING")
        
        self.processing_finished()
        
    def processing_finished(self):
        """Clean up after processing is finished"""
        self.is_processing = False
        self.process = None
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        
        if self.progress_var.get() == "Processing files...":
            self.progress_var.set("Ready to process files")
            
    def get_final_output_folder(self):
        """Get the final output folder"""
        return self.output_folder.get().strip()
    
    def delete_selected_from_tree(self, tree):
        """Delete selected files/folders from tree view"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select files or folders to delete.")
            return
            
        # Get folder path
        folder_path = getattr(tree, 'folder_path', None)
        if not folder_path:
            messagebox.showerror("Error", "Cannot determine folder path for deletion.")
            return
            
        # Build list of items to delete with their full paths
        items_to_delete = []
        for item_id in selection:
            item_path = self.get_item_full_path(tree, item_id, folder_path)
            if item_path:
                items_to_delete.append((item_id, item_path))
        
        if not items_to_delete:
            messagebox.showinfo("No Selection", "Please select valid files or folders to delete.")
            return
            
        # Show confirmation dialog
        item_names = [Path(path).name for _, path in items_to_delete]
        item_list = '\n'.join(f"• {name}" for name in item_names[:10])  # Show first 10
        if len(item_names) > 10:
            item_list += f"\n... and {len(item_names) - 10} more items"
            
        confirm_msg = f"Are you sure you want to permanently delete these {len(items_to_delete)} item(s)?\n\n{item_list}"
        
        if messagebox.askyesno("Confirm Deletion", confirm_msg, icon='warning'):
            try:
                popup_window = tree.popup_window
                popup_title = tree.popup_title
                
                deleted_count = 0
                failed_items = []
                
                for item_id, item_path in items_to_delete:
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            deleted_count += 1
                            self.log_message(f"Deleted file: {Path(item_path).name}", "INFO")
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            deleted_count += 1
                            self.log_message(f"Deleted folder: {Path(item_path).name}", "INFO")
                    except Exception as e:
                        failed_items.append(f"{Path(item_path).name}: {str(e)}")
                        self.log_message(f"Failed to delete {Path(item_path).name}: {str(e)}", "ERROR")
                
                # Show results
                if deleted_count > 0:
                    messagebox.showinfo("Deletion Complete", 
                                      f"Successfully deleted {deleted_count} item(s).")
                
                if failed_items:
                    failed_msg = "Failed to delete:\n" + '\n'.join(failed_items[:5])
                    if len(failed_items) > 5:
                        failed_msg += f"\n... and {len(failed_items) - 5} more"
                    messagebox.showerror("Deletion Errors", failed_msg)
                
                # Refresh the view
                popup_window.destroy()
                self.show_folder_contents(popup_title, folder_path)
                
            except Exception as e:
                messagebox.showerror("Error", f"Deletion failed: {str(e)}")
                
    def get_item_full_path(self, tree, item_id, base_path):
        """Get the full path of a tree item by traversing up the tree"""
        try:
            path_parts = []
            current_item = item_id
            
            while current_item:
                item = tree.item(current_item)
                if item['values']:
                    path_parts.append(item['values'][0])  # item name
                current_item = tree.parent(current_item)
            
            # Reverse to get correct order (root to leaf)
            path_parts.reverse()
            
            if path_parts:
                return os.path.join(base_path, *path_parts)
            return None
            
        except Exception as e:
            self.log_message(f"Error getting item path: {str(e)}", "ERROR")
            return None
                
    def show_selected_in_explorer(self, tree):
        """Show selected file/folder in system explorer"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a file or folder to show in explorer.")
            return
            
        # Get folder path
        folder_path = getattr(tree, 'folder_path', None)
        if not folder_path:
            messagebox.showerror("Error", "Cannot determine folder path.")
            return
            
        # Get full path of selected item
        item_path = self.get_item_full_path(tree, selection[0], folder_path)
        if not item_path:
            messagebox.showerror("Error", "Cannot determine item path.")
            return
            
        try:
            if os.path.exists(item_path):
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', '/select,', item_path])
                elif os.name == 'posix':  # Linux/Mac
                    if os.path.isdir(item_path):
                        subprocess.run(['xdg-open', item_path])
                    else:
                        subprocess.run(['xdg-open', os.path.dirname(item_path)])
            else:
                messagebox.showerror("Error", f"Item not found: {Path(item_path).name}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show in explorer: {str(e)}")
            
    def delete_from_source_files(self):
        """Delete selected files from source file list permanently"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select files to delete from the list.")
            return
            
        selected_files = [self.selected_files[i] for i in selection if i < len(self.selected_files)]
        
        if not selected_files:
            messagebox.showinfo("No Selection", "Please select valid files to delete.")
            return
            
        # Confirm deletion
        file_names = [Path(f).name for f in selected_files]
        file_list = '\n'.join(f"• {name}" for name in file_names[:10])  # Show first 10
        if len(file_names) > 10:
            file_list += f"\n... and {len(file_names) - 10} more files"
            
        confirm_msg = f"Are you sure you want to permanently delete these {len(selected_files)} file(s) from disk?\n\n{file_list}"
        
        if messagebox.askyesno("Confirm Deletion", confirm_msg, icon='warning'):
            try:
                deleted_count = 0
                failed_files = []
                
                # Delete in reverse order to maintain indices for removal from list
                for i in reversed(selection):
                    if i < len(self.selected_files):
                        file_path = self.selected_files[i]
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                deleted_count += 1
                                self.log_message(f"Deleted: {Path(file_path).name}", "INFO")
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                deleted_count += 1
                                self.log_message(f"Deleted folder: {Path(file_path).name}", "INFO")
                            
                            # Remove from selected files list
                            self.selected_files.pop(i)
                            
                        except Exception as e:
                            failed_files.append(f"{Path(file_path).name}: {str(e)}")
                            self.log_message(f"Failed to delete {Path(file_path).name}: {str(e)}", "ERROR")
                
                # Update the file list display
                self.update_file_list()
                
                # Show results
                if deleted_count > 0:
                    messagebox.showinfo("Deletion Complete", 
                                      f"Successfully deleted {deleted_count} file(s) from disk.")
                
                if failed_files:
                    failed_msg = "Failed to delete:\n" + '\n'.join(failed_files[:5])
                    if len(failed_files) > 5:
                        failed_msg += f"\n... and {len(failed_files) - 5} more"
                    messagebox.showerror("Deletion Errors", failed_msg)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Deletion failed: {str(e)}")

    def open_folder_in_explorer(self, folder_path):
        """Open folder in system file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
            
def main():
    """Main application entry point"""
    try:
        if DRAG_DROP_AVAILABLE:
            root = TkinterDnD.Tk()
        else:
            root = tk.Tk()
            
        app = HighPerformanceZipperGUI(root)
        
        # Handle window close
        def on_closing():
            if app.is_processing:
                if messagebox.askokcancel("Quit", "Processing is running. Do you want to stop and quit?"):
                    app.stop_processing()
                    root.after(1000, root.destroy)  # Give time for cleanup
                else:
                    return
            else:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
