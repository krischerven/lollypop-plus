# Copyright (c) 2014-2020 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk

from lollypop.define import App, ViewType, MARGIN, ScanUpdate
from lollypop.view_tracks_album import AlbumTracksView
from lollypop.widgets_banner_album import AlbumBannerWidget
from lollypop.controller_view import ViewController, ViewControllerType
from lollypop.view_lazyloading import LazyLoadingView
from lollypop.helper_signals import SignalsHelper, signals_map


class AlbumView(LazyLoadingView, ViewController, SignalsHelper):
    """
        Show artist albums and tracks
    """

    @signals_map
    def __init__(self, album, storage_type, view_type):
        """
            Init ArtistView
            @param album as Album
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, storage_type, view_type)
        ViewController.__init__(self, ViewControllerType.ALBUM)
        self.__tracks_view = None
        self.__album = album
        self.__others_boxes = []
        self.__grid = Gtk.Grid()
        self.__grid.show()
        self.__grid.set_row_spacing(10)
        self.__grid.set_orientation(Gtk.Orientation.VERTICAL)
        self.__banner = AlbumBannerWidget(self.__album, self.storage_type,
                                          self.view_type)
        self.add_widget(self.__grid, self.__banner)
        return [
            (App().scanner, "scan-finished", "_on_scan_finished"),
            (App().scanner, "updated", "_on_collection_updated")
        ]

    def populate(self):
        """
            Populate the view with album
        """
        if self.__tracks_view is None:
            self.__tracks_view = AlbumTracksView(self.__album, ViewType.ALBUM)
            self.__tracks_view.show()
            self.__tracks_view.connect("populated", self.__on_tracks_populated)
            self.__tracks_view.set_margin_start(MARGIN)
            self.__tracks_view.set_margin_end(MARGIN)
            self.__tracks_view.populate()
            self.__grid.add(self.__tracks_view)

    @property
    def name(self):
        """
            Get name
            @return str
        """
        return self.__album.name

    @property
    def is_populated(self):
        """
            True if populated
            @return bool
        """
        return self.__tracks_view is not None

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"album": self.__album,
                "storage_type": self.storage_type,
                "view_type": self.view_type & ~(ViewType.ADAPTIVE |
                                                ViewType.SMALL)}

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        if self.__tracks_view is None:
            return []
        filtered = self.__tracks_view.children
        for box in self.__others_boxes:
            for child in box.children:
                filtered.append(child)
        return filtered

    @property
    def scroll_shift(self):
        """
            Get scroll shift for y axes
            @return int
        """
        return self.__banner.height

#######################
# PROTECTED           #
#######################
    def _on_scan_finished(self, scanner, track_ids):
        """
            Reload album if needed
            @param scanner as CollectionScanner
            @param track_ids as int
        """
        if not self.get_sensitive():
            App().window.container.reload_view()

    def _on_collection_updated(self, scanner, item, scan_update):
        """
            Handles changes in collection
            @param scanner as CollectionScanner
            @param item as CollectionItem
            @param scan_update as ScanUpdate
        """
        if item.album_id != self.__album.id:
            return
        if scan_update == ScanUpdate.REMOVED:
            App().window.container.go_back()

    def _on_current_changed(self, player):
        """
            Update children state
            @param player as Player
        """
        if self.__tracks_view is not None:
            self.__tracks_view.set_playing_indicator()

    def _on_duration_changed(self, player, track_id):
        """
            Update track duration
            @param player as Player
            @param track_id as int
        """
        if self.__tracks_view is not None:
            self.__tracks_view.update_duration(track_id)

#######################
# PRIVATE             #
#######################
    def __on_tracks_populated(self, view):
        """
            Populate remaining discs
            @param view as TracksView
        """
        if self.__tracks_view.is_populated:
            self.emit("populated")
            self.__banner.show()
            if self.view_type & ViewType.OVERLAY:
                from lollypop.view_albums_line import AlbumsArtistLineView
                for artist_id in self.__album.artist_ids:
                    others_box = AlbumsArtistLineView(artist_id,
                                                      self.__album.genre_ids,
                                                      self.storage_type,
                                                      ViewType.SMALL |
                                                      ViewType.ALBUM |
                                                      ViewType.SCROLLED)
                    others_box.set_margin_start(MARGIN)
                    others_box.set_margin_end(MARGIN)
                    others_box.populate(self.__album.id)
                    self.__grid.add(others_box)
                    self.__others_boxes.append(others_box)
        else:
            self.__tracks_view.populate()
