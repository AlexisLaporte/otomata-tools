"""Claude Code skills management (enable/disable oto skills via symlinks)."""

import shutil
import typer
from pathlib import Path

app = typer.Typer(help="Manage oto skills for Claude Code")

SKILLS_SOURCE = Path(__file__).resolve().parent.parent.parent / "skills"
SKILLS_TARGET = Path.home() / ".claude" / "skills"


def _available_skills() -> list[str]:
    """List available skill names from source directory."""
    if not SKILLS_SOURCE.exists():
        return []
    return sorted(
        d.name for d in SKILLS_SOURCE.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )


def _is_installed(name: str) -> bool:
    """Check if a skill is installed (symlink exists and points to source)."""
    target = SKILLS_TARGET / name
    return target.is_symlink() and target.resolve() == (SKILLS_SOURCE / name).resolve()


@app.command("list")
def list_skills():
    """List available oto skills and their installation status."""
    skills = _available_skills()
    if not skills:
        print(f"No skills found in {SKILLS_SOURCE}")
        raise typer.Exit(1)

    for name in skills:
        status = "installed" if _is_installed(name) else "not installed"
        print(f"  {'✓' if status == 'installed' else '·'} {name:<20} {status}")


@app.command("enable")
def enable(
    names: list[str] = typer.Argument(None, help="Skill names to enable"),
    all_skills: bool = typer.Option(False, "--all", help="Enable all skills"),
):
    """Enable skills by creating symlinks in ~/.claude/skills/."""
    skills = _available_skills() if all_skills else (names or [])
    if not skills:
        print("Specify skill names or use --all")
        raise typer.Exit(1)

    SKILLS_TARGET.mkdir(parents=True, exist_ok=True)

    for name in skills:
        source = SKILLS_SOURCE / name
        if not source.exists():
            print(f"  ✗ {name} — not found in {SKILLS_SOURCE}")
            continue

        target = SKILLS_TARGET / name
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            else:
                shutil.rmtree(target)

        target.symlink_to(source)
        print(f"  ✓ {name}")


@app.command("disable")
def disable(
    names: list[str] = typer.Argument(None, help="Skill names to disable"),
    all_skills: bool = typer.Option(False, "--all", help="Disable all skills"),
):
    """Disable skills by removing symlinks from ~/.claude/skills/."""
    skills = _available_skills() if all_skills else (names or [])
    if not skills:
        print("Specify skill names or use --all")
        raise typer.Exit(1)

    for name in skills:
        target = SKILLS_TARGET / name
        if target.is_symlink():
            target.unlink()
            print(f"  ✓ {name} disabled")
        elif target.exists():
            print(f"  · {name} — not a symlink, skipping")
        else:
            print(f"  · {name} — not installed")
