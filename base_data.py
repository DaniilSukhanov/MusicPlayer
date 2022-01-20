import sqlite3

import Errors


class BaseDataPlaylists:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def get_id_playlist(self, title_playlist):
        """Получить id плейлиста по названию."""
        if not isinstance(title_playlist, str):
            raise Errors.ErrorWrongTypeObject()
        id_playlist = self.cur.execute(
            """SELECT id FROM playlists WHERE title=(?)""",
            (title_playlist,)
        ).fetchone()
        if id_playlist is None:
            raise Errors.ErrorNoValueFound()
        return id_playlist[0]

    def get_all_songs_of_playlists(self, id_playlist):
        """Получить все песни, которые привязаны к плейлисту."""
        if not isinstance(id_playlist, int):
            raise Errors.ErrorWrongTypeObject()
        songs = self.cur.execute(
            """SELECT title FROM songs WHERE playlist=(?)""",
            (id_playlist,)
        ).fetchall()
        if not songs:
            raise Errors.ErrorNoValueFound()
        return tuple(map(lambda element: element[0], songs))

    def add_song(self, title_song, id_playlist):
        """Добавить песню в базу данных."""
        if not isinstance(title_song, str) or not isinstance(id_playlist, int):
            raise Errors.ErrorWrongTypeObject()
        self.cur.execute(
            """INSERT INTO songs (title, playlist) VALUES (?, ?)""",
            (title_song, id_playlist)
        )
        self.con.commit()

    def add_playlist(self, title_playlist):
        """Добавить плейлист в базу данных."""
        if not isinstance(title_playlist, str):
            raise Errors.ErrorWrongTypeObject()
        self.cur.execute(
            """INSERT INTO playlists (title) VALUES (?)""",
            (title_playlist,)
        )
        self.con.commit()

    def get_all_playlists(self):
        """Получить все существующие плейлисты."""
        playlists = self.cur.execute(
            """SELECT title FROM playlists"""
        )
        playlists = tuple(map(lambda element: str(element[0]), playlists))
        return playlists

    def delete_playlist(self, id_playlist):
        """Удаляет плейлист, а также все песни, котороые были привязаные."""
        if not isinstance(id_playlist, int):
            raise Errors.ErrorWrongTypeObject()
        self.cur.execute(
            """DELETE FROM playlists WHERE id=(?)""",
            (id_playlist,)
        )
        self.cur.execute(
            """DELETE FROM songs WHERE playlist=(?)""",
            (id_playlist,)
        )
        self.con.commit()

    def check_playlist_for_existence(self, id_playlist):
        """Проверяет на существования плейлиста."""
        if not isinstance(id_playlist, int):
            raise Errors.ErrorWrongTypeObject()
        result = self.cur.execute(
            """SELECT id FROM playlists WHERE id=(?)""",
            (id_playlist,)
        ).fetchone()
        if result is None:
            raise Errors.ErrorNoValueFound()
