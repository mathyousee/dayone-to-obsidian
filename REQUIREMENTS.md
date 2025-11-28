# DayOne to Obsidian Markdown Converter - Requirements

## Overview
A Python script to convert DayOne journal exports (JSON format) into individual Markdown files optimized for use in Obsidian.

---

## Input
- **Source file:** `DayOne Export.json` (DayOne export format)
- **Photos folder:** `photos/` directory containing referenced images
- **Location:** Script will run from the export directory

---

## Output

### File Structure
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

### Filename Format
```
YYYY-MM-DD Title Snippet (UUID8).md
```
- **Date:** Extracted from `creationDate`, converted to local timezone, formatted as `YYYY-MM-DD`
- **Title Snippet:** Up to ~50 characters, extracted and sanitized as follows:
  1. **Prefer header line:** If content starts with `# Header Text`, use the header text
  2. **Strip Markdown:** Remove leading `#` symbols and trim whitespace
  3. **Fallback:** If no header, use first ~50 characters of body text
  4. **Sanitize:** Remove/replace special characters: `< > : " / \ | ? *`
  5. **Trim:** Remove leading/trailing whitespace
  6. **Truncate:** Cut at word boundary if over 50 characters
  7. **Empty fallback:** If no usable text, use "Untitled"
- **UUID8:** First 8 characters of the entry's `uuid` field
- **Example:** `2025-10-28 Fire Department (032DB438).md`

---

## Frontmatter (YAML)

Each Markdown file will include YAML frontmatter with the following properties:

```yaml
---
uuid: 032DB4389D7C43D5821F60C67C3846A4
date: 2025-10-28T03:26:56Z
modified: 2025-10-28T03:28:39Z
location: "123 Main Street, Anytown, ST, USA"
coordinates:
  - "40.7128"
  - "-74.0060"
weather: "Partly Cloudy, 48°F"
tags:
  - tag1
  - tag2
starred: false
pinned: false
device: iPhone
timezone: America/Chicago
---
```

### Property Mapping
| Frontmatter Key | Source Field | Notes |
|-----------------|--------------|-------|
| `uuid` | `uuid` | Full UUID for future reference |
| `date` | `creationDate` | ISO 8601 format, converted to local timezone |
| `modified` | `modifiedDate` | ISO 8601 format, converted to local timezone |
| `location` | `location.address` | String, quoted if contains special chars |
| `coordinates` | `location.latitude`, `location.longitude` | YAML list format with quoted strings (Maps plugin compatible) |
| `weather` | `weather.conditionsDescription`, `weather.temperatureCelsius` | Formatted string with °F conversion |
| `tags` | `tags` | Array format |
| `starred` | `starred` | Boolean |
| `pinned` | `isPinned` | Boolean |
| `device` | `creationDevice` | String |
| `timezone` | `timeZone` | String |

### Handling Missing Data
- If a property is missing or empty, omit it from frontmatter entirely
- If `location` object exists but `address` is missing, omit `location`
- If `tags` array is empty, omit `tags`

### Timezone Conversion
- All timestamps in DayOne exports are in UTC format
- Script converts dates to local timezone (defaults to America/Chicago - Central Time)
- **DST Awareness**: Automatically detects and applies Daylight Saving Time offsets
  - Standard Time: UTC-6 (Central Standard Time)
  - Daylight Time: UTC-5 (Central Daylight Time)
- Dates are formatted without timezone suffix for cleaner frontmatter
- Original timezone information preserved in `timezone` field

### Coordinates Format
- Formatted as YAML list with quoted strings for Obsidian Maps plugin compatibility
- Format: `coordinates:\n  - "latitude"\n  - "longitude"`
- Compatible with Obsidian Maps plugin for location visualization

---

## Content Conversion

### Text Body
- Use the `text` field (already Markdown formatted)
- Skip the `richText` field (not needed)

### Image References
Convert DayOne image syntax to Obsidian wiki-link syntax:

**From:**
```markdown
![](dayone-moment://F27EAA706C554535BECEF55B662F7862)
```

**To:**
```markdown
![[photos/F27EAA706C554535BECEF55B662F7862.jpeg]]
```

### Image File Handling
- Match image `identifier` from entry's `photos` array to files in source `photos/` folder
- Copy referenced photos to output `photos/` folder with normalized extensions
- **Extension Normalization**: 
  - Source files may use `.jpg` extension
  - Output files use `.jpeg` extension for consistency
  - Script handles both `.jpg` and `.jpeg` extensions automatically
- Determine extension from `type` field in photos array or file system detection
- Supports multiple image formats: JPEG, PNG, GIF, HEIC

---

## Duplicate Detection & Update Mode

### Detection Method
- Check for existing files matching pattern `*(UUID8).md` in output directory
- UUID8 = first 8 characters of entry UUID

### Modes

#### Skip Mode (Default)
- If file with matching UUID exists, skip the entry
- Log skipped entries

#### Update Mode (`--update` flag)
- If file with matching UUID exists:
  - Compare `modifiedDate` from JSON with `modified` in existing file's frontmatter
  - If JSON's `modifiedDate` is newer, overwrite the file
  - If dates match or existing is newer, skip
- Log updated vs skipped entries

---

## Command Line Interface

```bash
python dayone_to_obsidian.py [OPTIONS]

Options:
  --input, -i      Path to JSON file (default: "DayOne Export.json")
  --output, -o     Output directory (default: "./output")
  --update, -u     Enable update mode (overwrite if modified)
  --dry-run        Show what would be done without making changes
  --verbose, -v    Verbose logging
  --help, -h       Show help message
```

### Example Usage
```bash
# Basic conversion
python dayone_to_obsidian.py

# Custom paths
python dayone_to_obsidian.py -i "DayOne Export.json" -o "C:\Obsidian\Vault\Journal"

# Update existing entries if modified
python dayone_to_obsidian.py -o "C:\Obsidian\Vault\Journal" --update

# Preview without making changes
python dayone_to_obsidian.py --dry-run --verbose
```

---

## Logging & Reporting

### Console Output
- Summary statistics at completion:
  - Total entries processed
  - New files created
  - Files updated (in update mode)
  - Files skipped (duplicates)
  - Errors encountered

### Log File
- **Location:** `conversion_log.txt` in output directory
- **Format:** Append new log entry each time script runs
- **Entry format:**
  ```
  ================================================================================
  Run: 2025-11-28 14:30:45
  Input: DayOne Export.json
  Output: ./output
  Mode: update
  --------------------------------------------------------------------------------
  Total entries processed: 150
  New files created: 25
  Files updated: 3
  Files skipped: 120
  Errors: 2
  ================================================================================
  ```

### Verbose Mode
- Log each entry as it's processed
- Show filename being created/skipped/updated
- Report any missing photos or conversion issues

---

## Error Handling

### Graceful Handling
- Missing `text` field: Skip entry, log warning
- Missing photo file: Convert link anyway, log warning
- Invalid characters in title: Sanitize and continue
- Empty entry (no text content): Use "Untitled" as title snippet

### Fatal Errors
- JSON file not found: Exit with error message
- JSON parse error: Exit with error message
- Output directory not writable: Exit with error message

---

## Dependencies

### Python Standard Library Only
- `json` - Parse DayOne export
- `os` / `pathlib` - File operations
- `shutil` - Copy photos
- `re` - Regex for text processing
- `argparse` - Command line parsing
- `datetime` - Date handling and timezone conversion

No external packages required.

### Timezone Implementation
- Uses custom DST-aware timezone conversion (no external timezone libraries required)
- Built-in timezone offset mappings for major US timezones
- Automatic DST detection based on date ranges (second Sunday of March to first Sunday of November)

---

## Encoding

- **All file operations use UTF-8 encoding**
- Required to properly handle:
  - Emoji characters (🍿, 🫠, etc.)
  - International characters in location names
  - Special punctuation and symbols
- JSON input: Read with `encoding='utf-8'`
- Markdown output: Write with `encoding='utf-8'`
- Log file: Append with `encoding='utf-8'`

---

## Future Considerations (Out of Scope)

These features are not included in initial implementation but could be added:
- [ ] Audio file handling
- [ ] PDF attachment handling
- [ ] Video file handling
- [ ] Batch processing multiple journal exports
- [ ] Obsidian Daily Notes format compatibility
- [ ] Custom frontmatter field selection via config file
