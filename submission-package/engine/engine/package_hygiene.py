"""Clean up .bak files and verify hygiene of submission-package."""
import os
import re
from pathlib import Path

sub = Path("submission-package")
print("1. Scanning for .bak files in submission-package...")
bak_files = list(sub.rglob("*.bak"))
print(f"Found {len(bak_files)} .bak files.")
for b in bak_files:
    print(f"  Removing {b}")
    b.unlink()

print("\n2. Scanning for __pycache__ or .pytest_cache in submission-package...")
caches = [p for p in sub.rglob("*") if p.is_dir() and p.name in ("__pycache__", ".pytest_cache")]
print(f"Found {len(caches)} cache directories.")
for c in caches:
    import shutil
    print(f"  Removing {c}")
    shutil.rmtree(c)

print("\n3. Scanning for secrets / .env in submission-package...")
secret_patterns = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),
    re.compile(r"OPENROUTER_API_KEY\s*=\s*['\"][^'\"]+['\"]"),
]
secrets = []
for p in sub.rglob("*"):
    if p.is_file():
        if p.name == ".env":
            secrets.append(f"ENV FILE: {p}")
        elif p.suffix in (".py", ".json", ".yaml", ".yml", ".md", ".csv", ".txt"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for pat in secret_patterns:
                    if pat.search(content):
                        secrets.append(f"SECRET PATTERN in {p}")
            except Exception:
                pass

if secrets:
    print(f"ALERT: Found {len(secrets)} potential secrets:")
    for s in secrets:
        print(f"  {s}")
else:
    print("Clean: 0 secrets and 0 .env files found in submission-package.")

print("\nHygiene scan complete.")
