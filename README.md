# DayOne to Obsidian Converter

A Python script that converts DayOne journal exports to Obsidian-compatible Markdown files with proper frontmatter, image handling, and timezone conversion.

## Features

- **Complete Conversion**: Converts DayOne JSON exports to individual Markdown files
- **Smart Frontmatter**: Extracts metadata (dates, location, weather, tags) into YAML frontmatter
- **Image Handling**: Converts DayOne image references to Obsidian wiki-links and copies photo files
- **Timezone Support**: Converts UTC timestamps to local timezone (with DST awareness)
- **Duplicate Detection**: Skip or update existing entries based on modification dates
- **Obsidian Maps Integration**: Formats coordinates for the Obsidian Maps plugin

## Quick Start

1. Export your DayOne journal as JSON (with photos)
2. Place the script in the same directory as your export files
3. (Optional) Copy `.env.example` to `.env` and customize settings
4. Run the conversion:

```bash
python convert_dayone_to_obsidian.py
```

Your converted files will be in the `output/journal-entries/` folder.

## Requirements

- Python 3.6+
- python-dotenv package (install with: `pip install python-dotenv`)
- DayOne JSON export file
- Photos folder (if your journal contains images)

## Usage

### Basic Usage
```bash
# Convert with default settings
python convert_dayone_to_obsidian.py

# Specify custom input/output paths
python convert_dayone_to_obsidian.py -i "DayOne Export.json" -o "C:\Obsidian\Vault\Journal"
```

### Advanced Options
```bash
# Update mode - overwrite files if they've been modified
python convert_dayone_to_obsidian.py --update

# Preview changes without making them
python convert_dayone_to_obsidian.py --dry-run --verbose

# Get help
python convert_dayone_to_obsidian.py --help
```

## Configuration

You can customize the converter's behavior using a `.env` file. Copy `.env.example` to `.env` and modify the values:

```bash
cp .env.example .env
```

### Available Settings

- **`INPUT_FILE`**: Default input JSON filename (default: `DayOne Journal.json`)
- **`OUTPUT_DIR`**: Output directory path (default: `./output`)
- **`DEFAULT_TIMEZONE`**: Your local timezone for date conversion (default: `America/Chicago`)
  - Supported: `America/Chicago`, `America/New_York`, `America/Denver`, `America/Los_Angeles`, `America/Phoenix`, `UTC`
- **`MAX_FILENAME_LENGTH`**: Maximum filename length in characters (default: `50`)
- **`UUID_PREFIX_LENGTH`**: Number of UUID characters in filenames (default: `8`)
- **`JOURNAL_ENTRIES_SUBDIR`**: Subdirectory name for entries (default: `journal-entries`)
- **`PHOTOS_SUBDIR`**: Subdirectory name for photos (default: `photos`)
- **`FALLBACK_TITLE`**: Title for entries without text (default: `Untitled`)
- **`LOG_FILENAME`**: Log file name (default: `conversion_log.txt`)

### Configuration Priority

Command-line arguments override `.env` settings:
1. Command-line arguments (highest priority)
2. `.env` file settings
3. Default values (lowest priority)

### Example `.env` File

```bash
# File paths
INPUT_FILE=My Journal Export.json
OUTPUT_DIR=C:\Obsidian\MyVault\Journal

# Timezone
DEFAULT_TIMEZONE=America/New_York

# Filename settings
MAX_FILENAME_LENGTH=60
UUID_PREFIX_LENGTH=6
```

## Output Structure

```
output/
└── journal-entries/
    ├── 2025-10-01 Tried today oh so tired (008446A5).md
    ├── 2025-10-28 Fire Department (032DB438).md
    ├── ...
    └── photos/
        ├── F27EAA706C554535BECEF55B662F7862.jpeg
        └── ...
```

## File Format

Each Markdown file includes:

- **YAML Frontmatter**: UUID, dates, location, coordinates, weather, tags, device info
- **Converted Content**: Original text with DayOne image links converted to Obsidian format
- **Local Timestamps**: All dates converted from UTC to your local timezone

### Example Output

```markdown
---
uuid: 032DB4389D7C43D5821F60C67C3846A4
date: 2025-10-28T03:26:56
modified: 2025-10-28T03:28:39
location: "123 Main Street, Anytown, ST, USA"
coordinates:
  - "40.7128"
  - "-74.0060"
weather: "Partly Cloudy, 48°F"
tags:
  - family
  - scouts
starred: false
device: iPhone
timezone: America/Chicago
---

# Fire department

Had a great time visiting the fire station today!

![[photos/F27EAA706C554535BECEF55B662F7862.jpeg]]
```

## What Gets Converted

- **Text Content**: Preserved as-is (already in Markdown format)
- **Images**: `![](dayone-moment://ID)` → `![[photos/ID.jpeg]]`
- **Dates**: UTC timestamps → Local timezone (with DST handling)
- **Weather**: Celsius temperatures → Fahrenheit
- **Metadata**: All journal metadata preserved in frontmatter

## Timezone Support

The script automatically converts UTC timestamps to your local timezone with full DST awareness. By default, it uses Central Time (America/Chicago). To change this, set `DEFAULT_TIMEZONE` in your `.env` file.

Supported timezones:
- `America/Chicago` (Central)
- `America/New_York` (Eastern)
- `America/Denver` (Mountain)
- `America/Los_Angeles` (Pacific)
- `America/Phoenix` (Arizona, no DST)
- `UTC`

## Logging

- Console output shows conversion progress and statistics
- Detailed log written to `output/conversion_log.txt`
- Verbose mode available with `-v` flag

## Files

- `convert_dayone_to_obsidian.py` - Main conversion script
- `.env.example` - Template for environment variables
- `.env` - Your local configuration (create from `.env.example`)
- `REQUIREMENTS.md` - Detailed technical specifications
- `README.md` - This file

## Getting Your DayOne Export

1. Open DayOne app
2. Go to File → Export → JSON
3. Choose "Export photos" option
4. Save the export (creates a JSON file and photos folder)
5. Place both in the same directory as this script

## Using in Obsidian

1. Copy the `journal-entries` folder to your Obsidian vault
2. The files will appear as individual notes with rich metadata
3. Images will display properly using Obsidian's image syntax
4. Install the Maps plugin to use the coordinate data for location visualization

## Troubleshooting

- **Missing photos**: Check that the photos folder is in the same directory as the JSON file
- **Encoding issues**: The script handles UTF-8 encoding for emoji and international characters
- **Duplicate entries**: Use `--update` mode to handle modified entries
- **Timezone issues**: Script defaults to Central Time; modify timezone mappings if needed

## License


This script is provided as-is for personal use. Feel free to modify and adapt for your needs.
