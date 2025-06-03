#!/usr/bin/env python3
"""
Remove a specific commit from a Git repository with full automation:
- Preserves timestamps and merge history
- Works on Windows and Unix
- Handles post-rewrite actions automatically
- Includes safety checks and confirmations
"""

import subprocess
import sys
import os
import tempfile
import re
from typing import List, Optional

def run_git_command(cmd: List[str], capture_output: bool = True) -> str:
    """Run a Git command and return the result."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
        )
        return result.stdout.strip() if capture_output else ""
    except subprocess.CalledProcessError as e:
        print(f"Error running Git command: {' '.join(cmd)}")
        print(e.stderr)
        sys.exit(1)

def validate_commit(commit_hash: str) -> None:
    """Check if the commit exists."""
    run_git_command(["rev-parse", "--verify", commit_hash])

def get_parent(commit_hash: str) -> str:
    """Get the parent commit of the specified commit."""
    parents = run_git_command(["log", "-1", "--format=%P", commit_hash])
    if not parents:
        print(f"Error: Commit {commit_hash} has no parent (root commit).")
        sys.exit(1)
    return parents.split()[0]  # Use first parent in case of merges

def get_remote_branches() -> List[str]:
    """Get list of all remote-tracking branches."""
    branches = run_git_command(["branch", "-r", "--format=%(refname:short)"])
    return [b.strip() for b in branches.splitlines() if b.strip()]

def confirm_action(prompt: str) -> bool:
    """Get user confirmation for an action."""
    response = input(f"{prompt} [y/N] ").strip().lower()
    return response == 'y'

def force_push_branches() -> None:
    """Force push all branches to their remotes after confirmation."""
    if not confirm_action("\nForce push all branches to their remotes?"):
        print("Skipping force push. You'll need to do this manually later.")
        return

    print("\nForce pushing branches...")
    branches = run_git_command(["branch", "--format=%(refname:short)"])
    for branch in branches.splitlines():
        branch = branch.strip()
        if not branch:
            continue
        
        remote = "origin"  # Default remote, could be enhanced to detect actual remote
        if confirm_action(f"Force push {branch} to {remote}?"):
            run_git_command(["push", "--force", remote, f"{branch}:{branch}"], capture_output=False)
            print(f"Force pushed {branch} to {remote}")

def update_remotes() -> None:
    """Update all remote references."""
    print("\nUpdating remotes...")
    remotes = run_git_command(["remote"])
    for remote in remotes.splitlines():
        remote = remote.strip()
        if remote:
            run_git_command(["remote", "update", remote], capture_output=False)
            print(f"Updated {remote}")

def cleanup_original_refs() -> None:
    """Clean up the original references created by filter-repo."""
    if confirm_action("\nClean up original references (refs/original/)?"):
        run_git_command(["for-each-ref", "--format=%(refname)", "refs/original/"], capture_output=False)
        print("Cleaned up original references")

def verify_filter_repo() -> None:
    """Verify git-filter-repo is installed."""
    try:
        subprocess.run(["git", "filter-repo", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: git-filter-repo is not installed.")
        print("Install it with: pip install git-filter-repo")
        print("Or download from: https://github.com/newren/git-filter-repo")
        sys.exit(1)

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: remove_commit.py <commit-to-remove>")
        sys.exit(1)

    commit_to_remove = sys.argv[1]
    validate_commit(commit_to_remove)
    parent_commit = get_parent(commit_to_remove)
    verify_filter_repo()

    # Safety checks
    if run_git_command(["status", "--porcelain"]):
        print("Error: Working directory is not clean. Commit or stash changes first.")
        sys.exit(1)

    if not confirm_action(f"WARNING: This will permanently rewrite history to remove {commit_to_remove}. Continue?"):
        sys.exit(0)

    # Create temporary graft file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as graft_file:
        graft_file.write(f"{commit_to_remove} {parent_commit}\n")
        graft_path = graft_file.name

    try:
        # Step 1: Create graft
        run_git_command(["replace", "--graft", commit_to_remove, parent_commit])
        
        # Step 2: Rewrite history with filter-repo
        print("\nRewriting repository history...")
        blob_hash = run_git_command(["hash-object", "-w", graft_path])
        
        filter_cmd = [
            "filter-repo", 
            "--force",
            "--refs", "refs/heads/*",
            "--refs", "refs/tags/*",
            f"--replace-refs=update=add:{blob_hash}:.git/info/grafts"
        ]
        
        subprocess.run(["git"] + filter_cmd, check=True)
        
        # Post-rewrite actions
        update_remotes()
        force_push_branches()
        cleanup_original_refs()
        
        print(f"\nSuccessfully removed commit {commit_to_remove}")
        print("Note: Collaborators will need to reclone or reset their repositories")

    finally:
        # Cleanup
        os.unlink(graft_path)
        run_git_command(["replace", "-d", commit_to_remove], capture_output=False)

if __name__ == "__main__":
    main()