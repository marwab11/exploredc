#!/usr/bin/env python3
"""
ExploreDC - GUI for Project Phase 2
CS 5614 - Introduction to Database Systems, Summer 2026
Marwa Bahr

A Tkinter window that connects to my MySQL database (exploredc) and lets you
insert, update, and delete rows. There is also a
tab that runs three aggregate queries and shows the results.

There is one tab for each of my 8 tables: museum, exhibit, category,
artifact, app_user, visit, review, and must_see.

To run:
    pip install mysql-connector-python
    python gui.py
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector


# --------------------------------------------------------------------------
# Talking to MySQL
# --------------------------------------------------------------------------
class Database:
    """Wraps the connection so the rest of the code just calls query/execute."""

    def __init__(self):
        self.conn = None

    def connect(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )

    def server_info(self):
        return self.conn.get_server_info()

    def query(self, sql, params=None):
        """Run a SELECT and hand back the column names and the rows."""
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        return cols, rows

    def execute(self, sql, params=None):
        """Run an INSERT/UPDATE/DELETE. Commits, or comes back if it fails."""
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params or ())
            affected = cur.rowcount
            self.conn.commit()
            return affected
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def close(self):
        if self.conn is not None:
            self.conn.close()


class ValidationError(Exception):
    """Raised when something typed in the form is wrong, before any SQL runs."""


# --------------------------------------------------------------------------
# Fill the dropdown menus. Each one returns a label to show the user,
# followed by the key value(s) that  go into database.
# --------------------------------------------------------------------------
LOOKUP_MUSEUM = ("SELECT CONCAT(`Name`, ' (#', `MuseumID`, ')'), `MuseumID` "
                 "FROM `museum` ORDER BY `Name`")
LOOKUP_CATEGORY = ("SELECT CONCAT(`Name`, ' (#', `CategoryID`, ')'), `CategoryID` "
                   "FROM `category` ORDER BY `Name`")
LOOKUP_USER = ("SELECT CONCAT(`Username`, ' (#', `UserID`, ')'), `UserID` "
               "FROM `app_user` ORDER BY `Username`")
LOOKUP_ARTIFACT = ("SELECT CONCAT(`Title`, ' (#', `ArtifactID`, ')'), `ArtifactID` "
                   "FROM `artifact` ORDER BY `Title`")
# EXHIBIT has a two-column key, so this lookup returns both.
LOOKUP_EXHIBIT = (
    "SELECT CONCAT(m.`Name`, ' > ', e.`ExhibitName`), e.`MuseumID`, e.`ExhibitName` "
    "FROM `exhibit` e JOIN `museum` m ON m.`MuseumID` = e.`MuseumID` "
    "ORDER BY m.`Name`, e.`ExhibitName`"
)


# --------------------------------------------------------------------------
# One entry per tab. This describes each table once - its columns, what to
# label them, and what kind of input box each one needs
#
# Field types: auto (the AUTO_INCREMENT key, read-only), text, multiline,
# int, date, choice (fixed list), password, fk (dropdown from another table).
# --------------------------------------------------------------------------
TABLES = [
    {
        "table": "museum",
        "label": "Museums",
        "pk": ["MuseumID"],
        "order_by": "`MuseumID`",
        "fields": [
            {"cols": ["MuseumID"], "label": "Museum ID", "type": "auto"},
            {"cols": ["Name"], "label": "Name", "type": "text", "required": True},
            {"cols": ["Address"], "label": "Address", "type": "text", "required": True},
            {"cols": ["Description"], "label": "Description", "type": "multiline"},
        ],
    },
    {
        # Weak entity - the key is (MuseumID, ExhibitName), so both are on
        # the form and neither is auto-generated.
        "table": "exhibit",
        "label": "Exhibits",
        "pk": ["MuseumID", "ExhibitName"],
        "order_by": "`MuseumID`, `ExhibitName`",
        "fields": [
            {"cols": ["MuseumID"], "label": "Museum", "type": "fk",
             "lookup": LOOKUP_MUSEUM, "required": True},
            {"cols": ["ExhibitName"], "label": "Exhibit Name", "type": "text",
             "required": True},
            {"cols": ["Location"], "label": "Location", "type": "text",
             "required": True},
        ],
    },
    {
        "table": "category",
        "label": "Categories",
        "pk": ["CategoryID"],
        "order_by": "`CategoryID`",
        "fields": [
            {"cols": ["CategoryID"], "label": "Category ID", "type": "auto"},
            {"cols": ["Name"], "label": "Name", "type": "text", "required": True},
        ],
    },
    {
        "table": "artifact",
        "label": "Artifacts",
        "pk": ["ArtifactID"],
        "order_by": "`ArtifactID`",
        "fields": [
            {"cols": ["ArtifactID"], "label": "Artifact ID", "type": "auto"},
            {"cols": ["Title"], "label": "Title", "type": "text", "required": True},
            {"cols": ["Creator"], "label": "Creator", "type": "text"},
            {"cols": ["Year"], "label": "Year", "type": "int", "min": -3000, "max": 2026},
            # one dropdown fills both MuseumID and ExhibitName
            {"cols": ["MuseumID", "ExhibitName"], "label": "Exhibit", "type": "fk",
             "lookup": LOOKUP_EXHIBIT, "required": True},
            {"cols": ["CategoryID"], "label": "Category", "type": "fk",
             "lookup": LOOKUP_CATEGORY, "required": True},
        ],
    },
    {
        "table": "app_user",
        "label": "Users",
        "pk": ["UserID"],
        "order_by": "`UserID`",
        # the stored hash is not worth showing in the row list
        "hidden_cols": ["PasswordHash"],
        "fields": [
            {"cols": ["UserID"], "label": "User ID", "type": "auto"},
            {"cols": ["Username"], "label": "Username", "type": "text",
             "required": True},
            {"cols": ["Email"], "label": "Email", "type": "text", "required": True},
            {"cols": ["PasswordHash"], "label": "Password", "type": "password",
             "required": True, "sql_expr": "SHA2(%s, 256)"},
            {"cols": ["Role"], "label": "Role", "type": "choice",
             "choices": ["member", "admin"], "required": True},
        ],
    },
    {
        "table": "visit",
        "label": "Visits",
        "pk": ["VisitID"],
        "order_by": "`VisitID`",
        "fields": [
            {"cols": ["VisitID"], "label": "Visit ID", "type": "auto"},
            {"cols": ["VisitDate"], "label": "Visit Date", "type": "date",
             "required": True},
            {"cols": ["UserID"], "label": "User", "type": "fk",
             "lookup": LOOKUP_USER, "required": True},
            {"cols": ["MuseumID"], "label": "Museum", "type": "fk",
             "lookup": LOOKUP_MUSEUM, "required": True},
            {"cols": ["Notes"], "label": "Notes", "type": "multiline"},
        ],
    },
    {
        "table": "review",
        "label": "Reviews",
        "pk": ["ReviewID"],
        "order_by": "`ReviewID`",
        "fields": [
            {"cols": ["ReviewID"], "label": "Review ID", "type": "auto"},
            {"cols": ["Rating"], "label": "Rating (1-5)", "type": "choice",
             "choices": ["1", "2", "3", "4", "5"], "required": True},
            {"cols": ["ReviewDate"], "label": "Review Date", "type": "date",
             "required": True},
            {"cols": ["UserID"], "label": "User", "type": "fk",
             "lookup": LOOKUP_USER, "required": True},
            {"cols": ["MuseumID"], "label": "Museum", "type": "fk",
             "lookup": LOOKUP_MUSEUM, "required": True},
            {"cols": ["Comment"], "label": "Comment", "type": "multiline"},
        ],
    },
    {
        # M:N table between users and artifacts - key is both columns
        "table": "must_see",
        "label": "Must-See List",
        "pk": ["UserID", "ArtifactID"],
        "order_by": "`UserID`, `ArtifactID`",
        "fields": [
            {"cols": ["UserID"], "label": "User", "type": "fk",
             "lookup": LOOKUP_USER, "required": True},
            {"cols": ["ArtifactID"], "label": "Artifact", "type": "fk",
             "lookup": LOOKUP_ARTIFACT, "required": True},
            {"cols": ["DateAdded"], "label": "Date Added", "type": "date",
             "required": True},
        ],
    },
]


# --------------------------------------------------------------------------
# The three aggregate queries
# --------------------------------------------------------------------------
AGGREGATES = [
    {
        "name": "1. AVG - Average rating per museum",
        "desc": "AVG(), COUNT(), MIN() and MAX() with GROUP BY and HAVING.",
        "sql": """
SELECT  m.`Name`                    AS Museum,
        COUNT(r.`ReviewID`)         AS ReviewCount,
        ROUND(AVG(r.`Rating`), 2)   AS AvgRating,
        MIN(r.`Rating`)             AS LowestRating,
        MAX(r.`Rating`)             AS HighestRating
FROM    `museum` m
JOIN    `review` r ON r.`MuseumID` = m.`MuseumID`
GROUP BY m.`MuseumID`, m.`Name`
HAVING  COUNT(r.`ReviewID`) > 0
ORDER BY AvgRating DESC, ReviewCount DESC
""",
    },
    {
        "name": "2. COUNT - Artifacts held per category",
        "desc": "COUNT() with GROUP BY over the ARTIFACT / CATEGORY join.",
        "sql": """
SELECT  c.`Name`                AS Category,
        COUNT(a.`ArtifactID`)   AS ArtifactCount,
        MIN(a.`Year`)           AS EarliestYear,
        MAX(a.`Year`)           AS LatestYear
FROM    `category` c
LEFT JOIN `artifact` a ON a.`CategoryID` = c.`CategoryID`
GROUP BY c.`CategoryID`, c.`Name`
ORDER BY ArtifactCount DESC, Category
""",
    },
    {
        "name": "3. SUM - Visit activity per user",
        "desc": "COUNT(), COUNT(DISTINCT ...) and SUM() with a CASE expression.",
        "sql": """
SELECT  u.`Username`                                             AS User,
        COUNT(v.`VisitID`)                                       AS TotalVisits,
        COUNT(DISTINCT v.`MuseumID`)                             AS DistinctMuseums,
        SUM(CASE WHEN v.`Notes` IS NOT NULL THEN 1 ELSE 0 END)   AS VisitsWithNotes
FROM    `app_user` u
JOIN    `visit` v ON v.`UserID` = u.`UserID`
GROUP BY u.`UserID`, u.`Username`
ORDER BY TotalVisits DESC, User
""",
    },
]


# --------------------------------------------------------------------------
# The first screen: ask for the MySQL login and try to connect
# --------------------------------------------------------------------------
class LoginFrame(ttk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master, padding=24)
        self.on_success = on_success
        self.db = Database()

        ttk.Label(self, text="ExploreDC", font=("Helvetica", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(self, text="Connect to the MySQL database").grid(
            row=1, column=0, columnspan=2, pady=(0, 16))

        self.vars = {}
        for i, (label, key, default) in enumerate([
            ("Host", "host", os.environ.get("MYSQL_HOST", "localhost")),
            ("User", "user", os.environ.get("MYSQL_USER", "root")),
            ("Password", "password", os.environ.get("MYSQL_PASSWORD", "")),
            ("Database", "database", "exploredc"),
        ], start=2):
            ttk.Label(self, text=label + ":").grid(row=i, column=0, sticky="e",
                                                   pady=4, padx=(0, 8))
            var = tk.StringVar(value=default)
            ttk.Entry(self, textvariable=var, width=28,
                      show="*" if key == "password" else "").grid(
                row=i, column=1, sticky="w", pady=4)
            self.vars[key] = var

        self.status = ttk.Label(self, text="", foreground="#b00020", wraplength=320)
        self.status.grid(row=6, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(self, text="Connect", command=self.attempt).grid(
            row=7, column=0, columnspan=2, pady=(16, 0))
        self.bind_all("<Return>", lambda _e: self.attempt())

    def attempt(self):
        self.status.config(text="Connecting...", foreground="#555555")
        self.update_idletasks()
        try:
            self.db.connect(self.vars["host"].get().strip(),
                            self.vars["user"].get().strip(),
                            self.vars["password"].get(),
                            self.vars["database"].get().strip())
        except mysql.connector.Error as err:
            self.status.config(text=f"Connection failed: {err.msg}",
                               foreground="#b00020")
            return
        self.unbind_all("<Return>")
        self.on_success(self.db)


# --------------------------------------------------------------------------
# One tab per table: a list of the rows on top, a form underneath, and the
# Insert / Update / Delete buttons at the bottom.
# --------------------------------------------------------------------------
class CrudTab(ttk.Frame):
    def __init__(self, master, db, spec, app):
        super().__init__(master, padding=10)
        self.db, self.spec, self.app = db, spec, app
        self.table = spec["table"]
        self.pk = spec["pk"]
        self.selected_pk = None
        self.widgets = {}
        self.fk_rows = {}

        self._build_table_view()
        self._build_form()
        self.refresh()

    # ---- layout -----------------------------------------------------------
    def _build_table_view(self):
        top = ttk.LabelFrame(self, text=f"Table: {self.table}", padding=6)
        top.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(top, show="headings", height=11, selectmode="browse")
        vsb = ttk.Scrollbar(top, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(top, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.count_label = ttk.Label(top, text="")
        self.count_label.grid(row=2, column=0, sticky="w", pady=(6, 0))

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Record details", padding=10)
        form.pack(fill="x", pady=(10, 0))

        col = row = 0
        per_col = (len(self.spec["fields"]) + 1) // 2
        for field in self.spec["fields"]:
            key = self._key(field)
            ftype = field["type"]

            # each field uses 3 grid columns: label, input box, grey hint
            ttk.Label(form, text=field["label"] + ":").grid(
                row=row, column=col * 3,
                sticky="ne" if ftype == "multiline" else "e",
                padx=(24 if col else 0, 6), pady=4)

            if ftype == "multiline":
                w = tk.Text(form, width=32, height=3, wrap="word",
                            font=("Helvetica", 11))
            elif ftype == "fk":
                w = ttk.Combobox(form, width=30, state="readonly")
            elif ftype == "choice":
                w = ttk.Combobox(form, width=30, state="readonly",
                                 values=field["choices"])
            elif ftype == "password":
                w = ttk.Entry(form, width=33, show="*")
            elif ftype == "auto":
                w = ttk.Entry(form, width=33, state="readonly")
            else:
                w = ttk.Entry(form, width=33)
            w.grid(row=row, column=col * 3 + 1, sticky="w", pady=4)
            self.widgets[key] = w

            hint = {"date": "YYYY-MM-DD",
                    "auto": "auto (assigned by MySQL)",
                    "password": "stored as a SHA2-256 hash"}.get(ftype)
            if hint:
                ttk.Label(form, text=hint, foreground="#777777").grid(
                    row=row, column=col * 3 + 2, sticky="w", padx=(8, 0))

            row += 1
            if row >= per_col and col == 0:
                col, row = 1, 0

        btns = ttk.Frame(self, padding=(0, 10, 0, 0))
        btns.pack(fill="x")
        ttk.Button(btns, text="Insert", command=self.do_insert).pack(side="left")
        ttk.Button(btns, text="Update", command=self.do_update).pack(side="left", padx=6)
        ttk.Button(btns, text="Delete", command=self.do_delete).pack(side="left")
        ttk.Button(btns, text="Clear form", command=self.clear_form).pack(side="left", padx=6)
        ttk.Button(btns, text="Refresh", command=self.refresh).pack(side="left")
        self.msg = ttk.Label(btns, text="", wraplength=480)
        self.msg.pack(side="left", padx=16)

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def _key(field):
        return "|".join(field["cols"])

    def say(self, text, ok=True):
        self.msg.config(text=text, foreground="#1a7f37" if ok else "#b00020")
        self.app.set_status(text)

    # ---- load----------------------------------------------------------
    def refresh(self):
        """Reload the dropdowns and the row list from the database."""
        for field in self.spec["fields"]:
            if field["type"] == "fk":
                key = self._key(field)
                _c, rows = self.db.query(field["lookup"])
                self.fk_rows[key] = [tuple(r[1:]) for r in rows]
                self.widgets[key]["values"] = [str(r[0]) for r in rows]

        cols, rows = self.db.query(
            f"SELECT * FROM `{self.table}` ORDER BY {self.spec['order_by']}")
        hidden = set(self.spec.get("hidden_cols", []))
        shown = [c for c in cols if c not in hidden]

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = shown
        widths = {"Description": 300, "Comment": 300, "Notes": 260, "Name": 260,
                  "Title": 260, "Address": 280, "ExhibitName": 240,
                  "Location": 180, "Creator": 180, "Email": 200, "Username": 140}
        for c in shown:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 100), anchor="w", stretch=False)

        self._rows_by_iid = {}
        for r in rows:
            record = dict(zip(cols, r))
            values = []
            for c in shown:
                v = "" if record[c] is None else str(record[c])
                values.append(v if len(v) <= 60 else v[:57] + "...")
            iid = "\x1f".join(str(record[k]) for k in self.pk)
            self.tree.insert("", "end", iid=iid, values=values)
            self._rows_by_iid[iid] = record

        self.count_label.config(text=f"{len(rows)} row(s) in {self.table}")

    # ---- form -----------------------------------------------------
    def _on_select(self, _event=None):
        """Clicking a row copies it into the form so it can be edited."""
        sel = self.tree.selection()
        if not sel:
            return
        record = self._rows_by_iid.get(sel[0])
        if record is None:
            return
        self.selected_pk = [record[k] for k in self.pk]

        for field in self.spec["fields"]:
            key = self._key(field)
            w = self.widgets[key]
            ftype = field["type"]

            if ftype == "fk":
                target = tuple(record[c] for c in field["cols"])
                try:
                    w.current(self.fk_rows[key].index(target))
                except ValueError:
                    w.set("")
            elif ftype == "password":
                w.delete(0, "end")      # leave blank - never show the hash
            elif ftype == "multiline":
                w.delete("1.0", "end")
                val = record[field["cols"][0]]
                w.insert("1.0", "" if val is None else str(val))
            elif ftype == "choice":
                val = record[field["cols"][0]]
                w.set("" if val is None else str(val))
            else:
                readonly = w.cget("state") == "readonly"
                if readonly:
                    w.config(state="normal")
                w.delete(0, "end")
                val = record[field["cols"][0]]
                w.insert(0, "" if val is None else str(val))
                if readonly:
                    w.config(state="readonly")
        self.say(f"Loaded {self.table} row {self.selected_pk} into the form.")

    def clear_form(self):
        self.selected_pk = None
        self.tree.selection_remove(*self.tree.selection())
        for field in self.spec["fields"]:
            w = self.widgets[self._key(field)]
            if field["type"] == "multiline":
                w.delete("1.0", "end")
            elif field["type"] in ("fk", "choice"):
                w.set("")
            else:
                readonly = w.cget("state") == "readonly"
                if readonly:
                    w.config(state="normal")
                w.delete(0, "end")
                if readonly:
                    w.config(state="readonly")
        self.msg.config(text="")

    def read_form(self, for_update=False):
        """Read the form into {column: (sql_snippet, value)}, checking it first.
        The password column uses SHA2(%s, 256) so MySQL does the hashing.
        """
        out = {}
        for field in self.spec["fields"]:
            key = self._key(field)
            w = self.widgets[key]
            ftype, label = field["type"], field["label"]

            if ftype == "auto":
                continue

            if ftype == "fk":
                idx = w.current()
                if idx < 0:
                    if field.get("required"):
                        raise ValidationError(f"'{label}' is required - pick a value.")
                    continue
                for c, v in zip(field["cols"], self.fk_rows[key][idx]):
                    out[c] = ("%s", v)
                continue

            raw = (w.get("1.0", "end") if ftype == "multiline" else w.get()).strip()
            col = field["cols"][0]

            if not raw:
                # leaving the password blank on an update means "keep the old one"
                if ftype == "password" and for_update:
                    continue
                if field.get("required"):
                    raise ValidationError(f"'{label}' is required.")
                out[col] = ("%s", None)
            elif ftype == "int":
                try:
                    val = int(raw)
                except ValueError:
                    raise ValidationError(f"'{label}' must be a whole number.")
                if "min" in field and not (field["min"] <= val <= field["max"]):
                    raise ValidationError(
                        f"'{label}' must be between {field['min']} and {field['max']}.")
                out[col] = ("%s", val)
            elif ftype == "date":
                try:
                    datetime.date.fromisoformat(raw)
                except ValueError:
                    raise ValidationError(f"'{label}' must be a date as YYYY-MM-DD.")
                out[col] = ("%s", raw)
            else:
                out[col] = (field.get("sql_expr", "%s"), raw)
        return out

    # ---- INSERT / UPDATE / DELETE ----------------------------------------
    def do_insert(self):
        try:
            data = self.read_form()
        except ValidationError as e:
            return self.say(str(e), ok=False)

        cols = list(data)
        sql = (f"INSERT INTO `{self.table}` ({', '.join(f'`{c}`' for c in cols)}) "
               f"VALUES ({', '.join(data[c][0] for c in cols)})")
        try:
            self.db.execute(sql, tuple(data[c][1] for c in cols))
        except mysql.connector.Error as err:
            return self.say(f"MySQL rejected the insert - {err.msg}", ok=False)

        self.refresh()
        self.say(f"Inserted 1 row into {self.table}.")

    def do_update(self):
        if self.selected_pk is None:
            return self.say("Select a row in the table above before updating.", ok=False)
        try:
            data = self.read_form(for_update=True)
        except ValidationError as e:
            return self.say(str(e), ok=False)

        assignments = ", ".join(f"`{c}` = {data[c][0]}" for c in data)
        where = " AND ".join(f"`{k}` = %s" for k in self.pk)
        sql = f"UPDATE `{self.table}` SET {assignments} WHERE {where}"
        params = tuple(data[c][1] for c in data) + tuple(self.selected_pk)
        try:
            affected = self.db.execute(sql, params)
        except mysql.connector.Error as err:
            return self.say(f"MySQL rejected the update - {err.msg}", ok=False)

        self.refresh()
        self.say(f"Updated {affected} row in {self.table}." if affected
                 else "No change - submitted values match the stored row.")

    def do_delete(self):
        if self.selected_pk is None:
            return self.say("Select a row in the table above before deleting.", ok=False)
        pk_text = ", ".join(f"{k} = {v}" for k, v in zip(self.pk, self.selected_pk))
        if not messagebox.askyesno(
                "Confirm delete",
                f"Delete this row from {self.table}?\n\n{pk_text}",
                parent=self):
            return

        where = " AND ".join(f"`{k}` = %s" for k in self.pk)
        try:
            affected = self.db.execute(
                f"DELETE FROM `{self.table}` WHERE {where}", tuple(self.selected_pk))
        except mysql.connector.Error as err:
            return self.say(f"MySQL rejected the delete - {err.msg}", ok=False)

        self.clear_form()
        self.refresh()
        self.say(f"Deleted {affected} row from {self.table} ({pk_text}).")


# --------------------------------------------------------------------------
# Reports tab: click one of the three aggregate queries and see results.
# --------------------------------------------------------------------------
class AggregateTab(ttk.Frame):
    def __init__(self, master, db, app):
        super().__init__(master, padding=10)
        self.db, self.app = db, app

        left = ttk.LabelFrame(self, text="Aggregate queries", padding=8)
        left.pack(side="left", fill="y")
        self.listbox = tk.Listbox(left, width=40, height=6, exportselection=False,
                                  font=("Helvetica", 11))
        for a in AGGREGATES:
            self.listbox.insert("end", a["name"])
        self.listbox.pack()
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self.run())
        self.listbox.selection_set(0)
        ttk.Button(left, text="Run query", command=self.run).pack(pady=(8, 0), fill="x")

        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.desc = ttk.Label(right, text="", wraplength=620, justify="left")
        self.desc.pack(fill="x", pady=(0, 6))

        resbox = ttk.LabelFrame(right, text="Result", padding=4)
        resbox.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(resbox, show="headings", height=18)
        vsb = ttk.Scrollbar(resbox, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.run()

    def run(self):
        sel = self.listbox.curselection()
        agg = AGGREGATES[sel[0] if sel else 0]
        self.desc.config(text=agg["desc"])

        try:
            cols, rows = self.db.query(agg["sql"])
        except mysql.connector.Error as err:
            messagebox.showerror("Query failed", err.msg, parent=self)
            return

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=max(120, min(240, len(c) * 14)), anchor="w")
        for r in rows:
            self.tree.insert("", "end",
                             values=["" if v is None else str(v) for v in r])
        self.app.set_status(f"{agg['name']} - {len(rows)} row(s) returned.")


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.db = None
        self.tabs = []
        root.title("ExploreDC - Washington DC Museum Database")

        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=22)
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

        self.login = LoginFrame(root, self.on_connected)
        self.login.pack(fill="both", expand=True)

    def on_connected(self, db):
        self.db = db
        self.login.destroy()

        header = ttk.Frame(self.root, padding=(10, 8, 10, 0))
        header.pack(fill="x")
        ttk.Label(header, text="ExploreDC",
                  font=("Helvetica", 16, "bold")).pack(side="left")
        ttk.Label(header,
                  text=f"  connected to MySQL {db.server_info()} / database: exploredc",
                  foreground="#1a7f37").pack(side="left")

        self.nb = ttk.Notebook(self.root, padding=6)
        self.nb.pack(fill="both", expand=True)
        for spec in TABLES:
            tab = CrudTab(self.nb, self.db, spec, self)
            self.nb.add(tab, text=spec["label"])
            self.tabs.append(tab)
        self.nb.add(AggregateTab(self.nb, self.db, self), text="Aggregate Reports")
        # Reload a tab when you switch to it. Otherwise a category you just
        # added wouldn't show up in the Artifacts dropdown until you hit
        # Refresh.
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.status = ttk.Label(self.root, text="Ready.", relief="sunken",
                                anchor="w", padding=4)
        self.status.pack(fill="x", side="bottom")

        self.root.geometry("1180x820")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_tab_changed(self, _event=None):
        current = self.nb.nametowidget(self.nb.select())
        if isinstance(current, CrudTab):
            try:
                current.refresh()
            except mysql.connector.Error:
                pass

    def set_status(self, text):
        if hasattr(self, "status"):
            self.status.config(text=text)

    def on_close(self):
        if self.db:
            self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
