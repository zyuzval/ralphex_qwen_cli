#!/usr/bin/env python3
"""
generate_report.py - Генерирует стандартизированный отчёт для параллельной сессии

Использование:
    python scripts/generate_report.py --fix-session analysis-critical

Выходные данные:
    - Отчёт в markdown формате
    - Список изменённых файлов
    - Результаты тестов
    - Результаты сборки
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
    """Выполнить команду и вернуть (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=300  # 5 минут таймаут
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return -1, "", str(e)


def get_git_diff() -> tuple[str, str]:
    """Получить git diff статистику и полный diff."""
    _, stat, _ = run_command(["git", "diff", "--stat"])
    _, diff, _ = run_command(["git", "diff"])
    return stat.strip(), diff.strip()


def get_modified_files() -> list[str]:
    """Получить список изменённых файлов."""
    _, files, _ = run_command(["git", "diff", "--name-only"])
    return [f.strip() for f in files.split("\n") if f.strip()]


def run_tests() -> tuple[bool, str]:
    """Запустить тесты и вернуть результат."""
    print("Running pytest...")
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
    ])
    success = returncode == 0
    output = stdout + "\n" + stderr
    return success, output[-5000:]  # Последние 5000 символов


def run_build() -> tuple[bool, str]:
    """Запустить сборку frontend и вернуть результат."""
    print("Running npm build...")
    returncode, stdout, stderr = run_command([
        "npm", "run", "build"
    ], capture=False)
    success = returncode == 0
    return success, stdout + stderr


def run_typescript_check() -> tuple[bool, str]:
    """Запустить проверку TypeScript."""
    print("Running TypeScript check...")
    returncode, stdout, stderr = run_command([
        "npx", "tsc", "--noEmit"
    ])
    success = returncode == 0
    output = stdout + "\n" + stderr
    return success, output[-3000:]


def generate_report(fix_session_name: str = "unnamed") -> str:
    """Сгенерировать полный отчёт."""
    print("=" * 50)
    print(f"  TG-STATS Fix Session Report: {fix_session_name}")
    print("=" * 50)
    print()

    # Git diff
    print("Collecting git diff...")
    diff_stat, diff_full = get_git_diff()
    modified_files = get_modified_files()

    # Tests
    print("Running tests...")
    tests_passed, tests_output = run_tests()

    # Build
    print("Running build...")
    build_passed, build_output = run_build()

    # TypeScript
    print("Running TypeScript check...")
    ts_passed, ts_output = run_typescript_check()

    # Generate markdown report
    report = f"""# Fix Session Report: {fix_session_name}

**Generated:** {datetime.now().isoformat()}

---

## Summary

| Check | Status |
|-------|--------|
| Tests | {"✅ PASS" if tests_passed else "❌ FAIL"} |
| Build | {"✅ PASS" if build_passed else "❌ FAIL"} |
| TypeScript | {"✅ PASS" if ts_passed else "❌ FAIL"} |

---

## Files Modified ({len(modified_files)})

```
{chr(10).join(f"- {f}" for f in modified_files)}
```

---

## Git Diff Statistics

```
{diff_stat}
```

---

## Test Results

{"✅ All tests passed" if tests_passed else "❌ Some tests failed"}

<details>
<summary>Test Output (click to expand)</summary>

```bash
{tests_output}
```

</details>

---

## Build Results

{"✅ Build succeeded" if build_passed else "❌ Build failed"}

<details>
<summary>Build Output (click to expand)</summary>

```bash
{build_output[-3000:]}
```

</details>

---

## TypeScript Check

{"✅ No TypeScript errors" if ts_passed else "❌ TypeScript errors found"}

<details>
<summary>TypeScript Output (click to expand)</summary>

```bash
{ts_output}
```

</details>

---

## Verification Checklist

- [ ] All tests pass
- [ ] Build succeeds
- [ ] No new TypeScript errors
- [ ] Specific fixes verified (see below)

---

## Specific Fixes Verified

<!-- Fill this section manually -->

### Fix 1: [Description]
- [ ] Verified working

### Fix 2: [Description]
- [ ] Verified working

---

## Issues Encountered

<!-- Fill this section manually -->

- None

---

## Recommendations

<!-- Fill this section manually -->

- Ready to commit
- Needs additional review
- Has known issues (see above)
"""

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate standardized fix session report"
    )
    parser.add_argument(
        "--fix-session", "-f",
        default="unnamed",
        help="Name of the fix session"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    report = generate_report(args.fix_session)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        print(f"\nReport saved to: {output_path}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
