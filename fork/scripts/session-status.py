#!/usr/bin/env python3
"""
session-status.py - Проверить статус сессии

Использование:
    python scripts/session-status.py SESSION-001
"""

import argparse
import json
from pathlib import Path


def check_status(session_id: str):
    """Проверить статус сессии."""
    
    sessions_dir = Path(__file__).parent.parent / "sessions"
    session_dir = sessions_dir / session_id
    
    if not session_dir.exists():
        print(f"❌ Session not found: {session_id}")
        return
    
    # Проверить session.md
    session_md = session_dir / "session.md"
    if session_md.exists():
        print(f"📄 Session: {session_id}")
        print(f"   Template: {session_md}")
    else:
        print(f"⚠️  No session.md found")
    
    # Найти последнюю итерацию
    iterations = sorted(session_dir.glob("iteration-*"))
    if not iterations:
        print(f"⚠️  No iterations found")
        return
    
    last_iteration = iterations[-1]
    print(f"\n📁 Latest iteration: {last_iteration.name}")
    
    # Проверить status.json
    status_json = last_iteration / "status.json"
    if status_json.exists():
        status = json.loads(status_json.read_text(encoding="utf-8"))
        print(f"\n📊 Status: {status.get('status', 'unknown').upper()}")
        print(f"   Tests: {'✅' if status.get('checks', {}).get('tests') else '❌' if status.get('checks', {}).get('tests') is False else '⏳'}")
        print(f"   Build: {'✅' if status.get('checks', {}).get('build') else '❌' if status.get('checks', {}).get('build') is False else '⏳'}")
        print(f"   TypeScript: {'✅' if status.get('checks', {}).get('typescript') else '❌' if status.get('checks', {}).get('typescript') is False else '⏳'}")
        print(f"   Ready to commit: {'✅ Yes' if status.get('ready_to_commit') else '❌ No'}")
        
        if status.get('issues'):
            print(f"\n⚠️  Issues:")
            for issue in status['issues']:
                print(f"   - {issue}")
        
        if status.get('files_modified'):
            print(f"\n📝 Files modified ({len(status['files_modified'])}):")
            for f in status['files_modified']:
                print(f"   - {f}")
    else:
        print(f"⚠️  No status.json found")
    
    # Проверить report.md
    report_md = last_iteration / "report.md"
    if report_md.exists():
        print(f"\n📄 Report: {report_md}")
    else:
        print(f"\n⚠️  No report.md found")
    
    # Проверить files-changed.txt
    files_txt = last_iteration / "files-changed.txt"
    if files_txt.exists():
        content = files_txt.read_text(encoding="utf-8")
        if not content.strip().startswith('#') or len(content.split('\n')) > 3:
            print(f"\n📝 Files changed:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"   {line}")


def main():
    parser = argparse.ArgumentParser(description="Check session status")
    parser.add_argument("session", help="Session ID (e.g., SESSION-001)")
    
    args = parser.parse_args()
    check_status(args.session)


if __name__ == "__main__":
    main()
