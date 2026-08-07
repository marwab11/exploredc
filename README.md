# ExploreDC

CS 5614 – Introduction to Database Systems, Summer 2026 Author: Marwa Bahr

A database of Washington, DC museums, exhibits, and artifacts. Users log visits, write reviews, and keep a "must-see" list of artifacts.

- **DBMS:** MySQL 8 (MySQL Community Server)  
- **Interface language:** Python 3 (`mysql-connector-python`)

## Repository contents

| File | Purpose |
| :---- | :---- |
| `sql/schema.sql` | Creates the `exploredc` database and all 8 tables with PK, FK, NOT NULL, UNIQUE, and CHECK constraints |
| `sql/data.sql` | Loads sample data (30+ rows in every major table) |
| `connect.py` | Python script that connects to MySQL and prints connection status \+ row counts |
| `ID.txt` | Author / course identification |
| `gui.py` | Tkinter gui - App interface |
