# PostgreSQL backup and recovery

Backups may contain finding evidence and must be handled as sensitive data.

The following commands require PostgreSQL client tools (`pg_dump` and `pg_restore`)
and `SENTINELFORGE_DATABASE_URL` pointing to an operator-controlled database.

```bash
cd SentinelForge-AI
python -m sentinelforge.backup backup ./private-backups/sentinelforge.dump
```

The utility refuses to overwrite an existing dump and attempts to restrict its
file permissions to the owner. Store encrypted backups outside the repository.

**Restore is destructive.** Only restore to a disposable test database first:

```bash
export SENTINELFORGE_DATABASE_URL='postgresql://.../sentinelforge_restore_test'
python -m sentinelforge.backup restore ./private-backups/sentinelforge.dump --confirm-restore
```

Verify restored finding counts and sample investigation IDs before using the
backup in an incident. Never run the restore command against production without
an approved maintenance plan and a separate verified backup.

The utility and unit tests do **not** prove that an actual restore succeeded.
A disposable PostgreSQL round-trip integration test is required.
