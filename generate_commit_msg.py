#!/usr/bin/env python3
"""
Generate detailed commit messages by analyzing git diff
"""
import subprocess
import sys
from datetime import datetime

def get_git_diff():
    """Get the staged changes"""
    try:
        # Get the diff of staged changes
        result = subprocess.run(['git', 'diff', '--cached'], 
                              capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return ""

def get_changed_files():
    """Get list of changed files"""
    try:
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def analyze_changes(diff_text, files):
    """Analyze the diff to create a meaningful summary"""
    if not diff_text or not files:
        return "No changes detected", []
    
    # Categorize files
    categories = {
        'config': [],
        'source': [],
        'docker': [],
        'docs': [],
        'other': []
    }
    
    for f in files:
        if 'config' in f or f.endswith('.json'):
            categories['config'].append(f)
        elif f.endswith('.py'):
            categories['source'].append(f)
        elif 'docker' in f.lower() or f == 'Dockerfile':
            categories['docker'].append(f)
        elif f.endswith('.md'):
            categories['docs'].append(f)
        else:
            categories['other'].append(f)
    
    # Analyze specific changes
    changes = []
    
    # Look for common patterns in the diff
    if 'requirements.txt' in files:
        changes.append("Updated Python dependencies")
    
    if 'Dockerfile' in files or 'docker-compose.yml' in files:
        if 'CMD [' in diff_text:
            changes.append("Modified Docker container entry point")
        if 'RUN ' in diff_text:
            changes.append("Updated Docker build steps")
        if 'services:' in diff_text:
            changes.append("Modified Docker Compose services")
    
    if categories['config']:
        if 'stt_config.json' in categories['config']:
            changes.append("Updated STT configuration parameters")
        else:
            changes.append(f"Modified configuration files: {', '.join(categories['config'])}")
    
    if categories['source']:
        # Look for specific code patterns
        if '+ class ' in diff_text:
            changes.append("Added new class definitions")
        if '- class ' in diff_text:
            changes.append("Removed class definitions")
        if 'def ' in diff_text and '+' in diff_text:
            changes.append("Added or modified functions")
        if 'import ' in diff_text:
            changes.append("Updated imports")
        if 'logging' in diff_text:
            changes.append("Modified logging configuration")
    
    # Generate title based on most significant change
    if len(files) == 1:
        file = files[0]
        if file == 'Dockerfile':
            title = "Update Docker configuration"
        elif file.endswith('.py'):
            title = f"Update {file.replace('src/', '').replace('.py', '')} module"
        else:
            title = f"Update {file}"
    else:
        if categories['source'] and len(categories['source']) > 2:
            title = "Refactor codebase"
        elif categories['config']:
            title = "Update configuration"
        elif categories['docker']:
            title = "Update Docker setup"
        else:
            title = "Update project files"
    
    return title, changes

def generate_commit_message():
    """Generate a detailed commit message"""
    diff = get_git_diff()
    files = get_changed_files()
    
    if not files:
        print("No changes to commit")
        sys.exit(1)
    
    title, changes = analyze_changes(diff, files)
    
    # Build commit message
    timestamp = datetime.now().strftime("%a %b %d %I:%M:%S %p %Z %Y")
    
    message_parts = [
        f"{title} at {timestamp}",
        ""
    ]
    
    if changes:
        message_parts.append("Summary of changes:")
        for change in changes:
            message_parts.append(f"- {change}")
        message_parts.append("")
    
    message_parts.append("Files modified:")
    for f in files[:10]:  # Limit to 10 files
        message_parts.append(f"- {f}")
    
    if len(files) > 10:
        message_parts.append(f"... and {len(files) - 10} more files")
    
    message_parts.extend([
        "",
        "🤖 Generated with Claude Code",
        "",
        "Co-Authored-By: Claude <noreply@anthropic.com>"
    ])
    
    return '\n'.join(message_parts)

if __name__ == "__main__":
    print(generate_commit_message())