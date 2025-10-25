# VM_Runner
VM_Runner is a simple python script that allows you to easily run your virtual box virtual machines from and open an ssh connection to them.
Thats pretty much it but for those that know the pain of opening virtual box and starting a vm and then opening a terminal and typing ssh user@ip_address
this is a nice little time saver.

## Requirements
- Python 3.x
- VirtualBox installed
- Guest Additions installed on the VMs
- SSH server running on the VMs

## Changelog Automation

This repository uses automated changelog generation based on commit messages. The system works as follows:

### How it works
1. **Commit Message Analysis**: The GitHub Action analyzes commit messages and categorizes them
2. **Automatic Updates**: When commits are pushed to main, the changelog is automatically updated
3. **Conventional Commits**: Supports conventional commit format for better categorization

### Commit Message Categories
- `feat:` or keywords like "add", "new", "create" → **Added** section
- `fix:` or keywords like "fix", "bug", "issue" → **Fixed** section  
- `docs:`, `style:`, `refactor:` → **Changed** section
- Keywords like "remove", "delete" → **Removed** section
- Keywords like "deprecate" → **Deprecated** section
- Keywords like "security", "vulnerability" → **Security** section

### Manual Changelog Management
Use the `changelog_manager.py` script located in `.github/scripts/` for manual entries:

```bash
# Add a new entry
python .github/scripts/changelog_manager.py add added "New feature for VM status checking"

# Create a release
python .github/scripts/changelog_manager.py release 1.0.0

# Validate changelog format
python .github/scripts/changelog_manager.py validate
```

## DINOSAURS ARE CUTE
