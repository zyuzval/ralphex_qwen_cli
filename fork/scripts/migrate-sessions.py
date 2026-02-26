#!/usr/bin/env python3
"""
migrate-sessions.py - Миграция существующих отчётов в новую структуру

Использование:
    python scripts/migrate-sessions.py --from-docs --to-sessions
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


def migrate_existing_reports():
    """Миграция отчётов из docs/reviews/fixes/ в docs/sessions/."""
    
    reviews_dir = Path(__file__).parent.parent / "docs" / "reviews" / "fixes"
    sessions_dir = Path(__file__).parent.parent / "docs" / "sessions"
    
    # Найти все fix документы
    fix_docs = list(reviews_dir.glob("*-fixes.md"))
    
    migrated = []
    
    for fix_doc in fix_docs:
        # Извлечь имя из имени файла
        # 02-analysis-modules-fixes.md -> analysis-critical
        name = fix_doc.stem.replace("-fixes", "").replace("-modules", "").replace("-api", "").replace("-react", "")
        name = name.lstrip("0123456789-")
        
        # Создать сессию
        session_id = f"SESSION-{len(migrated)+1:03d}-{name}-migrated"
        session_dir = sessions_dir / session_id
        iteration_dir = session_dir / "iteration-01"
        iteration_dir.mkdir(parents=True, exist_ok=True)
        
        # Скопировать fix документ
        dest_doc = session_dir / "source-fixes.md"
        dest_doc.write_text(fix_doc.read_text(encoding="utf-8"), encoding="utf-8")
        
        # Создать session.md
        session_md = f"""# Session: {session_id}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
**Priority:** Critical  
**Source:** {fix_doc}

## Status

✅ **MIGRATED** — Existing fixes imported

## Files to Review

See: `source-fixes.md`

## Iterations

| Iteration | Status | Date | Notes |
|-----------|--------|------|-------|
| 01 (migrated) | PENDING REVIEW | {datetime.now().strftime("%Y-%m-%d")} | Imported from existing work |

## Final Status

- [ ] Review fixes
- [ ] Apply if valid
- [ ] Commit
"""
        (session_dir / "session.md").write_text(session_md, encoding="utf-8")
        
        # Создать status.json
        status = {
            "session": session_id,
            "iteration": 1,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_review",
            "checks": {
                "tests": None,
                "build": None,
                "typescript": None
            },
            "files_modified": [],
            "issues": ["Needs review before applying"],
            "ready_to_commit": False,
            "migrated_from": str(fix_doc)
        }
        (iteration_dir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # Создать files-changed.txt
        files_txt = f"""# Session: {session_id}
# Iteration: 01 (migrated)
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Migrated from: {fix_doc}
# Files will be listed after review

"""
        (iteration_dir / "files-changed.txt").write_text(files_txt, encoding="utf-8")
        
        migrated.append(session_id)
        print(f"[OK] Migrated: {fix_doc.name} -> {session_id}")
    
    # Обновить индекс
    update_index(migrated)
    
    print(f"\n[OK] Total migrated: {len(migrated)}")
    print(f"[DIR] Sessions directory: {sessions_dir}")


def update_index(migrated_sessions: list):
    """Обновить README.md с мигрированными сессиями."""
    sessions_dir = Path(__file__).parent.parent / "docs" / "sessions"
    index_path = sessions_dir / "README.md"
    
    if not index_path.exists():
        return
    
    index_content = index_path.read_text(encoding="utf-8")
    
    # Добавить мигрированные сессии
    new_rows = []
    for session_id in migrated_sessions:
        name = session_id.replace("SESSION-", "").replace("-migrated", "")
        new_rows.append(f"| {session_id} | Critical | ⏳ Pending Review | 1 | {datetime.now().strftime("%Y-%m-%d")} |")
    
    if new_rows:
        # Вставить после заголовка
        lines = index_content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("|---------|"):
                for row in reversed(new_rows):
                    lines.insert(i + 1, row)
                break
        index_content = "\n".join(lines)
        
        # Добавить секцию о миграции
        migration_note = """
## Migrated Sessions

Sessions marked as "migrated" were imported from existing fix documents.
They need review before fixes can be applied.
"""
        if "## Migrated Sessions" not in index_content:
            index_content += migration_note
    
    index_path.write_text(index_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Migrate existing fix reports to new session structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        reviews_dir = Path(__file__).parent.parent / "docs" / "reviews" / "fixes"
        fix_docs = list(reviews_dir.glob("*-fixes.md"))
        print("Would migrate:")
        for doc in fix_docs:
            print(f"  {doc.name}")
        print(f"\nTotal: {len(fix_docs)} documents")
    else:
        migrate_existing_reports()


if __name__ == "__main__":
    main()
