# ExploreDC

CS 5614 – Introduction to Database Systems, Summer 2026 Author: Marwa Bahr ([marwab@vt.edu](mailto:marwab@vt.edu))

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

## Setup

1. Install MySQL Community Server (and optionally MySQL Workbench): [https://dev.mysql.com/downloads/](https://dev.mysql.com/downloads/)  
     
2. Load the schema and data (enter your root password when prompted):  
     
   mysql \-u root \-p \< sql/schema.sql  
     
   mysql \-u root \-p \< sql/data.sql  
     
3. Verify the connection from Python:  
     
   pip install mysql-connector-python  
     
   python connect.py

## Schema overview

Eight relations: `museum`, `exhibit` (weak entity, PK \= MuseumID \+ ExhibitName), `category`, `artifact`, `app_user`, `visit`, `review`, and `must_see` (M:N between users and artifacts). All relations are in 3NF. User passwords are stored as SHA-256 hashes.  
