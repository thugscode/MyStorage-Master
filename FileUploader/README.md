# High-Performance File Zipper

A fast, secure C++ application that creates password-protected ZIP files for each file in a directory, with parallel processing and real-time monitoring.

## Features

- **🔒 Security**: AES-256 encryption for all ZIP files
- **⚡ Performance**: Multi-threaded processing with up to 8x speed improvement
- **🎯 Smart Processing**: Automatic thread optimization and load balancing
- **📊 Real-time Monitoring**: Live statistics and progress tracking
- **🖥️ Multiple Interfaces**: Command-line and modern GUI options
- **🔄 Duplicate Detection**: Skips files that are already processed and up-to-date
- **📈 Comprehensive Analytics**: Compression ratios, throughput, and timing data

## Quick Start

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libzip-dev build-essential python3-tkinter

# Optional: For drag and drop support in GUI
pip install tkinterdnd2

# Fedora/CentOS/RHEL
sudo dnf install -y libzip-devel gcc-c++ make python3-tkinter
pip install tkinterdnd2  # Optional drag and drop
```

### Build and Run
```bash
# Build the high-performance version
make

# Run with command line interface
./high_performance_zipper

# Run with graphical interface
python3 high_performance_gui_zipper.py

# Run one-click script
./run_zipper.sh
```

## Usage

### Directory Structure
```
FileUploader/
├── input/          # Place your files here
├── output/         # ZIP files will be created here
├── high_performance_zipper
├── high_performance_gui_zipper.py
└── run_zipper.sh
```

### Command Line Interface
1. Place files in the `input/` directory
2. Run `./high_performance_zipper`
3. Find password-protected ZIP files in `output/`

### Graphical Interface
1. Run `python3 high_performance_gui_zipper.py`
2. **Choose processing mode**:
   - **Input Folder Mode**: Process all files from a specific folder (original behavior)
   - **Individual Files Mode**: Select specific files and folders to process
3. **File Selection Options** (Individual Files Mode):
   - Click **"Add Files"** to select specific files
   - Click **"Add Folder"** to add all files from a folder
   - **Drag and drop** files/folders directly (requires `tkinterdnd2`)
   - **Right-click** file list for context menu (remove, clear, show location)
4. **Optional**: Enable "Use custom storage location" to save ZIP files to a different folder
5. Set performance options (parallel processing, thread count)
6. Click "Start Processing" to begin
7. Monitor real-time progress and statistics

### One-Click Operation
```bash
./run_zipper.sh  # Automated processing with default settings
```

## Configuration

### Default Settings
- **Input Folder**: `input/`
- **Output Folder**: `output/`
- **Password**: `SecurePass2025!`
- **Encryption**: AES-256
- **Compression**: Maximum (Level 9)
- **Threads**: Auto-detected (up to 8)

### Customization
Edit the configuration constants in `high_performance_zipper.cpp`:
```cpp
static constexpr std::string_view INPUT_FOLDER = "input";

static constexpr std::string_view PASSWORD = "SecurePass2025!";
static constexpr size_t MAX_THREADS = 8;
```

## Build Options

### Standard Build
```bash
make                    # Build high-performance version (default)
make performance        # Same as above with maximum optimizations
```

### Development Builds
```bash
make debug             # Debug version with sanitizers
make profile           # Profiling version for performance analysis
```

### Testing and Analysis
```bash
make benchmark         # Compare performance with timing
make performance-test  # Comprehensive test suite with synthetic data
make memory-check      # Memory analysis with valgrind
make cpu-profile       # Generate CPU profiling report
make static-analysis   # Run static code analysis
```

### Utility Commands
```bash
make clean            # Remove build files
make clean-all        # Remove build files and output directory
make help             # Show all available commands
```

## Performance Features

### Multi-Threading Architecture
- **Automatic Core Detection**: Uses optimal thread count for your CPU
- **Smart Load Balancing**: Processes largest files first for better utilization
- **Thread-Safe Operations**: Lock-free statistics with atomic operations
- **Adaptive Strategy**: Chooses sequential vs parallel based on file characteristics

### Memory Optimizations
- **Memory Pools**: Efficient allocation using `std::pmr`
- **Reduced Allocations**: Pre-reserved containers and move semantics
- **Cache-Friendly Design**: Optimized data structures for CPU cache performance

### I/O Optimizations
- **Cached Timestamps**: Avoids repeated filesystem calls (60-80% reduction)
- **Batch Operations**: O(1) lookup for existing files
- **Optimized File Handling**: Different strategies for small vs large files

### Compilation Optimizations
- **C++20 Features**: Latest standard with modern optimizations
- **Link-Time Optimization**: Cross-module optimizations with `-flto`
- **Architecture-Specific**: CPU-optimized code with `-march=native`
- **Advanced Flags**: Loop unrolling, function inlining, frame pointer omission

## Performance Benchmarks

### Expected Improvements
| Metric | Improvement |
|--------|-------------|
| **Processing Speed** | 3-8x faster (multi-core systems) |
| **Memory Usage** | 25-35% reduction |
| **I/O Operations** | 60-80% fewer filesystem calls |
| **CPU Utilization** | Linear scaling across cores |

### Test Results
Run comprehensive benchmarks:
```bash
make performance-test
```

This creates test files of various sizes and compares performance across different scenarios.

## GUI Features

### Real-Time Monitoring
- **Live Statistics**: Files processed, compression ratios, throughput
- **Progress Tracking**: Current file and overall completion
- **Error Reporting**: Detailed error messages and recovery options
- **Performance Metrics**: Processing time, memory usage, CPU utilization

### File Selection Options
- **Folder Mode**: Process all files from an input directory (original mode)
- **Individual Files**: Select specific files to process
- **Folder Addition**: Add all files from selected folders
- **Mixed Selection**: Combine files from different locations
- **Drag and Drop**: Intuitive file selection (with tkinterdnd2)
- **Context Menu**: Right-click management (remove, clear, show location)

### Advanced Options
- **Custom Directories**: Browse and select input/output folders
- **Custom Storage Location**: Save ZIP files to any folder on your system
- **Password Configuration**: Set custom encryption passwords
- **Thread Control**: Adjust maximum thread count
- **Processing Options**: Enable/disable parallel processing

### User Experience
- **Modern Interface**: Clean, responsive Tkinter-based GUI
- **Flexible File Selection**: Choose between folder and individual file modes
- **Drag and Drop**: Intuitive file management (optional tkinterdnd2)
- **Flexible Storage**: Choose any location to save your ZIP files
- **Auto-Building**: Automatically compiles the C++ binary if needed
- **Error Handling**: Comprehensive error recovery and user feedback
- **Progress Indication**: Visual progress bars and status updates
- **Storage Management**: Automatic directory creation and file copying
- **Context Menus**: Right-click file management options

## Security

### Encryption
- **Algorithm**: AES-256 (Advanced Encryption Standard)
- **Key Derivation**: PBKDF2 with salt
- **Integrity**: CRC32 checksums for data verification
- **Standards Compliance**: ZIP specification compatible

### Best Practices
- Use strong, unique passwords for sensitive data
- Store passwords securely (consider using password managers)
- Regularly update the application for security patches
- Verify ZIP file integrity after creation

## File Processing Logic

### Duplicate Detection
- **Timestamp Comparison**: Only processes files newer than existing ZIPs
- **Cached Lookups**: Maintains timestamp cache for performance
- **Smart Skipping**: Avoids reprocessing unchanged files

### Error Handling
- **Graceful Recovery**: Continues processing other files on individual failures
- **Cleanup**: Automatically removes incomplete ZIP files
- **Detailed Logging**: Comprehensive error reporting and diagnostics

### Compression Strategy
- **Maximum Compression**: Uses deflate level 9 for best space savings
- **Adaptive Processing**: Different strategies for various file sizes
- **Progress Reporting**: Real-time compression ratio calculations

## Technical Architecture

### Core Components
- **HighPerformanceFileZipper**: Main processing engine with multi-threading
- **ThreadSafeStats**: Lock-free statistics collection using atomic operations
- **ZipArchive**: RAII wrapper for libzip with automatic resource management
- **MemoryPool**: Efficient memory allocation using std::pmr

### Dependencies
- **libzip**: ZIP file creation and encryption
- **C++20 Compiler**: GCC 9+ or Clang 10+
- **pthread**: Multi-threading support
- **Python 3**: GUI interface (optional)
- **Tkinter**: GUI framework (usually included with Python)

### Platform Support
- **Linux**: Primary platform (Ubuntu, Debian, Fedora, CentOS, RHEL)
- **macOS**: Compatible with Homebrew-installed dependencies
- **Windows**: WSL2 or native compilation with MinGW

## Troubleshooting

### Common Issues

**Build Errors**
```bash
# Missing libzip
sudo apt-get install libzip-dev  # Ubuntu/Debian
sudo dnf install libzip-devel    # Fedora/CentOS

# Compiler too old
gcc --version  # Needs GCC 9+ for C++20
```

**Runtime Issues**
```bash
# Permission errors
chmod +x high_performance_zipper
chmod +x run_zipper.sh

# Missing directories
mkdir -p input output
```

**GUI Problems**
```bash
# Missing Tkinter
sudo apt-get install python3-tkinter  # Ubuntu/Debian
sudo dnf install python3-tkinter       # Fedora/CentOS
```

### Performance Tuning

**For Large Files (>100MB each)**
- Increase thread count in configuration
- Use SSD storage for input/output directories
- Ensure sufficient RAM (2x largest file size)

**For Many Small Files (1000+ files)**
- Enable parallel processing
- Use maximum thread count
- Consider batch processing in smaller groups

**For Limited Resources**
- Reduce thread count to 2-4
- Use sequential processing mode
- Monitor memory usage with `make memory-check`

## Development

### Code Structure
```
high_performance_zipper.cpp     # Main C++ implementation
high_performance_gui_zipper.py  # Python GUI interface
performance_test.sh             # Automated testing suite
Makefile                        # Build system with multiple targets
run_zipper.sh                   # One-click automation script
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Run tests: `make performance-test`
4. Submit pull request with performance benchmarks

### Testing
```bash
# Unit tests (built into performance-test)
make performance-test

# Memory leak detection
make memory-check

# Performance profiling
make cpu-profile

# Static analysis
make static-analysis
```

## Delete Functionality

The application provides comprehensive delete functionality for both source files and output ZIP files:

### Source File Management
- **Remove from List**: Remove files from the processing list without deleting from disk
- **Delete from Disk**: Permanently delete selected files from the filesystem
- **Context Menu**: Right-click on files in the list for quick access to delete options
- **Delete Button**: Use the "Delete Selected" button for easy file deletion

### Output File Management
- **View Output Folder**: Browse and manage created ZIP files
- **Delete ZIP Files**: Remove individual ZIP files or entire folders
- **Nested Folder Support**: Navigate and delete from subdirectories
- **Batch Deletion**: Select multiple items for simultaneous deletion

### Safety Features
- **Confirmation Dialogs**: All delete operations require user confirmation
- **Error Handling**: Graceful handling of permission errors and file locks
- **Detailed Feedback**: Progress logging and error reporting
- **Undo Protection**: Clear warnings about permanent deletion

### How to Use Delete Features

1. **Deleting Source Files**:
   - Select files in the file list
   - Right-click to open context menu
   - Choose "Delete from Disk" for permanent deletion
   - Or use the "Delete Selected" button

2. **Deleting Output Files**:
   - Click "View" button next to output folder
   - Navigate through the folder structure
   - Right-click on files/folders to delete
   - Confirm deletion in the dialog

3. **Context Menu Options**:
   - **Remove from List**: Removes from processing list only
   - **Delete from Disk**: Permanently deletes the file
   - **Clear All**: Removes all files from the list
   - **Show in Explorer**: Opens file location in system explorer

# FileUploader Directory

This directory contains the main GUI application and configuration for interacting with the MyStorage GitHub repository.

## Key Files

### 1. `high_performance_gui_zipper.py`
- **Description:**
  - Main Python GUI application for file zipping and GitHub integration.
  - Allows users to select files, zip them, and push changes to the MyStorage GitHub repository directly from the GUI.
- **Features:**
  - Modern Tkinter-based interface
  - GitHub integration (commit, push, check status)
  - Reads credentials from `credentials.json`
  - Drag-and-drop support (if `tkinterdnd2` is installed)
- **Usage:**
  - Run with: `python3 high_performance_gui_zipper.py`
  - Make sure `credentials.json` is present and contains valid GitHub credentials (see below).

### 2. `credentials.json`
- **Description:**
  - Stores confidential GitHub credentials for use by the GUI and automation scripts.
- **Format:**
  ```json
  {
      "github_token": "<YOUR_GITHUB_TOKEN_HERE>",
      "github_user": "<YOUR_GITHUB_USERNAME_HERE>",
      "github_email": "<YOUR_GITHUB_EMAIL_HERE>"
  }
  ```
- **Security:**
  - **Never commit this file to a public repository!**
  - Add `credentials.json` to your `.gitignore` file.
  - Treat your token as a password—keep it private.

## Setup Instructions
1. Copy `credentials.json.example` to `credentials.json` and fill in your details.
2. Run the GUI: `python3 high_performance_gui_zipper.py`
3. Use the GitHub controls in the GUI to commit and push changes.


## Notes
- For automation (e.g., GitHub Actions), use the built-in `GITHUB_TOKEN` instead of a personal token.
- If you change your GitHub token, update `credentials.json` accordingly.
