#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime

def get_git_logs(n):
    """Get the last n git commit logs with full messages"""
    try:
        # Get git log with full commit messages
        cmd = ['git', 'log', f'-{n}', '--pretty=format:%H|%an|%ad|%s|%b|%n', '--date=iso']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git logs: {e}")
        sys.exit(1)

def parse_commits(log_output):
    """Parse git log output into structured commits"""
    commits = []
    current_commit = {}
    
    for line in log_output.split('\n'):
        if '|' in line:
            parts = line.split('|', 4)
            if len(parts) >= 4:
                current_commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'subject': parts[3],
                    'body': parts[4] if len(parts) > 4 else ''
                }
                commits.append(current_commit)
    
    return commits

def generate_markdown(commits):
    """Generate markdown content from commits"""
    md_content = f"# Git Log\n\n"
    md_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md_content += f"## Last {len(commits)} Commits\n\n"
    
    for i, commit in enumerate(commits, 1):
        md_content += f"### {i}. {commit['subject']}\n\n"
        md_content += f"- **Commit Hash:** `{commit['hash']}`\n"
        md_content += f"- **Author:** {commit['author']}\n"
        md_content += f"- **Date:** {commit['date']}\n\n"
        
        if commit['body'].strip():
            md_content += f"**Full Message:**\n```\n{commit['body'].strip()}\n```\n\n"
        
        md_content += "---\n\n"
    
    return md_content

def main():
    # Get number of commits from command line argument
    if len(sys.argv) != 2:
        print("Usage: python3 makeLogs.py <number_of_commits>")
        sys.exit(1)
    
    try:
        n = int(sys.argv[1])
        if n <= 0:
            raise ValueError("Number must be positive")
    except ValueError:
        print("Error: Please provide a valid positive number")
        sys.exit(1)
    
    # Get git logs
    log_output = get_git_logs(n)
    
    # Parse commits
    commits = parse_commits(log_output)
    
    # Generate markdown
    md_content = generate_markdown(commits)
    
    # Write to file
    with open('git_log.md', 'w') as f:
        f.write(md_content)
    
    print(f"Successfully generated git_log.md with {len(commits)} commits")

if __name__ == "__main__":
    main()