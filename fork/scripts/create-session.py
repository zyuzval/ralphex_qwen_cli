#!/usr/bin/env python3
"""
create-session.py - Создать новую сессию для параллельных исправлений

Использование:
    python scripts/create-session.py --name "analysis-critical" --priority "Critical"
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


def create_session(name: str, priority: str, source: str = ""):
    """Создать структуру папок для сессии."""
    
    # Найти следующий номер сессии
    sessions_dir = Path(__file__).parent.parent / "docs" / "sessions"
    existing = list(sessions_dir.glob("SESSION-*"))
    next_num = len(existing) + 1
    session_id = f"SESSION-{next_num:03d}-{name}"
    
    # Создать папки
    session_dir = sessions_dir / session_id
    iteration_dir = session_dir / "iteration-01"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    
    # Создать session.md
    template_path = sessions_dir / "TEMPLATE.md"
    if template_path.exists():
        session_md = template_path.read_text(encoding="utf-8")
        session_md = session_md.replace("SESSION-XXX-[name]", session_id)
        session_md = session_md.replace("YYYY-MM-DD HH:MM", datetime.now().strftime("%Y-%m-%d %H:%M"))
        session_md = session_md.replace("Critical / High / Medium", priority)
        session_md = session_md.replace("docs/reviews/fixes/XXX-fixes.md", source or f"docs/reviews/fixes/{name}-fixes.md")
        (session_dir / "session.md").write_text(session_md, encoding="utf-8")
    
    # Создать status.json шаблон
    status = {
        "session": session_id,
        "iteration": 1,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "checks": {
            "tests": None,
            "build": None,
            "typescript": None
        },
        "files_modified": [],
        "issues": [],
        "ready_to_commit": False
    }
    (iteration_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    
    # Создать files-changed.txt шаблон
    files_changed = f"""# Session: {session_id}
# Iteration: 01
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Files will be listed here after fixes are applied

"""
    (iteration_dir / "files-changed.txt").write_text(files_changed, encoding="utf-8")
    
    # Обновить индекс сессий
    update_index(session_id, priority)
    
    print(f"[OK] Session created: {session_id}")
    print(f"    Path: {session_dir}")
    print(f"    Template: {session_dir / 'session.md'}")
    print()
    print("Next steps:")
    print(f"   1. Edit {session_dir}/session.md with task details")
    print(f"   2. Start parallel session with this directory")
    print(f"   3. Agent will create iteration-01/report.md")


def update_index(session_id: str, priority: str):
    """Обновить README.md с новой сессией."""
    sessions_dir = Path(__file__).parent.parent / "sessions"
    index_path = sessions_dir / "README.md"
    
    if not index_path.exists():
        # Создать новый индекс
        index_content = f"""# Session Index

| Session | Priority | Status | Iterations | Created |
|---------|----------|--------|------------|---------|
| {session_id} | {priority} | 🔄 In Progress | 0 | {datetime.now().strftime("%Y-%m-%d")} |

## Legend

- ✅ Done — Ready to commit
- 🔄 In Progress — Active iteration
- ⏳ Pending — Waiting to start
- ❌ Blocked — Needs review
"""
    else:
        # Добавить в существующий
        index_content = index_path.read_text(encoding="utf-8")
        new_row = f"| {session_id} | {priority} | 🔄 In Progress | 0 | {datetime.now().strftime("%Y-%m-%d")} |\n"
        
        # Вставить после заголовка таблицы
        lines = index_content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("|---------|"):
                lines.insert(i + 1, new_row)
                break
        index_content = "\n".join(lines)
    
    index_path.write_text(index_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create new fix session")
    parser.add_argument("--name", "-n", required=True, help="Session name (e.g., 'analysis-critical')")
    parser.add_argument("--priority", "-p", default="Medium", choices=["Critical", "High", "Medium"], help="Priority level")
    parser.add_argument("--source", "-s", default="", help="Source fix document path")
    parser.add_argument("--auto", "-a", action="store_true", help="Auto-detect source from reviews/fixes/")
    
    args = parser.parse_args()
    
    # Auto-detect source
    if args.auto:
        reviews_dir = Path(__file__).parent.parent / "docs" / "reviews" / "fixes"
        pattern = f"*{args.name}*fixes.md"
        matches = list(reviews_dir.glob(pattern))
        if matches:
            args.source = str(matches[0])
            print(f"[AUTO] Detected source: {args.source}")
        else:
            print(f"[WARN] No matching fix document found for '{args.name}'")
    
    create_session(args.name, args.priority, args.source)


if __name__ == "__main__":
    main()
