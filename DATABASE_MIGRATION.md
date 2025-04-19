# Database Migration Guide (Alembic)

This guide explains how to generate and apply database migrations using Alembic after making changes to the SQLAlchemy models defined in `src/database/models.py`.

## Prerequisites

- Alembic must be initialized and configured as described in `SETUP_GUIDE.md`.
- Your `alembic.ini` file must point to the correct database URL.
- Your `alembic/env.py` file must be configured to use the metadata from your models (`src.database.session.Base.metadata`).
- Ensure your database (local instance or Docker container) is running before applying migrations.

## Migration Steps

### 1. Generate Migration Script

After you have modified your models (e.g., added/removed columns, changed types, added tables), generate a new migration script using Alembic's autogenerate feature:

```bash
# Ensure you are in the project root directory (agents/zenplify-agent)
poetry run alembic revision --autogenerate -m "Your concise migration description"
```

- Replace `"Your concise migration description"` with a short message describing the schema changes (e.g., `"add gender and date_of_birth to users table"`).
- This command compares your current models against the database schema recorded by Alembic and creates a new Python script in the `alembic/versions/` directory.

### 2. Review the Generated Script (CRITICAL STEP)

Before applying any migration, **always** review the script Alembic generated.

- Open the new file created in `alembic/versions/`. The filename will contain a unique ID and part of your description message (e.g., `alembic/versions/xxxxxxxxxxxx_your_description.py`).
- **Carefully examine the `upgrade()` function:**
    - Verify that it contains the correct SQLAlchemy operations or raw SQL commands (e.g., `op.add_column()`, `op.create_table()`, `op.drop_column()`) to reflect your intended schema changes.
    - Check column names, types, nullability constraints, foreign keys, etc.
- **Carefully examine the `downgrade()` function:**
    - Ensure it contains the necessary operations to safely reverse the changes made in the `upgrade()` function. This is crucial if you ever need to roll back the migration.
- **Make Manual Corrections:** Alembic's autogenerate feature might not always capture every nuance perfectly, especially for complex changes like type alterations, constraint modifications, or index changes. If the generated script is incorrect or incomplete, **manually edit the Python script** to ensure it performs the exact operations required.

### 3. Apply the Migration

Once you have reviewed the script and confirmed it is correct, apply the migration to your database:

```bash
# Ensure the database is running
poetry run alembic upgrade head
```

- `head` instructs Alembic to apply all pending migrations up to the latest revision.
- Alembic connects to the database specified in `alembic.ini` and executes the `upgrade()` function(s) from the unapplied migration script(s).

Your database schema should now be synchronized with your SQLAlchemy models.

## Rolling Back Migrations (If Necessary)

If you apply a migration and realize it was incorrect or caused issues, you can roll it back using the `downgrade` command.

```bash
# Downgrade by one revision
poetry run alembic downgrade -1

# Downgrade to a specific revision (replace xxxxxxxx with the target revision ID prefix)
# poetry run alembic downgrade xxxxxxxx
```

**Caution:** Downgrading can be risky, especially if the `downgrade()` function in the migration script is incorrect or if data has been added that depends on the schema changes. Always back up your database before performing major schema changes or downgrades if the data is critical. 