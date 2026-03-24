from __future__ import annotations

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "sptube.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spotify_url TEXT UNIQUE NOT NULL,
            title TEXT,
            artist TEXT,
            youtube_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            song_id INTEGER NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
            UNIQUE(playlist_id, song_id)
        )
    """)
    conn.commit()
    conn.close()


def insert_song(spotify_url: str) -> int | None:
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO songs (spotify_url) VALUES (?)",
            (spotify_url,),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_song(song_id: int, title: str, artist: str, status: str = "scraped"):
    conn = get_db()
    conn.execute(
        "UPDATE songs SET title=?, artist=?, status=? WHERE id=?",
        (title, artist, status, song_id),
    )
    conn.commit()
    conn.close()


def set_youtube_url(song_id: int, youtube_url: str):
    conn = get_db()
    conn.execute(
        "UPDATE songs SET youtube_url=? WHERE id=?",
        (youtube_url, song_id),
    )
    conn.commit()
    conn.close()


def set_song_error(song_id: int, error_msg: str):
    conn = get_db()
    conn.execute(
        "UPDATE songs SET status=?, title=? WHERE id=?",
        ("error", error_msg, song_id),
    )
    conn.commit()
    conn.close()


def get_all_songs():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM songs ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_song(song_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM songs WHERE id=?", (song_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_pending_count():
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM songs WHERE status='pending'"
    ).fetchone()
    conn.close()
    return row["c"]


def clear_all_songs():
    conn = get_db()
    conn.execute("DELETE FROM songs")
    conn.commit()
    conn.close()


def delete_song(song_id: int):
    conn = get_db()
    conn.execute("DELETE FROM playlist_songs WHERE song_id=?", (song_id,))
    conn.execute("DELETE FROM songs WHERE id=?", (song_id,))
    conn.commit()
    conn.close()


def reset_stuck_songs():
    """Reset error/pending songs back to pending for retry."""
    conn = get_db()
    conn.execute("UPDATE songs SET status='pending', title=NULL, artist=NULL WHERE status IN ('error', 'pending')")
    conn.commit()
    conn.close()


# ── Playlist CRUD ──────────────────────────────────────────────────────────


def create_playlist(name: str) -> int:
    conn = get_db()
    cur = conn.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def delete_playlist(playlist_id: int):
    conn = get_db()
    conn.execute("DELETE FROM playlist_songs WHERE playlist_id=?", (playlist_id,))
    conn.execute("DELETE FROM playlists WHERE id=?", (playlist_id,))
    conn.commit()
    conn.close()


def rename_playlist(playlist_id: int, name: str):
    conn = get_db()
    conn.execute("UPDATE playlists SET name=? WHERE id=?", (name, playlist_id))
    conn.commit()
    conn.close()


def get_all_playlists():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id, p.name, p.created_at, COUNT(ps.id) as song_count
        FROM playlists p
        LEFT JOIN playlist_songs ps ON ps.playlist_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_playlist_songs(playlist_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT s.* FROM songs s
        JOIN playlist_songs ps ON ps.song_id = s.id
        WHERE ps.playlist_id = ?
        ORDER BY ps.position, ps.id
    """, (playlist_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_song_to_playlist(playlist_id: int, song_id: int):
    conn = get_db()
    # Get next position
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM playlist_songs WHERE playlist_id=?",
        (playlist_id,)
    ).fetchone()
    pos = row["next_pos"]
    try:
        conn.execute(
            "INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id, position) VALUES (?, ?, ?)",
            (playlist_id, song_id, pos),
        )
        conn.commit()
    finally:
        conn.close()


def remove_song_from_playlist(playlist_id: int, song_id: int):
    conn = get_db()
    conn.execute(
        "DELETE FROM playlist_songs WHERE playlist_id=? AND song_id=?",
        (playlist_id, song_id),
    )
    conn.commit()
    conn.close()


# By JP