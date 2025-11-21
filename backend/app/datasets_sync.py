import subprocess
from pathlib import Path
from typing import Dict, Any

def sync_repo(target_dir: Path) -> Dict[str, Any]:
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = target_dir / "dataset"
    url = "https://github.com/linhandev/dataset.git"
    if repo_dir.exists() and (repo_dir / ".git").exists():
        subprocess.run(["git", "-C", str(repo_dir), "pull"], check=False)
    else:
        subprocess.run(["git", "clone", url, str(repo_dir)], check=False)
    cats = []
    for p in repo_dir.iterdir():
        if p.is_dir():
            cats.append(p.name)
    return {"path": str(repo_dir), "categories": cats}