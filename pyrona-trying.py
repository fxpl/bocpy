#!/usr/bin/env python3

import sqlite3
from bocpy import Cown
from immutable import TracingRegion as Region
from immutable import set_freezable, FREEZABLE_YES
import collections

def setup():
    set_freezable(collections._tuplegetter, FREEZABLE_YES)

def main():
    setup()

    c = Cown()

    with c:
        c.value = Region()
        c.value.db = sqlite3.connect("ducks.db")

    r = c.unwrap()
    print(r)
    print(r.db)

def baseline():
    conn = sqlite3.connect("example.db")

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)

        conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        conn.commit()

        for row in conn.execute("SELECT id, name FROM users ORDER BY id"):
            print(row)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
