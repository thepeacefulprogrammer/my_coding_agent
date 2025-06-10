"""Database migration system for schema updates and versioning."""

from __future__ import annotations

import json
import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""

    def __init__(
        self,
        version: int,
        name: str,
        up_sql: str,
        down_sql: str,
        create_backup: bool = False,
        description: str = "",
    ):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.create_backup = create_backup
        self.description = description
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Convert migration to dictionary."""
        return {
            "version": self.version,
            "name": self.name,
            "up_sql": self.up_sql,
            "down_sql": self.down_sql,
            "create_backup": self.create_backup,
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Migration:
        """Create migration from dictionary."""
        migration = cls(
            version=data["version"],
            name=data["name"],
            up_sql=data["up_sql"],
            down_sql=data["down_sql"],
            create_backup=data.get("create_backup", False),
            description=data.get("description", ""),
        )
        if "created_at" in data:
            migration.created_at = data["created_at"]
        return migration


class MigrationManager:
    """Manages database schema migrations and versioning."""

    def __init__(self, db_path: str | Path):
        """Initialize migration manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.migrations: dict[int, Migration] = {}

    def initialize_version_tracking(self) -> None:
        """Initialize schema version tracking table."""
        logger.info("Initializing migration version tracking")

        with sqlite3.connect(self.db_path) as conn:
            # Create schema_version table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL DEFAULT 0,
                    last_migration_name TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            # Insert initial version if table is empty
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schema_version")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    """INSERT INTO schema_version (id, version, updated_at)
                       VALUES (1, 0, ?)""",
                    (datetime.now(timezone.utc).isoformat(),),
                )
                conn.commit()
                logger.debug("Initialized schema version at 0")

    def get_current_version(self) -> int:
        """Get the current database schema version.

        Returns:
            int: Current schema version
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else 0

    def set_version(self, version: int, migration_name: str = "") -> None:
        """Set the database schema version.

        Args:
            version: Version number to set
            migration_name: Name of the migration being applied
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE schema_version
                   SET version = ?, last_migration_name = ?, updated_at = ?
                   WHERE id = 1""",
                (version, migration_name, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            logger.debug(f"Set schema version to {version}")

    def register_migration(
        self,
        version: int,
        name: str,
        up_sql: str,
        down_sql: str,
        create_backup: bool = False,
        description: str = "",
    ) -> None:
        """Register a new migration.

        Args:
            version: Migration version number (must be unique)
            name: Human-readable migration name
            up_sql: SQL to apply the migration
            down_sql: SQL to rollback the migration
            create_backup: Whether to create a backup before applying
            description: Optional description of the migration

        Raises:
            ValueError: If version already registered or SQL is invalid
        """
        if version in self.migrations:
            raise ValueError(f"Migration version {version} already registered")

        # Validate SQL syntax
        self._validate_sql(up_sql)
        self._validate_sql(down_sql)

        migration = Migration(
            version=version,
            name=name,
            up_sql=up_sql,
            down_sql=down_sql,
            create_backup=create_backup,
            description=description,
        )

        self.migrations[version] = migration
        logger.debug(f"Registered migration {version}: {name}")

    def _validate_sql(self, sql: str) -> None:
        """Validate SQL syntax.

        Args:
            sql: SQL statement to validate

        Raises:
            ValueError: If SQL is invalid
        """
        if not sql.strip():
            raise ValueError("Invalid migration SQL: SQL cannot be empty")

        # Basic syntax validation
        forbidden_patterns = ["INVALID SQL", "DROP DATABASE", "ATTACH DATABASE"]

        sql_upper = sql.upper()
        for pattern in forbidden_patterns:
            if pattern in sql_upper:
                raise ValueError(f"Invalid migration SQL: {pattern} not allowed")

    def get_registered_migrations(self) -> list[dict]:
        """Get all registered migrations sorted by version.

        Returns:
            List[Dict]: List of migration dictionaries
        """
        return [
            self.migrations[version].to_dict()
            for version in sorted(self.migrations.keys())
        ]

    def apply_migration(self, version: int) -> str | None:
        """Apply a specific migration.

        Args:
            version: Migration version to apply

        Returns:
            Optional[str]: Path to backup file if created, None otherwise

        Raises:
            ValueError: If migration not found or already applied
        """
        if version not in self.migrations:
            raise ValueError(f"Migration version {version} not found")

        current_version = self.get_current_version()
        if version <= current_version:
            logger.warning(
                f"Migration {version} already applied (current: {current_version})"
            )
            return None

        migration = self.migrations[version]
        backup_path = None

        logger.info(f"Applying migration {version}: {migration.name}")

        try:
            # Create backup if requested
            if migration.create_backup:
                backup_path = self._create_backup()
                logger.info(f"Created backup at {backup_path}")

            # Apply migration in transaction
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                try:
                    # Execute migration SQL
                    conn.execute(migration.up_sql)

                    # Update schema version
                    conn.execute(
                        """UPDATE schema_version
                           SET version = ?, last_migration_name = ?, updated_at = ?
                           WHERE id = 1""",
                        (
                            version,
                            migration.name,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

                    conn.execute("COMMIT")
                    logger.info(f"Successfully applied migration {version}")
                    return backup_path

                except Exception as e:
                    conn.execute("ROLLBACK")
                    logger.error(f"Failed to apply migration {version}: {e}")
                    raise

        except Exception:
            # If backup was created and migration failed, note backup location
            if backup_path:
                logger.error(f"Migration failed, backup available at {backup_path}")
            raise

    def apply_all_migrations(self) -> list[int]:
        """Apply all pending migrations in order.

        Returns:
            List[int]: List of applied migration versions
        """
        current_version = self.get_current_version()
        pending_versions = [
            version
            for version in sorted(self.migrations.keys())
            if version > current_version
        ]

        applied = []
        for version in pending_versions:
            try:
                self.apply_migration(version)
                applied.append(version)
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                break  # Stop on first failure

        logger.info(f"Applied {len(applied)} migrations: {applied}")
        return applied

    def rollback_migration(self, version: int) -> bool:
        """Rollback a specific migration.

        Args:
            version: Migration version to rollback

        Returns:
            bool: True if rollback succeeded, False otherwise
        """
        if version not in self.migrations:
            raise ValueError(f"Migration version {version} not found")

        current_version = self.get_current_version()
        if version > current_version:
            logger.warning(
                f"Migration {version} not applied (current: {current_version})"
            )
            return False

        migration = self.migrations[version]
        logger.info(f"Rolling back migration {version}: {migration.name}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                try:
                    # Execute rollback SQL
                    conn.execute(migration.down_sql)

                    # Update schema version to previous
                    new_version = version - 1
                    conn.execute(
                        """UPDATE schema_version
                           SET version = ?, last_migration_name = ?, updated_at = ?
                           WHERE id = 1""",
                        (
                            new_version,
                            f"rollback_{migration.name}",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

                    conn.execute("COMMIT")
                    logger.info(f"Successfully rolled back migration {version}")
                    return True

                except Exception as e:
                    conn.execute("ROLLBACK")
                    logger.error(f"Failed to rollback migration {version}: {e}")
                    raise

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _create_backup(self) -> str:
        """Create a backup of the database.

        Returns:
            str: Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.{timestamp}.backup"

        shutil.copy2(self.db_path, backup_path)
        logger.debug(f"Created database backup at {backup_path}")

        return backup_path

    def get_migration_history(self) -> list[dict]:
        """Get the history of applied migrations.

        Returns:
            List[Dict]: Migration history with timestamps
        """
        # This is a simplified version - in a real implementation,
        # you might want to track each migration application separately
        current_version = self.get_current_version()

        history = []
        for version in range(1, current_version + 1):
            if version in self.migrations:
                migration = self.migrations[version]
                history.append(
                    {
                        "version": version,
                        "name": migration.name,
                        "applied_at": migration.created_at,
                        "description": migration.description,
                    }
                )

        return history

    def export_migrations(self, file_path: str | Path) -> None:
        """Export all registered migrations to a JSON file.

        Args:
            file_path: Path to export file
        """
        migrations_data = {
            "migrations": [
                migration.to_dict() for migration in self.migrations.values()
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(migrations_data, f, indent=2)

        logger.info(f"Exported {len(self.migrations)} migrations to {file_path}")

    def import_migrations(self, file_path: str | Path) -> int:
        """Import migrations from a JSON file.

        Args:
            file_path: Path to import file

        Returns:
            int: Number of migrations imported
        """
        with open(file_path) as f:
            data = json.load(f)

        imported_count = 0
        for migration_data in data.get("migrations", []):
            migration = Migration.from_dict(migration_data)
            if migration.version not in self.migrations:
                self.migrations[migration.version] = migration
                imported_count += 1

        logger.info(f"Imported {imported_count} migrations from {file_path}")
        return imported_count
