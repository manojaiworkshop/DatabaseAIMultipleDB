#!/usr/bin/env python3
"""
Git Secrets Cleaner and Preventer
Automatically removes secrets from Git history and prevents future commits
"""

import os
import sys
import subprocess
import shutil
import re
from pathlib import Path

class GitSecretsCleaner:
    def __init__(self):
        self.repo_root = self.get_repo_root()
        self.sensitive_files = [
            'app_config.yml',
            'config.yml',
            '.env',
            '*.key',
            '*.pem',
            '*.cert'
        ]
        
    def get_repo_root(self):
        """Get the root directory of the Git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            print("❌ Error: Not in a Git repository")
            sys.exit(1)
    
    def run_command(self, cmd, check=True, capture=True):
        """Run a shell command"""
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=check,
                    shell=True
                )
                return result.stdout.strip(), result.returncode
            else:
                result = subprocess.run(cmd, check=check, shell=True)
                return "", result.returncode
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return e.stderr if capture else "", e.returncode
    
    def check_gitignore(self):
        """Ensure sensitive files are in .gitignore"""
        gitignore_path = os.path.join(self.repo_root, '.gitignore')
        
        print("\n📝 Checking .gitignore...")
        
        if not os.path.exists(gitignore_path):
            print("⚠️  .gitignore not found, creating one...")
            with open(gitignore_path, 'w') as f:
                f.write("# Sensitive files\n")
        
        with open(gitignore_path, 'r') as f:
            current_content = f.read()
        
        patterns_to_add = []
        for pattern in self.sensitive_files:
            # Check if pattern exists (uncommented)
            if not re.search(rf'^{re.escape(pattern)}$', current_content, re.MULTILINE):
                if not re.search(rf'^# {re.escape(pattern)}$', current_content, re.MULTILINE):
                    patterns_to_add.append(pattern)
                else:
                    # Uncomment the pattern
                    current_content = re.sub(
                        rf'^# ({re.escape(pattern)})$',
                        r'\1',
                        current_content,
                        flags=re.MULTILINE
                    )
        
        if patterns_to_add:
            print(f"✅ Adding {len(patterns_to_add)} patterns to .gitignore")
            with open(gitignore_path, 'a') as f:
                f.write("\n# Auto-added by git_secrets_cleaner.py\n")
                for pattern in patterns_to_add:
                    f.write(f"{pattern}\n")
        
        # Write updated content if we uncommented anything
        if '# app_config.yml' not in current_content:
            with open(gitignore_path, 'w') as f:
                f.write(current_content)
        
        print("✅ .gitignore updated")
    
    def remove_from_history(self, filename):
        """Remove a file from Git history using git filter-branch"""
        print(f"\n🔄 Removing {filename} from Git history...")
        
        # Check if file exists in history
        output, _ = self.run_command(f'git log --all --full-history -- {filename}')
        
        if not output:
            print(f"✅ {filename} not found in history, skipping...")
            return True
        
        # Stash any changes
        print("📦 Stashing uncommitted changes...")
        self.run_command('git stash', check=False)
        
        # Set environment variable to suppress warning
        os.environ['FILTER_BRANCH_SQUELCH_WARNING'] = '1'
        
        try:
            # Remove file from history
            cmd = f'git filter-branch --force --index-filter "git rm --cached --ignore-unmatch {filename}" --prune-empty --tag-name-filter cat -- --all'
            print(f"🔧 Running: {cmd}")
            _, returncode = self.run_command(cmd, check=False, capture=False)
            
            if returncode != 0:
                print(f"⚠️  Warning: filter-branch returned {returncode}")
                return False
            
            # Clean up backup refs
            backup_refs = os.path.join(self.repo_root, '.git', 'refs', 'original')
            if os.path.exists(backup_refs):
                shutil.rmtree(backup_refs)
                print("🗑️  Removed backup refs")
            
            # Expire reflog and garbage collect
            print("🗑️  Running garbage collection...")
            self.run_command('git reflog expire --expire=now --all', check=False)
            self.run_command('git gc --prune=now --aggressive', check=False)
            
            print(f"✅ Successfully removed {filename} from history")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def clear_sensitive_data_in_file(self, filename):
        """Clear sensitive data in a file (replace with empty string)"""
        filepath = os.path.join(self.repo_root, filename)
        
        if not os.path.exists(filepath):
            return
        
        print(f"\n🔒 Clearing sensitive data in {filename}...")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace API keys with empty strings
            patterns = [
                (r"(api_key\s*:\s*)['\"]?[^\s'\"]+['\"]?", r"\1''"),
                (r"(password\s*:\s*)['\"]?[^\s'\"]+['\"]?", r"\1''"),
                (r"(secret\s*:\s*)['\"]?[^\s'\"]+['\"]?", r"\1''"),
                (r"(key\s*:\s*)['\"]?sk-[^\s'\"]+['\"]?", r"\1''"),
            ]
            
            modified = False
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    content = new_content
                    modified = True
            
            if modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Cleared sensitive data in {filename}")
            else:
                print(f"✅ No sensitive data found in {filename}")
                
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
    
    def create_example_config(self):
        """Create example config file"""
        example_file = os.path.join(self.repo_root, 'app_config.example.yml')
        config_file = os.path.join(self.repo_root, 'app_config.yml')
        
        if os.path.exists(config_file) and not os.path.exists(example_file):
            print("\n📄 Creating app_config.example.yml...")
            shutil.copy(config_file, example_file)
            
            # Clear secrets in example file
            self.clear_sensitive_data_in_file('app_config.example.yml')
            print("✅ Created app_config.example.yml")
    
    def setup_pre_commit_hook(self):
        """Create a pre-commit hook to prevent committing secrets"""
        hooks_dir = os.path.join(self.repo_root, '.git', 'hooks')
        hook_file = os.path.join(hooks_dir, 'pre-commit')
        
        print("\n🪝 Setting up pre-commit hook...")
        
        if not os.path.exists(hooks_dir):
            os.makedirs(hooks_dir)
        
        hook_content = '''#!/bin/sh
# Pre-commit hook to prevent committing secrets
# Auto-generated by git_secrets_cleaner.py

# Files to check
SENSITIVE_FILES="app_config.yml config.yml .env"

# Check if any sensitive files are being committed
for file in $SENSITIVE_FILES; do
    if git diff --cached --name-only | grep -q "^$file$"; then
        echo "❌ Error: Attempting to commit sensitive file: $file"
        echo "   This file should not be committed to Git."
        echo "   Please remove it from staging: git reset HEAD $file"
        exit 1
    fi
done

# Check for API keys in staged files
if git diff --cached | grep -iE "(api_key|secret|password).*['\\\"]sk-[a-zA-Z0-9]{20,}"; then
    echo "❌ Error: Found API key in staged changes!"
    echo "   Please remove the API key before committing."
    exit 1
fi

exit 0
'''
        
        with open(hook_file, 'w') as f:
            f.write(hook_content)
        
        # Make hook executable (Unix-like systems)
        if sys.platform != 'win32':
            os.chmod(hook_file, 0o755)
        
        print("✅ Pre-commit hook installed")
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("=" * 60)
        print("  Git Secrets Cleaner")
        print("=" * 60)
        
        # Step 1: Check and update .gitignore
        self.check_gitignore()
        
        # Step 2: Clear sensitive data in current files
        for filename in ['app_config.yml', 'config.yml']:
            self.clear_sensitive_data_in_file(filename)
        
        # Step 3: Create example config
        self.create_example_config()
        
        # Step 4: Remove files from Git history
        print("\n🔄 Cleaning Git history...")
        print("⚠️  This may take a few minutes...")
        
        files_to_remove = ['app_config.yml', 'config.yml']
        success_count = 0
        
        for filename in files_to_remove:
            if self.remove_from_history(filename):
                success_count += 1
        
        # Step 5: Setup pre-commit hook
        self.setup_pre_commit_hook()
        
        # Step 6: Stage and commit changes
        print("\n📝 Staging changes...")
        self.run_command('git add .gitignore', check=False)
        
        if os.path.exists(os.path.join(self.repo_root, 'app_config.example.yml')):
            self.run_command('git add app_config.example.yml', check=False)
        
        print("\n" + "=" * 60)
        print("  ✅ Cleanup Complete!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   - Updated .gitignore")
        print(f"   - Cleared sensitive data in local files")
        print(f"   - Removed {success_count}/{len(files_to_remove)} files from history")
        print(f"   - Created example config file")
        print(f"   - Installed pre-commit hook")
        
        print("\n⚠️  IMPORTANT NEXT STEPS:")
        print("=" * 60)
        print("1. Commit the .gitignore changes:")
        print("   git commit -m 'chore: Update .gitignore to exclude sensitive files'")
        print("\n2. Force push to update remote (WARNING: This rewrites history!):")
        print("   git push --force-with-lease")
        print("\n3. Revoke any exposed API keys:")
        print("   - OpenAI: https://platform.openai.com/api-keys")
        print("   - Generate new keys after pushing")
        print("\n4. Update your local app_config.yml with new keys")
        print("   (This file is now in .gitignore and won't be committed)")
        print("=" * 60)


def main():
    """Main entry point"""
    cleaner = GitSecretsCleaner()
    
    try:
        cleaner.run_cleanup()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
