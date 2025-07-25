#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime

def get_git_logs(n=None):
    """Get the last n git commit logs with full messages, or all if n is None"""
    try:
        # Get git log with full commit messages using a delimiter
        if n is None:
            cmd = ['git', 'log', '--pretty=format:===COMMIT_START===%n%H%n%an%n%ad%n%s%n%b===COMMIT_END===', '--date=iso']
        else:
            cmd = ['git', 'log', f'-{n}', '--pretty=format:===COMMIT_START===%n%H%n%an%n%ad%n%s%n%b===COMMIT_END===', '--date=iso']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git logs: {e}")
        sys.exit(1)

def parse_commits(log_output):
    """Parse git log output into structured commits"""
    commits = []
    commit_blocks = log_output.split('===COMMIT_START===')
    
    for block in commit_blocks:
        if '===COMMIT_END===' in block:
            content = block.replace('===COMMIT_END===', '').strip()
            if content:
                lines = content.split('\n', 4)
                if len(lines) >= 4:
                    commit = {
                        'hash': lines[0].strip(),
                        'author': lines[1].strip(),
                        'date': lines[2].strip(),
                        'subject': lines[3].strip(),
                        'body': lines[4].strip() if len(lines) > 4 else ''
                    }
                    commits.append(commit)
    
    return commits

def generate_markdown(commits, n=None):
    """Generate markdown content from commits"""
    md_content = f"# Git Log\n\n"
    md_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    if n is None:
        md_content += f"## Complete Git History ({len(commits)} Commits)\n\n"
    else:
        md_content += f"## Last {len(commits)} Commits\n\n"
    
    for i, commit in enumerate(commits, 1):
        md_content += f"### {i}. Commit: {commit['hash'][:8]}\n\n"
        md_content += f"- **Author:** {commit['author']}\n"
        md_content += f"- **Date:** {commit['date']}\n"
        md_content += f"- **Subject:** {commit['subject']}\n\n"
        
        md_content += f"**Full Commit Message:**\n```\n{commit['subject']}\n"
        if commit['body'].strip():
            md_content += f"\n{commit['body'].strip()}\n"
        md_content += "```\n\n"
        
        md_content += "---\n\n"
    
    return md_content

def main():
    # Get number of commits from command line argument
    n = None
    if len(sys.argv) == 2:
        try:
            n = int(sys.argv[1])
            if n <= 0:
                raise ValueError("Number must be positive")
        except ValueError:
            print("Error: Please provide a valid positive number")
            sys.exit(1)
    elif len(sys.argv) > 2:
        print("Usage: python3 makeLogs.py [number_of_commits]")
        print("       If no number is provided, generates entire git history")
        sys.exit(1)
    
    # Get git logs
    log_output = get_git_logs(n)
    
    # Parse commits
    commits = parse_commits(log_output)
    
    # Generate markdown
    md_content = generate_markdown(commits, n)
    
    # Write to file
    with open('git_log.md', 'w') as f:
        f.write(md_content)
    
    if n is None:
        print(f"Successfully generated git_log.md with complete history ({len(commits)} commits)")
    else:
        print(f"Successfully generated git_log.md with {len(commits)} commits")

if __name__ == "__main__":
    main()