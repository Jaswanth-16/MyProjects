"""Operator-controlled PostgreSQL backup and restore helpers.

Run against an isolated database and protect resulting dumps as sensitive data.
"""
from __future__ import annotations
import argparse
import os
import subprocess
from pathlib import Path


def backup(dsn: str, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        try:
            subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-acl",
                            "--dbname", dsn], stdout=output, stderr=subprocess.PIPE,
                           check=True, timeout=300)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    destination.chmod(0o600)


def restore(dsn: str, source: Path, *, confirmed: bool = False) -> None:
    if not confirmed:
        raise ValueError("Restore requires explicit confirmation")
    if not source.is_file():
        raise FileNotFoundError(source)
    subprocess.run(["pg_restore", "--no-owner", "--no-acl", "--clean",
                    "--if-exists", "--dbname", dsn, str(source)],
                   stderr=subprocess.PIPE, check=True, timeout=300)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup/restore a controlled PostgreSQL database")
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--confirm-restore", action="store_true")
    args = parser.parse_args()
    dsn = os.getenv("SENTINELFORGE_DATABASE_URL")
    if not dsn:
        parser.error("SENTINELFORGE_DATABASE_URL is required")
    if args.operation == "backup":
        backup(dsn, args.path)
    else:
        restore(dsn, args.path, confirmed=args.confirm_restore)


if __name__ == "__main__":
    main()
