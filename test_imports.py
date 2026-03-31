"""Test all hare module imports."""
import os
import sys
import importlib

hare_dir = "hare"
total_files = 0
total_lines = 0
errors = []

for root, dirs, files in os.walk(hare_dir):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if not f.endswith(".py"):
            continue
        total_files += 1
        fpath = os.path.join(root, f)
        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
            total_lines += sum(1 for _ in fh)
        
        mod_path = fpath.replace(os.sep, ".").replace("/", ".")[:-3]
        try:
            importlib.import_module(mod_path)
        except Exception as e:
            errors.append((mod_path, str(e)[:150]))

print(f"Total Python files: {total_files}")
print(f"Total lines of code: {total_lines}")
print(f"Import errors: {len(errors)}")
if errors:
    for mod, err in errors[:30]:
        print(f"  ERROR: {mod}: {err}")
else:
    print("All modules imported successfully!")
