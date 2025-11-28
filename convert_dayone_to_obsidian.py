#!/usr/bin/env python3
"""
DayOne to Obsidian Markdown Converter

Converts DayOne journal exports (JSON format) into individual Markdown files
optimized for use in Obsidian.
"""

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Timezone offset mappings (hours from UTC)
# Using DST-aware logic based on date
TIMEZONE_OFFSETS_STD = {
    'America/Chicago': -6,      # Central Standard Time (CST)
    'America/New_York': -5,     # Eastern Standard Time (EST)
    'America/Denver': -7,       # Mountain Standard Time (MST)
    'America/Los_Angeles': -8,  # Pacific Standard Time (PST)
    'America/Phoenix': -7,      # Arizona (no DST)
    'UTC': 0,
}

TIMEZONE_OFFSETS_DST = {
    'America/Chicago': -5,      # Central Daylight Time (CDT)
    'America/New_York': -4,     # Eastern Daylight Time (EDT)
    'America/Denver': -6,       # Mountain Daylight Time (MDT)
    'America/Los_Angeles': -7,  # Pacific Daylight Time (PDT)
    'America/Phoenix': -7,      # Arizona (no DST)
    'UTC': 0,
}


def is_dst(dt):
    """Check if a date falls within US Daylight Saving Time (approximate)."""
    # DST in the US: Second Sunday of March to First Sunday of November
    year = dt.year
    
    # Find second Sunday of March
    march_first = datetime(year, 3, 1, tzinfo=timezone.utc)
    days_until_sunday = (6 - march_first.weekday()) % 7
    dst_start = march_first + timedelta(days=days_until_sunday + 7)  # Second Sunday
    
    # Find first Sunday of November
    nov_first = datetime(year, 11, 1, tzinfo=timezone.utc)
    days_until_sunday = (6 - nov_first.weekday()) % 7
    dst_end = nov_first + timedelta(days=days_until_sunday)  # First Sunday
    
    return dst_start <= dt.replace(tzinfo=timezone.utc) < dst_end


def get_timezone_offset(timezone_str, dt):
    """Get the UTC offset for a timezone at a given datetime."""
    if is_dst(dt):
        return TIMEZONE_OFFSETS_DST.get(timezone_str, -6)  # Default to CDT
    else:
        return TIMEZONE_OFFSETS_STD.get(timezone_str, -6)  # Default to CST


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert DayOne journal exports to Obsidian-compatible Markdown files."
    )
    parser.add_argument(
        "-i", "--input",
        default="DayOne Export.json",
        help="Path to JSON file (default: \"DayOne Export.json\")"
    )
    parser.add_argument(
        "-o", "--output",
        default="./output",
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="Enable update mode (overwrite if modified)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )
    return parser.parse_args()


def sanitize_filename(text, max_length=50):
    """
    Sanitize text for use in a filename.
    
    - Remove/replace special characters: < > : " / \ | ? *
    - Trim whitespace
    - Truncate at word boundary if over max_length
    """
    if not text:
        return "Untitled"
    
    # Remove special characters not allowed in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '', text)
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    if not sanitized:
        return "Untitled"
    
    # Truncate at word boundary if too long
    if len(sanitized) > max_length:
        truncated = sanitized[:max_length]
        # Find last space to break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 20:  # Only break at word if we keep reasonable length
            truncated = truncated[:last_space]
        sanitized = truncated.strip()
    
    return sanitized if sanitized else "Untitled"


def extract_title(text):
    """
    Extract title from entry text.
    
    1. Prefer header line: If content starts with # Header Text, use the header text
    2. Strip Markdown: Remove leading # symbols and trim whitespace
    3. Fallback: If no header, use first ~50 characters of body text
    4. Skip lines that are only images
    """
    if not text:
        return "Untitled"
    
    lines = text.strip().split('\n')
    
    # Check if first line is a header
    first_line = lines[0].strip() if lines else ""
    
    if first_line.startswith('#'):
        # Extract header text, removing leading # symbols
        title = re.sub(r'^#+\s*', '', first_line)
        # Skip if title is just an image reference
        if not re.match(r'^!\[.*\]\(.*\)$', title.strip()):
            return sanitize_filename(title)
    
    # Fallback: use first non-empty, non-image line
    for line in lines:
        line = line.strip()
        # Skip empty lines and lines that are just image references
        if line and not re.match(r'^!\[.*\]\(.*\)$', line):
            # Also skip lines that start with malformed image syntax
            if not line.startswith('!['):
                return sanitize_filename(line)
    
    return "Untitled"


def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return round(celsius * 9/5 + 32)


def format_weather(weather_data):
    """Format weather data into a readable string."""
    if not weather_data:
        return None
    
    parts = []
    
    if 'conditionsDescription' in weather_data:
        parts.append(weather_data['conditionsDescription'])
    
    if 'temperatureCelsius' in weather_data:
        temp_f = celsius_to_fahrenheit(weather_data['temperatureCelsius'])
        parts.append(f"{temp_f}°F")
    
    return ', '.join(parts) if parts else None


def normalize_extension(ext):
    """Normalize image extension (jpg -> jpeg for consistency)."""
    ext = ext.lower() if ext else 'jpeg'
    # Normalize jpg to jpeg for consistency
    if ext == 'jpg':
        return 'jpeg'
    return ext


def convert_image_links(text, photos_info):
    """
    Convert DayOne image syntax to Obsidian wiki-link syntax.
    
    From: ![](dayone-moment://IDENTIFIER)
    To: ![[photos/IDENTIFIER.jpeg]]
    """
    if not text:
        return text
    
    # Build a map of identifier to file extension
    ext_map = {}
    if photos_info:
        for photo in photos_info:
            identifier = photo.get('identifier', '')
            # Determine extension from type field or default to jpeg
            photo_type = normalize_extension(photo.get('type', 'jpeg'))
            ext_map[identifier] = photo_type
    
    def replace_image(match):
        identifier = match.group(1)
        if not identifier:
            # Empty identifier - remove the broken link
            return ''
        ext = ext_map.get(identifier, 'jpeg')
        return f"![[photos/{identifier}.{ext}]]"
    
    # Match dayone-moment:// links (case-insensitive for hex identifier)
    # Also handle empty identifiers: ![](dayone-moment://)
    pattern = r'!\[.*?\]\(dayone-moment://([A-Fa-f0-9]*)\)'
    return re.sub(pattern, replace_image, text)


def build_frontmatter(entry):
    """Build YAML frontmatter from entry data."""
    fm = {}
    
    # UUID
    if 'uuid' in entry:
        fm['uuid'] = entry['uuid']
    
    # Dates - convert to local timezone
    timezone_str = entry.get('timeZone', 'America/Chicago')
    
    if 'creationDate' in entry:
        dt = convert_to_local_time(entry['creationDate'], timezone_str)
        if dt:
            fm['date'] = format_local_datetime(dt)
    
    if 'modifiedDate' in entry:
        dt = convert_to_local_time(entry['modifiedDate'], timezone_str)
        if dt:
            fm['modified'] = format_local_datetime(dt)
    
    # Location
    location = entry.get('location', {})
    if location.get('address'):
        fm['location'] = location['address']
    if location.get('latitude') is not None and location.get('longitude') is not None:
        fm['coordinates'] = [location['latitude'], location['longitude']]
    
    # Weather
    weather_str = format_weather(entry.get('weather'))
    if weather_str:
        fm['weather'] = weather_str
    
    # Tags (only if non-empty)
    tags = entry.get('tags', [])
    if tags:
        fm['tags'] = tags
    
    # Flags
    if entry.get('starred'):
        fm['starred'] = True
    if entry.get('isPinned'):
        fm['pinned'] = True
    
    # Device info
    if 'creationDevice' in entry:
        fm['device'] = entry['creationDevice']
    if 'timeZone' in entry:
        fm['timezone'] = entry['timeZone']
    
    return fm


def frontmatter_to_yaml(fm):
    """Convert frontmatter dict to YAML string."""
    lines = ['---']
    
    for key, value in fm.items():
        if isinstance(value, list):
            if key == 'coordinates':
                # Format as YAML list with quoted strings for Obsidian Maps plugin
                lines.append(f"{key}:")
                lines.append(f'  - "{value[0]}"')
                lines.append(f'  - "{value[1]}"')
            else:
                # Format as YAML list (for tags)
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, str):
            # Quote strings that contain special characters
            if any(c in value for c in [':', '#', '"', "'", '\n', '[', ']', '{', '}']):
                # Escape quotes and wrap in quotes
                escaped = value.replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    
    lines.append('---')
    return '\n'.join(lines)


def convert_to_local_time(iso_date_str, timezone_str):
    """Convert UTC ISO date string to local timezone."""
    if not iso_date_str:
        return None
    try:
        # Parse the UTC date
        dt = datetime.fromisoformat(iso_date_str.replace('Z', '+00:00'))
        # Get the appropriate offset based on DST
        offset_hours = get_timezone_offset(timezone_str, dt)
        # Apply the offset
        local_dt = dt + timedelta(hours=offset_hours)
        # Return as naive datetime (no timezone info) for cleaner output
        return local_dt.replace(tzinfo=None)
    except Exception:
        return None


def format_local_datetime(dt):
    """Format datetime as ISO string without timezone suffix for frontmatter."""
    if not dt:
        return None
    # Format as ISO but without the timezone offset for cleaner frontmatter
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


def generate_filename(entry):
    """Generate filename for an entry."""
    # Extract date and convert to local timezone
    creation_date = entry.get('creationDate', '')
    timezone_str = entry.get('timeZone', 'America/Chicago')
    
    dt = convert_to_local_time(creation_date, timezone_str)
    if dt:
        date_str = dt.strftime('%Y-%m-%d')
    else:
        date_str = 'Unknown-Date'
    
    # Extract title
    text = entry.get('text', '')
    title = extract_title(text)
    
    # Get UUID prefix (first 8 characters)
    uuid = entry.get('uuid', 'UNKNOWN')
    uuid8 = uuid[:8]
    
    return f"{date_str} {title} ({uuid8}).md"


def find_existing_file(output_dir, uuid8):
    """Find existing file with matching UUID8."""
    entries_dir = Path(output_dir) / 'journal-entries'
    if not entries_dir.exists():
        return None
    
    pattern = f"*({uuid8}).md"
    matches = list(entries_dir.glob(pattern))
    return matches[0] if matches else None


def extract_modified_date_from_file(filepath):
    """Extract modified date from existing file's frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for modified: in frontmatter
        match = re.search(r'^modified:\s*(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"')
    except Exception:
        pass
    return None


def copy_photos(entry, source_photos_dir, output_photos_dir, dry_run=False, verbose=False):
    """Copy photos for an entry to output directory."""
    photos = entry.get('photos', [])
    if not photos:
        return
    
    source_path = Path(source_photos_dir)
    output_path = Path(output_photos_dir)
    
    for photo in photos:
        identifier = photo.get('identifier', '')
        md5 = photo.get('md5', '')
        photo_type_raw = photo.get('type', 'jpeg').lower()
        photo_type = normalize_extension(photo_type_raw)
        
        # Try to find source file (could be named by md5 or identifier)
        # Source files use original extension (jpg), destination uses normalized (jpeg)
        source_file = None
        for name_pattern in [f"{md5}.{photo_type_raw}", f"{md5}.{photo_type}",
                             f"{identifier}.{photo_type_raw}", f"{identifier}.{photo_type}", 
                             f"{md5}.jpeg", f"{identifier}.jpeg",
                             f"{md5}.jpg", f"{identifier}.jpg"]:
            potential = source_path / name_pattern
            if potential.exists():
                source_file = potential
                break
        
        if source_file is None:
            # Try to find by md5 with any extension
            for ext in ['jpg', 'jpeg', 'png', 'gif', 'heic']:
                potential = source_path / f"{md5}.{ext}"
                if potential.exists():
                    source_file = potential
                    break
        
        if source_file is None:
            if verbose:
                print(f"  Warning: Photo not found for identifier {identifier}")
            continue
        
        # Destination uses identifier as filename with normalized extension
        dest_file = output_path / f"{identifier}.{photo_type}"
        
        if not dest_file.exists():
            if dry_run:
                if verbose:
                    print(f"  Would copy: {source_file.name} -> {dest_file.name}")
            else:
                shutil.copy2(source_file, dest_file)
                if verbose:
                    print(f"  Copied: {source_file.name} -> {dest_file.name}")


def write_log(output_dir, stats, input_file, update_mode):
    """Write conversion log to file."""
    log_path = Path(output_dir) / 'conversion_log.txt'
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mode = 'update' if update_mode else 'skip'
    
    log_entry = f"""================================================================================
Run: {timestamp}
Input: {input_file}
Output: {output_dir}
Mode: {mode}
--------------------------------------------------------------------------------
Total entries processed: {stats['total']}
New files created: {stats['created']}
Files updated: {stats['updated']}
Files skipped: {stats['skipped']}
Errors: {stats['errors']}
================================================================================

"""
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def process_entries(args):
    """Main processing function."""
    # Load JSON
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON: {e}")
        return 1
    
    entries = data.get('entries', [])
    if not entries:
        print("No entries found in JSON file.")
        return 0
    
    # Setup directories
    output_dir = Path(args.output)
    entries_dir = output_dir / 'journal-entries'
    photos_dir = entries_dir / 'photos'
    source_photos_dir = input_path.parent / 'photos'
    
    if not args.dry_run:
        entries_dir.mkdir(parents=True, exist_ok=True)
        photos_dir.mkdir(parents=True, exist_ok=True)
    
    # Stats tracking
    stats = {
        'total': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for entry in entries:
        stats['total'] += 1
        
        try:
            # Skip entries without text
            if not entry.get('text'):
                if args.verbose:
                    print(f"Skipping entry {entry.get('uuid', 'unknown')}: no text content")
                stats['skipped'] += 1
                continue
            
            uuid = entry.get('uuid', '')
            uuid8 = uuid[:8]
            
            # Generate filename
            filename = generate_filename(entry)
            filepath = entries_dir / filename
            
            # Check for existing file
            existing_file = find_existing_file(args.output, uuid8)
            
            if existing_file:
                if args.update:
                    # Compare modified dates
                    existing_modified = extract_modified_date_from_file(existing_file)
                    entry_modified = entry.get('modifiedDate', '')
                    
                    if existing_modified and entry_modified <= existing_modified:
                        if args.verbose:
                            print(f"Skipping (not modified): {filename}")
                        stats['skipped'] += 1
                        continue
                    
                    # Delete old file if filename changed
                    if existing_file != filepath:
                        if not args.dry_run:
                            existing_file.unlink()
                    
                    if args.verbose:
                        print(f"Updating: {filename}")
                    stats['updated'] += 1
                else:
                    if args.verbose:
                        print(f"Skipping (exists): {filename}")
                    stats['skipped'] += 1
                    continue
            else:
                if args.verbose:
                    print(f"Creating: {filename}")
                stats['created'] += 1
            
            # Build frontmatter
            frontmatter = build_frontmatter(entry)
            yaml_fm = frontmatter_to_yaml(frontmatter)
            
            # Process content
            text = entry.get('text', '')
            photos_info = entry.get('photos', [])
            content = convert_image_links(text, photos_info)
            
            # Combine frontmatter and content
            full_content = f"{yaml_fm}\n\n{content}"
            
            if not args.dry_run:
                # Write markdown file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                # Copy photos
                copy_photos(entry, source_photos_dir, photos_dir, 
                           dry_run=args.dry_run, verbose=args.verbose)
            else:
                if args.verbose:
                    print(f"  Would write: {filepath}")
                    copy_photos(entry, source_photos_dir, photos_dir, 
                               dry_run=True, verbose=args.verbose)
        
        except Exception as e:
            print(f"Error processing entry {entry.get('uuid', 'unknown')}: {e}")
            stats['errors'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("Conversion Complete")
    print("=" * 60)
    print(f"Total entries processed: {stats['total']}")
    print(f"New files created:       {stats['created']}")
    print(f"Files updated:           {stats['updated']}")
    print(f"Files skipped:           {stats['skipped']}")
    print(f"Errors:                  {stats['errors']}")
    print("=" * 60)
    
    # Write log file
    if not args.dry_run:
        write_log(args.output, stats, args.input, args.update)
        print(f"\nLog written to: {output_dir / 'conversion_log.txt'}")
    
    return 0 if stats['errors'] == 0 else 1


def main():
    args = parse_args()
    
    if args.dry_run:
        print("=== DRY RUN MODE - No changes will be made ===\n")
    
    return process_entries(args)


if __name__ == '__main__':
    exit(main())
