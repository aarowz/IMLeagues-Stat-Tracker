# Database Files Directory

The MySQL server running in the database container is configured to automatically execute all `.sql` files in this directory when the container is first created.

## File Execution Order

SQL files are executed in alphabetical order. Files are numbered with prefixes (e.g., `01_`, `02_`, etc.) to ensure proper execution sequence:

1. `01_imleagues_schema.sql` - Database schema (DDL) - Creates all tables
2. `02_imleagues_data.sql` through `16_player_awards.sql` - Sample data (DML) - Populates tables with initial data

## Important Notes

- SQL files are only executed when the database container is first created
- Simply stopping and restarting the container will NOT re-run the SQL files
- If you make changes to any SQL files after the container is created, you must delete and recreate the container

## Recreating the Database

To recreate the database container with updated SQL files:

### Team Repository
```bash
docker compose down db -v
docker compose up db -d
```

### Sandbox Repository
```bash
docker compose -f sandbox.yaml down db -v
docker compose -f sandbox.yaml up db -d
```

The `-v` flag removes the volume associated with MySQL, which is necessary to rerun the SQL files.

## File Structure

- Schema files define the database structure (tables, relationships, constraints)
- Data files contain INSERT statements to populate tables with sample data
- Files are organized sequentially to ensure proper dependencies are met
