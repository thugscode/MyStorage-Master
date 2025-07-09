# MyStorage Directory

This directory contains the static web files and assets for the MyStorage project.

## Contents
- **index.html**: Main entry point for the web application.
- **generate-hash.html**: Utility page for generating file hashes.
- **script.js**: Main JavaScript logic for the web app.
- **mobile.js**: JavaScript for mobile-specific features.
- **security-utils.js**: Security and cryptography helper functions.
- **styles.css**: Main stylesheet for the web app.
- **files/**: Directory for uploaded or managed files.

## Usage
- Open `index.html` in your browser to use the MyStorage web application.
- Use the GUI or CLI tools in the parent directory to manage and push changes to GitHub.

## GitHub Integration
- This folder is a Git repository and can be managed using the GUI (`high_performance_gui_zipper.py`) or CLI tools in the parent directory.
- All changes to files in this directory can be committed and pushed to GitHub using those tools.

## Security
- Do not store sensitive credentials or tokens in this directory.
- All authentication for GitHub operations is handled by the parent directory's configuration.

## Automation
- For CI/CD or GitHub Actions, use the built-in `GITHUB_TOKEN` for repository operations.

## License
This project is for educational and personal use. Please see the root project for license details.
