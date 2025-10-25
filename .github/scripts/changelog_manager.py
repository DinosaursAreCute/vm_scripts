#!/usr/bin/env python3
"""
Changelog Management Script

This script helps manage the changelog by:
1. Adding new entries to the unreleased section
2. Creating new releases
3. Validating changelog format

Usage:
    python changelog_manager.py add "Added new feature for VM management"
    python changelog_manager.py release 1.0.0
    python changelog_manager.py validate
"""

import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

CHANGELOG_FILE = Path("Changelog.md")

CATEGORIES = {
    'added': 'Added',
    'changed': 'Changed', 
    'deprecated': 'Deprecated',
    'removed': 'Removed',
    'fixed': 'Fixed',
    'security': 'Security'
}

def read_changelog():
    """Read the changelog file"""
    if not CHANGELOG_FILE.exists():
        print(f"Error: {CHANGELOG_FILE} not found")
        sys.exit(1)
    
    return CHANGELOG_FILE.read_text(encoding='utf-8')

def write_changelog(content):
    """Write content to changelog file"""
    CHANGELOG_FILE.write_text(content, encoding='utf-8')

def add_entry(category, message):
    """Add a new entry to the unreleased section"""
    if category.lower() not in CATEGORIES:
        print(f"Error: Invalid category '{category}'. Valid categories: {', '.join(CATEGORIES.keys())}")
        sys.exit(1)
    
    content = read_changelog()
    category_name = CATEGORIES[category.lower()]
    
    # Find the unreleased section and the specific category
    pattern = rf'(## \[Unreleased\].*?### {category_name}\n\n)(.*?)(\n### |\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print(f"Error: Could not find unreleased section or {category_name} category")
        sys.exit(1)
    
    prefix, existing_entries, suffix = match.groups()
    
    # Add the new entry
    new_entry = f"- {message}\n"
    
    if existing_entries.strip():
        updated_entries = existing_entries.rstrip() + '\n' + new_entry
    else:
        updated_entries = new_entry
    
    # Replace the content
    new_content = content[:match.start()] + prefix + updated_entries + suffix + content[match.end():]
    
    write_changelog(new_content)
    print(f"Added entry to {category_name}: {message}")

def create_release(version):
    """Create a new release by moving unreleased items to a versioned section"""
    content = read_changelog()
    
    # Check if version already exists
    if f"## [{version}]" in content:
        print(f"Error: Version {version} already exists in changelog")
        sys.exit(1)
    
    # Get current date
    release_date = datetime.now().strftime("%Y-%m-%d")
    
    # Find unreleased section
    unreleased_pattern = r'(## \[Unreleased\]\n\n)(.*?)(\n## \[|\Z)'
    match = re.search(unreleased_pattern, content, re.DOTALL)
    
    if not match:
        print("Error: Could not find unreleased section")
        sys.exit(1)
    
    prefix, unreleased_content, suffix = match.groups()
    
    # Check if there are any entries to release
    has_entries = any(line.strip().startswith('- ') for line in unreleased_content.split('\n'))
    
    if not has_entries:
        print("Warning: No entries found in unreleased section")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Create new release section
    release_section = f"## [{version}] - {release_date}\n\n{unreleased_content}"
    
    # Create new empty unreleased section
    new_unreleased = """## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

"""
    
    # Build new content
    new_content = content.replace(match.group(0), new_unreleased + release_section + suffix)
    
    write_changelog(new_content)
    print(f"Created release {version} dated {release_date}")

def validate_changelog():
    """Validate changelog format"""
    content = read_changelog()
    errors = []
    
    # Check for required sections
    if "## [Unreleased]" not in content:
        errors.append("Missing [Unreleased] section")
    
    # Check for required categories in unreleased section
    for category in CATEGORIES.values():
        if f"### {category}" not in content:
            errors.append(f"Missing {category} category in unreleased section")
    
    # Check for proper markdown formatting
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        # Check for proper heading format
        if line.startswith('#'):
            if not re.match(r'^#{1,6} ', line):
                errors.append(f"Line {i}: Invalid heading format")
    
    if errors:
        print("Changelog validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Changelog validation passed!")

def main():
    parser = argparse.ArgumentParser(description="Manage changelog entries")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add entry command
    add_parser = subparsers.add_parser('add', help='Add new entry to unreleased section')
    add_parser.add_argument('category', choices=list(CATEGORIES.keys()), 
                           help='Category for the entry')
    add_parser.add_argument('message', help='Entry message')
    
    # Release command
    release_parser = subparsers.add_parser('release', help='Create new release')
    release_parser.add_argument('version', help='Version number (e.g., 1.0.0)')
    
    # Validate command
    subparsers.add_parser('validate', help='Validate changelog format')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_entry(args.category, args.message)
    elif args.command == 'release':
        create_release(args.version)
    elif args.command == 'validate':
        validate_changelog()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()