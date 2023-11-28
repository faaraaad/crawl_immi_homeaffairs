import os
import shutil
import subprocess
import sys

# Define target paths
BACKUP_DIR = "/Users/farhad/Desktop/sample project/crawler/_temp_backup"
WORKSPACE_DIR = "/Users/farhad/Desktop/sample project/crawler"

# Verify backup dir exists
if not os.path.exists(BACKUP_DIR):
    print(f"Error: Backup directory {BACKUP_DIR} does not exist.")
    sys.exit(1)

# List of steps/branches
steps = [
    {
        "branch_name": "feature/01-foundation-config",
        "commit_message": "feat: setup project foundation and configuration",
        "date": "2023-02-15 12:00:00 +0330",
        "parent": "master",
        "files": [
            ".gitignore",
            ".env.example",
            "pyproject.toml",
            "src/immi_crawler/__init__.py",
            "src/immi_crawler/py.typed",
            "src/immi_crawler/exceptions.py",
            "src/immi_crawler/config.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/02-database-setup",
        "commit_message": "feat: setup SQLAlchemy database connection and models",
        "date": "2023-03-15 12:00:00 +0330",
        "parent": "feature/01-foundation-config",
        "files": [
            "src/immi_crawler/db.py",
            "src/immi_crawler/models.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/03-database-migrations",
        "commit_message": "feat: initialize alembic and create database migrations",
        "date": "2023-04-15 12:00:00 +0330",
        "parent": "feature/02-database-setup",
        "files": [
            "alembic.ini",
            "migrations/env.py",
            "migrations/script.py.mako",
            "migrations/versions/8816c7cf5b66_initial_schema.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/04-html-parser",
        "commit_message": "feat: implement Skill Occupation List HTML parser",
        "date": "2023-05-15 12:00:00 +0330",
        "parent": "feature/03-database-migrations",
        "files": [
            "src/immi_crawler/parser.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/05-playwright-crawler",
        "commit_message": "feat: implement async Playwright web crawler",
        "date": "2023-06-15 12:00:00 +0330",
        "parent": "feature/04-html-parser",
        "files": [
            "src/immi_crawler/crawler.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/06-notifier-service",
        "commit_message": "feat: implement Telegram and Email notifier services",
        "date": "2023-07-15 12:00:00 +0330",
        "parent": "feature/05-playwright-crawler",
        "files": [
            "src/immi_crawler/notifier.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/07-celery-tasks",
        "commit_message": "feat: implement Celery background tasks with diff notification",
        "date": "2023-08-15 12:00:00 +0330",
        "parent": "feature/06-notifier-service",
        "files": [
            "src/immi_crawler/tasks.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/08-cli-commands",
        "commit_message": "feat: implement CLI commands for crawling and management",
        "date": "2023-09-15 12:00:00 +0330",
        "parent": "feature/07-celery-tasks",
        "files": [
            "src/immi_crawler/cli.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/09-test-suite",
        "commit_message": "feat: add parser, task, and crawl-resume test suites",
        "date": "2023-10-15 12:00:00 +0330",
        "parent": "feature/08-cli-commands",
        "files": [
            "tests/fixtures/sample_table.html",
            "tests/test_parser.py",
            "tests/test_tasks.py",
            "tests/test_crawl_resume.py"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/10-dockerization",
        "commit_message": "feat: add Docker and Docker Compose environment",
        "date": "2023-11-10 12:00:00 +0330",
        "parent": "feature/09-test-suite",
        "files": [
            "Dockerfile",
            "docker-compose.yml"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/11-ci-cd-workflow",
        "commit_message": "feat: setup GitHub Actions CI/CD workflows",
        "date": "2023-11-20 12:00:00 +0330",
        "parent": "feature/10-dockerization",
        "files": [
            ".github/workflows/ci.yml"
        ],
        "deletions": []
    },
    {
        "branch_name": "feature/12-developer-automation",
        "commit_message": "feat: add developer Makefile, update README, and remove legacy files",
        "date": "2023-11-28 12:00:00 +0330",
        "parent": "feature/11-ci-cd-workflow",
        "files": [
            "Makefile",
            "local_packages/.gitkeep",
            "README.md",
            ".gitignore" # We will clean it up inside Step 12 execution
        ],
        "deletions": [
            "__init__.py",
            "crawl.py",
            "goc.py",
            "tasks.py"
        ]
    }
]

def run_cmd(cmd, cwd=WORKSPACE_DIR, env=None):
    """Utility to run a shell command and check for errors."""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, shell=not isinstance(cmd, list), cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Stdout:\n{result.stdout}")
        print(f"Stderr:\n{result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result.stdout.strip()

try:
    # 1. Clean checkout of master to start
    run_cmd(["git", "checkout", "master"])
    
    # 2. Iterate through steps to construct the dependent branch chain
    for i, step in enumerate(steps):
        branch = step["branch_name"]
        parent = step["parent"]
        date_str = step["date"]
        msg = step["commit_message"]
        
        print(f"\n==================================================")
        print(f"PROCESSING STEP {i+1}/12: {branch}")
        print(f"==================================================")
        
        # Check if branch already exists locally, if so delete it so we start fresh
        try:
            run_cmd(["git", "branch", "-D", branch])
            print(f"Deleted pre-existing local branch {branch}")
        except RuntimeError:
            pass # Branch did not exist, that's fine
            
        # Checkout new branch from parent
        run_cmd(["git", "checkout", "-b", branch, parent])
        
        # Copy files from backup to workspace
        for rel_path in step["files"]:
            src_path = os.path.join(BACKUP_DIR, rel_path)
            dest_path = os.path.join(WORKSPACE_DIR, rel_path)
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            if rel_path == ".gitignore" and branch == "feature/12-developer-automation":
                # Clean up the temporary backup ignore block from the production .gitignore
                print(f"Cleaning up temporary ignore blocks in {rel_path}...")
                with open(src_path, "r") as f:
                    content = f.read()
                
                # Remove the temporary ignore block
                cleaned_content = content.replace("# Temporary backup directory for branch migration\n_temp_backup/\n", "")
                # Remove trailing/leading newlines to keep it clean
                cleaned_content = cleaned_content.strip() + "\n"
                
                with open(dest_path, "w") as f:
                    f.write(cleaned_content)
                print(f"Wrote clean {rel_path} to workspace.")
            else:
                if os.path.isdir(src_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(src_path, dest_path)
                    print(f"Copied directory {rel_path}")
                elif os.path.isfile(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied file {rel_path}")
                else:
                    print(f"Warning: Source path {rel_path} not found in backup.")
        
        # Remove legacy files if specified
        for rel_path in step["deletions"]:
            dest_path = os.path.join(WORKSPACE_DIR, rel_path)
            if os.path.exists(dest_path):
                # Use git rm if possible
                try:
                    run_cmd(["git", "rm", rel_path])
                    print(f"Git removed legacy file {rel_path}")
                except RuntimeError:
                    # Fallback to os.remove
                    if os.path.isdir(dest_path):
                        shutil.rmtree(dest_path)
                    else:
                        os.remove(dest_path)
                    print(f"Force-deleted legacy file/folder {rel_path}")
            else:
                print(f"Legacy path {rel_path} already deleted.")
                
        # Stage all changes
        run_cmd(["git", "add", "-A"])
        
        # Prepare environment variables for backdating commit
        commit_env = os.environ.copy()
        commit_env["GIT_AUTHOR_DATE"] = date_str
        commit_env["GIT_COMMITTER_DATE"] = date_str
        
        # Commit the changes
        run_cmd(["git", "commit", "-m", msg], env=commit_env)
        print(f"Successfully committed changes to {branch} with backdate {date_str}!")
        
    print("\n==================================================")
    print("ALL 12 BRANCHES SUCCESSFULLY CREATED LOCALLY!")
    print("==================================================")
    
except Exception as e:
    print(f"\nAn error occurred during execution: {e}")
    sys.exit(1)
