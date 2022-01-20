import sys
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, \
    QLineEdit, QToolButton, QDialog, QWidget
from PyQt5.QtCore import QUrl, Qt

import Errors
import my_search_site
import base_data

from design.main_window import Ui_MainWindow
from design.dialog_function_song import Ui_Dialog as \
    Ui_Dialog_function_song
from design.dialog_confirm import Ui_Dialog as Ui_Dialog_confirm
from design.dialog_create_playlist import Ui_Dialog as \
    Ui_Dialog_create_playlist
from design.dialog_function_playlist import Ui_Dialog as \
    Ui_Dialog_function_playlist
from design.download_song import Ui_Form as Ui_From_download_song
from design.song_add_in_playlist import Ui_Dialog as \
    Ui_Dialog_song_add_in_playlist


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # плейер.
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.next_media_auto)

        # Очередь песень и история.
        self.queue = ListMusic()

        # Перемещение слайдера с музыкой.
        self.player.positionChanged.connect(self.update_slider)
        # Настрой максимального значения
        self.player.durationChanged.connect(self.setting_slider)

        # Нажатие\опускание ползунка.
        self.slider_change = False
        self.horizontalSlider_duration.sliderReleased.connect(
            self.set_position_song
        )
        self.horizontalSlider_duration.sliderPressed.connect(
            self.set_slider_change
        )

        # Кнопка пауза\играть
        self.pause = False
        self.pushButton_pause_and_play.clicked.connect(self.play_and_pause)

        # Кнопки далее\назад
        self.pushButton_next.clicked.connect(self.next_media)
        self.pushButton_back.clicked.connect(self.back_media)

        # Поиск
        self.lineEdit_search.textEdited.connect(self.media_library_search)

        # Изменение звука
        value = 50
        self.verticalSlider_volume_sound.setValue(value)
        self.set_volume(value)
        self.verticalSlider_volume_sound.sliderMoved.connect(self.set_volume)

        # Добавление песеню в плейлист
        self.pushButton_add_playlist.clicked.connect(
            self.open_dialog_create_playlist
        )

        # Кнопка для скачивания песень.
        self.pushButton_add_song.clicked.connect(self.download_song)

        # база данных (base data) для плейлистов.
        self.bd = base_data.BaseDataPlaylists(
            'base data/music/playlists.sqlite'
        )

    def update_player(self, skip_check_position=False):
        """Обновляет плейер."""
        current_media = self.queue.get_current_media()
        # Если есть медиа-контент.
        try:
            if current_media is not None:
                url_media = current_media.canonicalUrl()
                # Пропучкаем не существующий контент.
                while not os.path.isfile(url_media.path()):
                    self.queue.remove_media_content(current_media)
                    self.queue.next_media_content()
                    self.update_queue_in_scroll_area()
                    self.update_songs_in_scroll_area()
                    current_media = self.queue.get_current_media()
                    url_media = current_media.canonicalUrl()
                # Обновляем, если песня не производится в данный момент.
                if not self.player.position() or skip_check_position:
                    self.label_name_song.setText(turn_into_a_name(
                        url_media.fileName())
                    )
                    self.player.setMedia(current_media)
                    # Играем, если нет паузы.
                    if not self.pause:
                        self.player.play()
            else:
                self.player.stop()
                self.label_name_song.setText('Ничего не играет')
        except Errors.ErrorEmptyQueue:
            self.statusbar.showMessage(
                f'Не удалось воспроизвести.', 5000
            )

    def download_song(self):
        """Открывает виджет для скачивания песнень."""
        self.widget = WidgetAddSong()
        self.widget.show()

    def play_playlist(self):
        """Проигрывает все песни из playlist."""
        playlist_name = self.sender().get_name()
        try:
            # получаем список песень в плейлисте.
            id_playlist = self.bd.get_id_playlist(playlist_name)
            data_playlist = self.bd.get_all_songs_of_playlists(id_playlist)
            # очищаем очередь.
            self.queue.clear()
            # заполняем очередь полученным списком из плейлиста
            for song in data_playlist:
                self.queue.add_media_content(QMediaContent(
                    QUrl.fromLocalFile(f'base data/music/songs/{song}')))
            # обновляем и проигрываем
            self.update_queue_in_scroll_area()
            self.update_player(True)
        except Errors.ErrorNoValueFound:
            self.statusbar.showMessage(
                f"В плейлисте \"{playlist_name}\" нет песень.",
                5000
            )

    def open_dialog_functions_playlist(self):
        """Окрывает диалог с функциями для playlist."""
        playlist_name = self.sender().get_name()
        dialog = DialogFunctionsPlaylist()
        dialog.show()
        result = dialog.exec_()
        if result:
            # получаем результат нажатия (какая кнопка была нажата).
            result = dialog.result_value
            # Получаем данные.
            id_playlist = self.bd.get_id_playlist(playlist_name)
            try:
                songs = self.bd.get_all_songs_of_playlists(id_playlist)
            except Errors.ErrorNoValueFound:
                if result not in {
                    dialog.pushButton_delete, dialog.pushButton_edit
                }:
                    self.statusbar.showMessage(
                        f"В плейлисте \"{playlist_name}\" нет песень."
                    )
                    return

            # если кнопка "удалить".
            if result == dialog.pushButton_delete:
                dialog_confirm = DialogConfirm()
                dialog_confirm.show()
                # ждем ответа, точно ли пользоатель хочет удалить
                result = dialog_confirm.exec_()
                if result:
                    # удаление плейлиста.
                    self.bd.delete_playlist(id_playlist)
                    self.update_player()
            # если кнопка "редактировать".
            elif result == dialog.pushButton_edit:
                dialog = DialogCreatePlaylist(
                    get_name_songs_download(),
                    self.bd,
                    playlist_name,
                    recreation=True
                )
                dialog.show()
                result = dialog.exec_()
                if result:
                    # Удаляем старый.
                    self.bd.delete_playlist(id_playlist)
                    data_playlist = dialog.playlist
                    name_playlist = dialog.name
                    self.bd.add_playlist(name_playlist)
                    id_playlist = self.bd.get_id_playlist(name_playlist)
                    # создаем новый.
                    for i in range(data_playlist.mediaCount()):
                        name_song = data_playlist.media(i)\
                            .canonicalUrl().fileName()
                        self.bd.add_song(name_song, id_playlist)
                    self.update_playlist_in_scroll_area()
            # если кнопка "добавить в конец очереди".
            elif result == dialog.pushButton_add_end:
                # получаем текущую песню.
                old_current_media = self.queue.get_current_media()
                # добавляем в очередь.
                for song in songs:
                    self.queue.add_media_content(QMediaContent(
                        QUrl.fromLocalFile(f'base data/music/songs/{song}')))
                # если изночально очередь была пустой,
                # то начинаем проигрывать очередь.
                if old_current_media is None:
                    self.update_player()
            # если кнопка "добавить в начало очереди".
            elif result == dialog.pushButton_add_next:
                # вставляем в начало очереди.
                for song in songs:
                    self.queue.insert_media_content(QMediaContent(
                        QUrl.fromLocalFile(
                            f'base data/music/songs/{song}')), 0
                    )
                self.update_player()
            # обновляем очередь и плейлист.
            self.update_playlist_in_scroll_area()
            self.update_queue_in_scroll_area()

    def delete_song(self):
        """Удаляет песню с очереди."""
        row = self.sender().get_row()
        self.queue.delete_media_content(row)
        self.update_queue_in_scroll_area()

    def update_playlist_in_scroll_area(self):
        """Обновляет layout с playlists."""
        clear_grid_layout(self.gridLayout_playlists)
        for i, playlist_name in enumerate(
                sorted(self.bd.get_all_playlists())):
            add_element_template(
                self, self.gridLayout_playlists, i, playlist_name,
                type_file=QMediaPlaylist, transformation_name=False
            )

    def open_dialog_create_playlist(self):
        """Открывает диалог создание playlist, который будет сохранен."""
        dialog = DialogCreatePlaylist(
            get_name_songs_download(),
            self.bd
        )
        dialog.show()
        result = dialog.exec_()
        if result:
            # песени, которые находятся в плейлисте.
            playlist = dialog.playlist
            # заполняем файл названиями песень.
            data_playlist = dialog.playlist
            name_playlist = dialog.name
            self.bd.add_playlist(name_playlist)
            id_playlist = self.bd.get_id_playlist(name_playlist)
            # создаем новый.
            for i in range(data_playlist.mediaCount()):
                name_song = data_playlist.media(i) \
                    .canonicalUrl().fileName()
                self.bd.add_song(name_song, id_playlist)
            self.update_playlist_in_scroll_area()

    def set_volume(self, value):
        """Устанавливает громкость."""
        self.player.setVolume(value)

    def open_dialog_functions_song(self):
        """Открывает диалог функций для песни."""
        dialog = DialogFunctionsSong()
        dialog.show()
        result = dialog.exec_()
        if result:
            result = dialog.result_accept
            media_content = QMediaContent(QUrl.fromLocalFile(
                f'base data/music/songs/{self.sender().get_name()}'
            ))
            # если кнопка "добавить в начало".
            if result == dialog.pushButton_add_next:
                self.queue.insert_media_content(media_content, 0)
                try:
                    self.update_player()
                except Errors.ErrorEmptyQueue:
                    self.statusbar.showMessage(
                        f'песню "{self.sender().get_name()}"'
                        f' не удалось воспроизвести',
                        5000
                    )
            # если кнопка "добавить в конец".
            elif result == dialog.pushButton_add_end:
                self.queue.add_media_content(media_content)
                self.update_player()
            # если кнопка "добавить в плейлист".
            elif result == dialog.pushButton_add_playlist:
                dialog = DialogSongAddInPlaylist(
                    self.sender().get_name(),
                    self.bd
                )
                dialog.show()
                _ = dialog.exec_()
            # если кнопка "удалить".
            elif result == dialog.pushButton_delete:
                dialog_confirm = DialogConfirm()
                dialog_confirm.show()
                result = dialog_confirm.exec_()
                if result:
                    self.queue.remove_media_content(
                        QMediaContent(
                            QUrl.fromLocalFile(
                                f'base data/music/songs/'
                                f'{self.sender().get_name()}'
                            )
                        )
                    )
                    os.remove(
                        f'base data/music/songs/'
                        f'{self.sender().get_name()}')
                    self.update_songs_in_scroll_area()
                    self.media_library_search()
                    self.next_media()
                    self.update_player()
            self.update_queue_in_scroll_area()

    def next_media_auto(self, state):
        """Переключает на следующую песню
         после того как предыдущая закончилась."""
        if state == QMediaPlayer.EndOfMedia:
            self.next_media()

    def next_media(self):
        """Переключить на следующую песню."""
        try:
            self.queue.next_media_content()
            self.update_player(True)
            self.update_queue_in_scroll_area()
        except Errors.ErrorEmptyQueue:
            self.statusbar.showMessage('В очереди ничего нет.', 5000)

    def back_media(self):
        """Вернуться к прошлой песне."""
        self.queue.back_media_content()
        self.update_player(True)
        self.update_queue_in_scroll_area()

    def play_and_pause(self):
        """ставит на пауза/играет песню."""
        if self.pause:
            self.pushButton_pause_and_play.setIcon(
                QIcon('images/button_play.png'))
            self.player.play()
        else:
            self.pushButton_pause_and_play.setIcon(
                QIcon('images/button_pause.png'))
            self.player.pause()
        self.pause = not self.pause

    def set_position_song(self):
        """Ставит песню в позицию, в которой стоит ползунок."""
        position = self.horizontalSlider_duration.sliderPosition()
        self.player.setPosition(position)
        self.set_slider_change()

    def set_slider_change(self):
        """Ставит музыку на стоп, когда меняется позиция ползунка."""
        if not self.slider_change:
            self.player.pause()
        else:
            if not self.pause:
                self.player.play()
        self.slider_change = not self.slider_change

    def media_library_search(self):
        """Поиск по загруженным песням."""
        song_name_search = self.lineEdit_search.text().lower()
        # Очистка
        clear_grid_layout(self.gridLayout_search)
        if song_name_search:
            # Все совпадение с song_name_search
            search_data = sorted(
                filter(
                    lambda name_song: song_name_search in name_song.lower(),
                    get_name_songs_download()
                ),
                key=lambda element: element.find(song_name_search)
            )
            # Заполнение gridLayout_search
            for i, name_song in enumerate(search_data):
                add_element_template(self, self.gridLayout_search, i,
                                     name_song)

    def update_songs_in_scroll_area(self):
        """Обновляет список песнь."""
        clear_grid_layout(self.gridLayout_songs)
        for i, song_name in sorted(enumerate(get_name_songs_download()),
                                   key=lambda element: element[1]):
            add_element_template(self, self.gridLayout_songs, i, song_name)

    def play_song(self):
        """Проигрывает песень."""
        file_name = self.sender().get_name()
        place_call = self.sender().get_place_call()
        row_place_call = self.sender().get_row()
        col_place_call = self.sender().get_column()
        # если кнопка была нажата из gridLayout_songs.
        if place_call == self.gridLayout_songs:
            # Очищаем очередь.
            self.queue.clear()
            # Очищаем layout очереди.
            clear_grid_layout(self.gridLayout_queue)
            # ставим текущую мелодию.
            self.queue.add_media_content(
                QMediaContent(
                    QUrl.fromLocalFile(f'base data/music/songs/{file_name}'))
            )
            for i in range(
                    row_place_call + 1,
                    self.gridLayout_songs.rowCount()
            ):
                object_qt = self.gridLayout_songs.itemAtPosition(
                    i, col_place_call
                )
                if object_qt is None:
                    continue
                name = object_qt.widget().get_name()
                self.queue.add_media_content(
                    QMediaContent(
                        QUrl.fromLocalFile(f'base data/music/songs/{name}'))
                )
            # Добавляем песни, которые идут с начало очереди
            # и до текущей песни (не включительно).
            for i in range(row_place_call):
                name = self.gridLayout_songs.itemAtPosition(
                    i, col_place_call
                ).widget().get_name()
                self.queue.add_media_content(
                    QMediaContent(
                        QUrl.fromLocalFile(f'base data/music/songs/{name}'))
                )
        # если кнопка была нажата из gridLayout_search.
        elif place_call == self.gridLayout_search:
            # Очищаем layout очереди.
            clear_grid_layout(self.gridLayout_queue)
            # Очищаем очередь.
            self.queue.clear()
            # Добавляем текущую песни.
            self.queue.add_media_content(
                QMediaContent(
                    QUrl.fromLocalFile(f'base data/music/songs/{file_name}'))
            )
        # если кнопка была нажата из gridLayout_queue.
        elif place_call == self.gridLayout_queue:
            small_queue = self.queue.get_queue()[row_place_call:]
            # Очищаем очередь.
            self.queue.clear()
            for media in small_queue:
                self.queue.add_media_content(
                    QMediaContent(
                        QUrl.fromLocalFile(
                            f'base data/music/songs/'
                            f'{media.canonicalUrl().fileName()}'))
                )
            clear_grid_layout(self.gridLayout_queue)
        for i, media_content in enumerate(self.queue.get_queue()):
            add_element_template(
                self, self.gridLayout_queue, i,
                media_content.canonicalUrl().fileName(), numbering=True
            )
        self.update_player(True)

    def update_slider(self, position):
        """Перемещает ползунок длительности в position."""
        if not self.slider_change:
            self.horizontalSlider_duration.setSliderPosition(position)

    def setting_slider(self, duration):
        """Изменение параметров ползунка длительности."""
        if duration:
            self.horizontalSlider_duration.setMaximum(duration)

    def move_media_queue(self):
        """Перемещает медиа по очереди."""
        new_index = int(self.sender().text()) - 1
        old_index = self.sender().get_row()
        self.queue.move_media_content(old_index, new_index)
        self.update_queue_in_scroll_area()

    def update_queue_in_scroll_area(self):
        """Обновляет список песнь."""
        list_music = tuple(
            map(
                lambda element: element.canonicalUrl().fileName(),
                self.queue.get_queue()
            )
        )
        clear_grid_layout(self.gridLayout_queue)
        for i, song_name in enumerate(list_music):
            add_element_template(self, self.gridLayout_queue, i, song_name,
                                 numbering=True, delete=True)


class WidgetAddSong(QWidget, Ui_From_download_song):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.search = my_search_site.Search()
        self.pushButton_search.clicked.connect(self.result_search_site)

    def keyPressEvent(self, event):
        """Обработка нажатия кнопки "ввод"."""
        if event.key() == Qt.Key_Return:
            self.result_search_site()

    def add_song(self):
        """Скачивает песню."""
        sender_object = self.sender()
        my_search_site.download(sender_object.get_href(),
                                sender_object.get_name())
        self.label_error.setText(
            f'Песня "{sender_object.get_name()}" скачена!')
        mw.update_songs_in_scroll_area()

    def result_search_site(self):
        """Отображяет результат поиска по сайту."""
        try:
            clear_grid_layout(self.gridLayout_search)
            for i, (title_song, href_song) in enumerate(
                    self.search.search(self.lineEdit_search.text())):
                add_element_template(self, self.gridLayout_search, i,
                                     title_song, href_object=href_song,
                                     play=False,
                                     tool_button=False, add=True,
                                     transformation_name=False)
            self.label_error.clear()
        except Errors.ErrorCouldNotFind:
            self.label_error.setText('Ничего не найдено!')


class DialogSongAddInPlaylist(QDialog, Ui_Dialog_song_add_in_playlist):
    def __init__(self, added_song, sqlite_base_data):
        super(QDialog, self).__init__()
        super(Ui_Dialog_song_add_in_playlist, self).__init__()
        self.setupUi(self)
        self.bd = sqlite_base_data
        self.added_song = added_song
        self.playlist_name = None
        list_playlist = sorted(self.bd.get_all_playlists())
        for i, playlist_name in enumerate(list_playlist):
            add_element_template(self, self.gridLayout, i, playlist_name,
                                 play=False, tool_button=False, add=True)

    def add_song(self):
        """Добавляет песню в плейлист."""
        name_playlist = self.sender().get_name()
        id_playlist = self.bd.get_id_playlist(name_playlist)
        self.bd.add_song(self.added_song, id_playlist)
        self.accept()


class DialogFunctionsPlaylist(QDialog, Ui_Dialog_function_playlist):
    def __init__(self):
        super(QDialog, self).__init__()
        super(Ui_Dialog_function_playlist, self).__init__()
        self.setupUi(self)
        self.result_value = None
        self.pushButton_delete.clicked.connect(self.accept_result)
        self.pushButton_edit.clicked.connect(self.accept_result)
        self.pushButton_add_next.clicked.connect(self.accept_result)
        self.pushButton_add_end.clicked.connect(self.accept_result)

    def accept_result(self):
        self.result_value = self.sender()
        self.accept()


class DialogCreatePlaylist(QDialog, Ui_Dialog_create_playlist):
    def __init__(
            self, songs, sqlite_base_data, old_file_name=None,
            recreation=False
    ):
        super(QDialog, self).__init__()
        super(Ui_Dialog_create_playlist, self).__init__()
        self.setupUi(self)
        self.lineEdit_search.textChanged.connect(self.media_library_search)
        self.pushButton_create.clicked.connect(self.accept_dialog)
        self.playlist = QMediaPlaylist()
        self.bd = sqlite_base_data
        self.name = None
        self.recreation = recreation
        self.songs = sorted(songs)
        self.fulling_search()
        # если есть старое имя, то передаем все данные в новый плейлист.
        if old_file_name is not None:
            self.name = old_file_name
            id_playlist = self.bd.get_id_playlist(self.name)
            try:
                songs = self.bd.get_all_songs_of_playlists(id_playlist)
            except Errors.ErrorNoValueFound:
                songs = []
            for song in songs:
                self.playlist.addMedia(QMediaContent(
                    QUrl.fromLocalFile(f'base data/music/songs/{song}')))
            self.lineEdit_name.setText(self.name)
            self.update_added_songs()

    def accept_dialog(self):
        """Создание playlist."""
        name = self.lineEdit_name.text()
        try:
            if not name.replace(' ', ''):
                raise Errors.ErrorInvalidName()
            playlists = self.bd.get_all_playlists()
            if name in playlists and not self.recreation:
                raise Errors.ErrorCopyName()
            self.name = name
            self.accept()
        except Errors.ErrorInvalidName:
            self.label_error.setText(f'Имя плейлиста "{name}" некорректно.')
        except Errors.ErrorCopyName:
            self.label_error.setText(f'Плейлист "{name}" уже существует.')

    def delete_song(self):
        """Удаляет песню из playlist."""
        row = self.sender().get_row()
        self.playlist.removeMedia(row)
        self.update_added_songs()

    def media_library_search(self):
        """Поиск по загруженным песням."""
        song_name_search = self.lineEdit_search.text().lower()
        # Очистка
        clear_grid_layout(self.gridLayout_search)
        if song_name_search:
            # Все совпадение с song_name_search
            search_data = sorted(
                filter(
                    lambda name_song: song_name_search in name_song.lower(),
                    get_name_songs_download()
                ),
                key=lambda element: element.find(song_name_search)
            )
            # Заполнение gridLayout_search
            for i, name_song in enumerate(search_data):
                add_element_template(self, self.gridLayout_search, i,
                                     name_song, tool_button=False, play=False,
                                     add=True)
        else:
            # заполняем поиск.
            self.fulling_search()

    def add_song(self):
        """Добавление песни в playlist."""
        self.playlist.addMedia(
            QMediaContent(QUrl.fromLocalFile(
                f'base data/music/songs/{self.sender().get_name()}')))
        self.update_added_songs()

    def update_added_songs(self):
        """Обновляет layout с добавленными песнями."""
        clear_grid_layout(self.gridLayout_added_songs)
        for i in range(self.playlist.mediaCount()):
            add_element_template(
                self, self.gridLayout_added_songs, i,
                self.playlist.media(i).canonicalUrl().fileName(),
                play=False, delete=True, tool_button=False
            )

    def fulling_search(self):
        """Заполняет layout поиска всеми загруженнами песнями."""
        for i, song in enumerate(self.songs):
            add_element_template(self, self.gridLayout_search, i, song,
                                 tool_button=False, play=False, add=True)


class DialogFunctionsSong(Ui_Dialog_function_song, QDialog):
    def __init__(self):
        super(Ui_Dialog_function_song, self).__init__()
        super(QDialog, self).__init__()
        self.setupUi(self)
        self.pushButton_add_next.clicked.connect(self.run)
        self.pushButton_add_end.clicked.connect(self.run)
        self.pushButton_add_playlist.clicked.connect(self.run)
        self.pushButton_delete.clicked.connect(self.run)
        self.result_accept = None

    def run(self):
        self.result_accept = self.sender()
        self.accept()


class ListMusic:
    def __init__(self):
        self.play_queue = list()
        self.current_media = None
        self.play_history = list()

    def insert_media_content(self, media_content, index):
        """Вставляет медиа контент в нужное место."""
        if not isinstance(media_content, QMediaContent) or not isinstance(
                index, int):
            raise Errors.ErrorWrongTypeObject()
        if self.current_media is None and (
                self.play_queue and not index or
                not self.play_queue
        ):
            self.current_media = media_content
        else:
            self.play_queue.insert(index, media_content)

    def add_media_playlist(self, media_playlist):
        """Добавляет плейлист в очередь (все песни из него)."""
        if not isinstance(media_playlist, QMediaPlaylist):
            raise Errors.ErrorWrongTypeObject()
        map(
            lambda i: self.play_queue.append(media_playlist.media(i)),
            range(media_playlist.mediaCount())
        )

    def add_media_content(self, media_content):
        """Добавляет контент в очередь."""
        if not isinstance(media_content, QMediaContent):
            raise Errors.ErrorWrongTypeObject()
        if self.current_media is not None:
            self.play_queue.append(media_content)
        else:
            self.current_media = media_content

    def remove_media_content(self, media_content):
        """Удаляет контент из всех данных."""
        if not isinstance(media_content, QMediaContent):
            raise Errors.ErrorWrongTypeObject()
        if media_content in self.play_history:
            for _ in range(self.play_history.count(media_content)):
                self.play_history.remove(media_content)
        if media_content in self.play_queue:
            for _ in range(self.play_queue.count(media_content)):
                self.play_queue.remove(media_content)
        if media_content == self.current_media:
            self.current_media = None

    def delete_media_content(self, index):
        """Удаляет контент из очереди."""
        try:
            del self.play_queue[index]
        except IndexError:
            raise Errors.ErrorGoingAbroad()

    def move_media_content(self, old_index, new_index):
        """Меняет расположение контента в очереди."""
        try:
            media_content = self.play_queue.pop(old_index)
            self.play_queue.insert(new_index, media_content)
        except IndexError:
            raise Errors.ErrorGoingAbroad()

    def next_media_content(self):
        """Переключает на следующий контент."""
        if not self.play_queue:
            raise Errors.ErrorEmptyQueue()
        media = self.play_queue.pop(0)
        if self.current_media is not None:
            self.play_history.append(self.current_media)
        self.current_media = media

    def back_media_content(self):
        """Переключает на прошлый контент."""
        if not self.play_history:
            return Errors.ErrorEmptyHistory()
        media = self.play_history.pop(-1)
        if self.current_media is not None:
            self.play_queue.insert(0, self.current_media)
        self.current_media = media

    def clear(self):
        """Очищает очередь и текущий контент."""
        self.play_queue.clear()
        self.current_media = None

    def get_current_media(self):
        """Возвращает текущий контент."""
        return self.current_media

    def get_history(self):
        """Возвращает историю прослушивания."""
        return self.play_history.copy()

    def get_queue(self):
        """Возвращает очередь прослушивания."""
        return self.play_queue.copy()


class DialogConfirm(QDialog, Ui_Dialog_confirm):
    def __init__(self):
        super(QDialog, self).__init__()
        super(Ui_Dialog_confirm, self).__init__()
        self.setupUi(self)
        list_buttons = self.buttonBox.buttons()
        list_buttons[0].clicked.connect(self.accept)
        list_buttons[1].clicked.connect(self.reject)


class MyObject:
    def __init__(self):
        self.row = None
        self.column = None
        self.place_call = None
        self.file_name = None
        self.href_song = None

    def set_href(self, href):
        """Ставит href."""
        if not isinstance(href, str):
            raise Errors.ErrorWrongTypeObject()
        self.href_song = href

    def get_href(self):
        """Возращает href."""
        return self.href_song

    def set_column(self, value):
        """Ставит столбик нахождения."""
        if not isinstance(value, int):
            raise Errors.ErrorWrongTypeObject()
        self.column = value

    def get_column(self):
        """Возвращает столбик нахождения."""
        return self.column

    def set_file_name(self, file_name):
        if not isinstance(file_name, str):
            raise Errors.ErrorWrongTypeObject()
        """Ставит имя медиа-файла, который будет привязан."""
        self.file_name = file_name

    def get_name(self):
        """Возвращает имя медиа-файла."""
        return self.file_name

    def set_place_call(self, place):
        """Ставит место, в когтором будет находиться."""
        self.place_call = place

    def get_place_call(self):
        """Возвращает место вызова."""
        return self.place_call

    def set_row(self, value):
        """Ставит строчку нахождения."""
        if not isinstance(value, int):
            raise Errors.ErrorWrongTypeObject()
        self.row = value

    def get_row(self):
        """Возращает строку нахождения."""
        return self.row


class Button(QPushButton, MyObject):
    def __init__(self, *args, **kwargs):
        super(QPushButton, self).__init__(*args, **kwargs)
        super(MyObject, self).__init__()


class LineEdit(QLineEdit, MyObject):
    def __init__(self, *args, **kwargs):
        super(LineEdit, self).__init__(*args, **kwargs)
        super(MyObject, self).__init__()


class Label(QLabel, MyObject):
    def __init__(self, *args, **kwargs):
        super(QLabel, self).__init__(*args, **kwargs)
        super(MyObject, self).__init__()


class ToolButton(QToolButton, MyObject):
    def __init__(self, *args, **kwargs):
        super(QToolButton, self).__init__(*args, **kwargs)
        super(MyObject, self).__init__()


# Очищает grid_layout от всех widgets.
def clear_grid_layout(grid_layout):
    for i in range(grid_layout.count()):
        widget = grid_layout.takeAt(0).widget()
        if widget is not None:
            widget.deleteLater()


# Шаблон элемента (строка),
# который будет создаваться в приложении для взаимодействия с пользователем.
def add_element_template(
        self, grid_layout, row, file_name,
        numbering=False, tool_button=True, delete=False, play=True, add=False,
        type_file=QMediaContent, href_object=None, transformation_name=True
):
    col = 0

    # Кнопка "добавить".
    if add and type_file == QMediaContent:
        button_add = Button('Добавить', self)
        button_add.setIcon(QIcon('images/plus-green.png'))
        if href_object is not None:
            button_add.set_href(href_object)
        button_add.set_row(row)
        button_add.set_column(col)
        button_add.set_file_name(file_name)
        button_add.set_place_call(grid_layout)
        button_add.clicked.connect(self.add_song)
        grid_layout.addWidget(button_add, row, col)
        col += 1

    # Номерация.
    if numbering and type_file == QMediaContent:
        line_edit = LineEdit(self)
        if href_object is not None:
            line_edit.set_href(href_object)
        line_edit.setText(str(row + 1))
        line_edit.set_row(row)
        line_edit.set_column(col)
        line_edit.set_file_name(file_name)
        line_edit.set_place_call(grid_layout)
        line_edit.editingFinished.connect(self.move_media_queue)
        grid_layout.addWidget(line_edit, row, col)
        col += 1

    # Отображаемое имя.
    label_name_song = Label(
        turn_into_a_name(file_name) if transformation_name else file_name,
        self)
    if href_object is not None:
        label_name_song.set_href(href_object)
    label_name_song.set_file_name(file_name)
    label_name_song.set_row(row)
    label_name_song.set_place_call(grid_layout)
    label_name_song.set_column(col)
    grid_layout.addWidget(label_name_song, row, col)
    col += 1

    # Кнопка "играть".
    if play:
        button_play = Button('играть', self)
        button_play.setIcon(QIcon('images/button_play.png'))
        if href_object is not None:
            button_play.set_href(href_object)
        button_play.set_row(row)
        button_play.set_column(col)
        button_play.set_place_call(grid_layout)
        button_play.set_file_name(file_name)
        button_play.clicked.connect(
            self.play_song if type_file == QMediaContent
            else self.play_playlist
        )
        grid_layout.addWidget(button_play, row, col)
        col += 1

    # Кнопка "удалить".
    if delete:
        button_delete = Button('delete', self)
        if href_object is not None:
            button_delete.set_href(href_object)
        button_delete.setIcon(QIcon('images/seo.png'))
        button_delete.set_row(row)
        button_delete.set_column(col)
        button_delete.set_file_name(file_name)
        button_delete.set_place_call(grid_layout)
        button_delete.clicked.connect(
            self.delete_song if type_file == QMediaContent else None)
        grid_layout.addWidget(button_delete, row, col)
        col += 1

    # Кнопка функций.
    if tool_button:
        tool_button = ToolButton(self)
        if href_object is not None:
            tool_button.set_href(href_object)
        tool_button.clicked.connect(
            self.open_dialog_functions_song if type_file == QMediaContent
            else self.open_dialog_functions_playlist
        )
        tool_button.set_row(row)
        tool_button.set_column(col)
        tool_button.set_file_name(file_name)
        tool_button.set_place_call(grid_layout)
        tool_button.setText('...')
        grid_layout.addWidget(tool_button, row, col)


# Возвращает множество песен, которые загруженны.
def get_name_songs_download():
    with os.scandir('base data/music/songs') as list_of_entries:
        return set(
            map(
                lambda entry: entry.name,
                list_of_entries
            )
        )


# удаляет расширение у названия.
def turn_into_a_name(file_name):
    if '.' in file_name:
        file_name = ''.join(file_name.split('.')[:-1])
    return file_name


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    mw.update_player()
    mw.update_songs_in_scroll_area()
    mw.update_playlist_in_scroll_area()
    sys.excepthook = except_hook
    sys.exit(app.exec())
