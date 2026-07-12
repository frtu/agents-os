"""Skill manager for installing and managing skills from the shared skills folder.

Usage:
    python skill_manager.py list          # List available skills
    python skill_manager.py installed     # List installed skills
    python skill_manager.py show <name>   # Show skill details
    python skill_manager.py install <name> [--copy]  # Install a skill (symlink by default)
    python skill_manager.py uninstall <name>         # Remove an installed skill
"""
import argparse
import shutil
import sys
from pathlib import Path

SKILLS_SOURCE = Path(__file__).parent.parent / "skills"
SKILLS_DEST = Path(__file__).parent / "skills"


def parse_skill_frontmatter(skill_path: Path) -> dict:
    """Parse YAML frontmatter from SKILL.md."""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return {}

    content = skill_file.read_text()
    if not content.startswith("---"):
        return {"name": skill_path.name}

    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {"name": skill_path.name}

    frontmatter = {}
    current_key = None
    current_value = []

    for line in lines[1:end_idx]:
        if line.startswith("  ") and current_key:
            current_value.append(line.strip())
        elif ":" in line:
            if current_key:
                frontmatter[current_key] = " ".join(current_value).strip()
            key, _, value = line.partition(":")
            current_key = key.strip()
            value = value.strip()
            if value.startswith(">"):
                current_value = []
            else:
                current_value = [value.strip('"').strip("'")]

    if current_key:
        frontmatter[current_key] = " ".join(current_value).strip()

    return frontmatter


def list_available_skills():
    """List all available skills from the source folder."""
    if not SKILLS_SOURCE.exists():
        print(f"Skills source not found: {SKILLS_SOURCE}")
        return

    skills = []
    for skill_dir in sorted(SKILLS_SOURCE.iterdir()):
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                info = parse_skill_frontmatter(skill_dir)
                skills.append({
                    "name": info.get("name", skill_dir.name),
                    "dir": skill_dir.name,
                    "description": info.get("description", "No description"),
                })

    if not skills:
        print("No skills found.")
        return

    print(f"\nAvailable skills ({len(skills)}):\n")
    for skill in skills:
        desc = skill["description"][:60] + "..." if len(skill["description"]) > 60 else skill["description"]
        print(f"  {skill['dir']:<25} {desc}")
    print(f"\nSource: {SKILLS_SOURCE}")


def list_installed_skills():
    """List installed skills."""
    SKILLS_DEST.mkdir(exist_ok=True)

    installed = []
    for item in sorted(SKILLS_DEST.iterdir()):
        if item.name.startswith("."):
            continue
        skill_file = item / "SKILL.md" if item.is_dir() else None
        if item.is_symlink():
            target = item.resolve()
            info = parse_skill_frontmatter(target)
            installed.append({
                "name": item.name,
                "type": "symlink",
                "target": str(target),
                "description": info.get("description", ""),
            })
        elif item.is_dir() and skill_file and skill_file.exists():
            info = parse_skill_frontmatter(item)
            installed.append({
                "name": item.name,
                "type": "copy",
                "description": info.get("description", ""),
            })

    if not installed:
        print("\nNo skills installed.")
        print(f"\nInstall with: python skill_manager.py install <skill-name>")
        return

    print(f"\nInstalled skills ({len(installed)}):\n")
    for skill in installed:
        link_info = f" -> {skill['target']}" if skill["type"] == "symlink" else " (copy)"
        print(f"  {skill['name']:<25} [{skill['type']}]{link_info}")


def show_skill(name: str):
    """Show details of a specific skill."""
    skill_path = SKILLS_SOURCE / name
    if not skill_path.exists():
        print(f"Skill not found: {name}")
        print(f"Run 'python skill_manager.py list' to see available skills.")
        return

    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        print(f"No SKILL.md found in {skill_path}")
        return

    info = parse_skill_frontmatter(skill_path)

    print(f"\n{'='*60}")
    print(f"Skill: {info.get('name', name)}")
    print(f"{'='*60}")
    print(f"\nDescription:\n  {info.get('description', 'No description')}")

    if "allowed-tools" in info:
        print(f"\nAllowed tools: {info['allowed-tools']}")
    if "compatibility" in info:
        print(f"\nCompatibility: {info['compatibility']}")

    # List files in skill
    print(f"\nContents:")
    for item in sorted(skill_path.rglob("*")):
        if item.is_file() and not item.name.startswith("."):
            rel = item.relative_to(skill_path)
            print(f"  {rel}")

    # Check if installed
    dest_path = SKILLS_DEST / name
    if dest_path.exists():
        if dest_path.is_symlink():
            print(f"\nStatus: Installed (symlink)")
        else:
            print(f"\nStatus: Installed (copy)")
    else:
        print(f"\nStatus: Not installed")
        print(f"Install with: python skill_manager.py install {name}")


def install_skill(name: str, copy: bool = False):
    """Install a skill to the local skills folder."""
    SKILLS_DEST.mkdir(exist_ok=True)

    source_path = SKILLS_SOURCE / name
    if not source_path.exists():
        print(f"Skill not found: {name}")
        print(f"Run 'python skill_manager.py list' to see available skills.")
        return False

    dest_path = SKILLS_DEST / name
    if dest_path.exists():
        print(f"Skill already installed: {name}")
        print(f"Uninstall first with: python skill_manager.py uninstall {name}")
        return False

    if copy:
        shutil.copytree(source_path, dest_path)
        print(f"Copied skill: {name}")
    else:
        dest_path.symlink_to(source_path.resolve())
        print(f"Linked skill: {name} -> {source_path}")

    return True


def uninstall_skill(name: str):
    """Remove an installed skill."""
    dest_path = SKILLS_DEST / name
    if not dest_path.exists():
        print(f"Skill not installed: {name}")
        return False

    if dest_path.is_symlink():
        dest_path.unlink()
        print(f"Removed symlink: {name}")
    else:
        shutil.rmtree(dest_path)
        print(f"Removed copy: {name}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Manage skills for leader-assistant")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # list command
    subparsers.add_parser("list", help="List available skills")

    # installed command
    subparsers.add_parser("installed", help="List installed skills")

    # show command
    show_parser = subparsers.add_parser("show", help="Show skill details")
    show_parser.add_argument("name", help="Skill name")

    # install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("name", help="Skill name")
    install_parser.add_argument("--copy", action="store_true", help="Copy instead of symlink")

    # uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill")
    uninstall_parser.add_argument("name", help="Skill name")

    args = parser.parse_args()

    if args.command == "list":
        list_available_skills()
    elif args.command == "installed":
        list_installed_skills()
    elif args.command == "show":
        show_skill(args.name)
    elif args.command == "install":
        install_skill(args.name, args.copy)
    elif args.command == "uninstall":
        uninstall_skill(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
