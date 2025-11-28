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
3. Run the conversion:

```bash
python convert_dayone_to_obsidian.py
```

Your converted files will be in the `output/journal-entries/` folder.

## Requirements

- Python 3.6+ (uses only standard library)
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

The script automatically converts UTC timestamps to Central Time (America/Chicago) with full DST awareness. Other timezones are supported - modify the timezone mappings in the script if needed.

## Logging

- Console output shows conversion progress and statistics
- Detailed log written to `output/conversion_log.txt`
- Verbose mode available with `-v` flag

## Files

- `dayone_to_obsidian.py` - Main conversion script
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
