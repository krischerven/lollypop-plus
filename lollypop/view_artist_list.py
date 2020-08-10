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

from lollypop.define import ViewType, MARGIN, App
from lollypop.widgets_banner_artist import ArtistBannerWidget
from lollypop.view_album import AlbumView
from lollypop.objects_album import Album
from lollypop.view_lazyloading import LazyLoadingView


class ArtistViewList(LazyLoadingView):
    """
        Show artist albums in a list with tracks
    """

    def __init__(self, genre_ids, artist_ids, storage_type, view_type):
        """
            Init ArtistView
            @param genre_ids as [int]
            @param artist_ids as [int]
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        LazyLoadingView.__init__(self, storage_type,
                                 view_type |
                                 ViewType.OVERLAY |
                                 ViewType.ARTIST)
        self.__others_boxes = []
        self.__genre_ids = genre_ids
        self.__artist_ids = artist_ids
        self.__storage_type = storage_type
        self.__banner = ArtistBannerWidget(genre_ids, artist_ids,
                                           storage_type, self.view_type)
        self.__banner.show()
        self.__list = Gtk.Box.new(Gtk.Orientation.VERTICAL, MARGIN * 4)
        self.__list.show()
        self.add_widget(self.__list, self.__banner)
        self.connect("populated", self.__on_populated)

    def populate(self):
        """
            Populate list
        """
        album_ids = App().albums.get_ids(self.__genre_ids,
                                         self.__artist_ids,
                                         self.storage_type,
                                         True)
        LazyLoadingView.populate(self, album_ids)

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"genre_ids": self.__genre_ids,
                "artist_ids": self.__artist_ids,
                "storage_type": self.storage_type,
                "view_type": self.view_type}

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        filtered = []
        for child in self.__list.get_children():
            if isinstance(child, AlbumView):
                filtered.append(child)
                filtered += child.filtered
            else:
                filtered += child.children
        return filtered

    @property
    def scroll_shift(self):
        """
            Get scroll shift for y axes
            @return int
        """
        return self.__banner.height + MARGIN

#######################
# PROTECTED           #
#######################
    def _get_child(self, album_id):
        """
            Get an album view widget
            @param album_id as int
            @return AlbumView
        """
        if self.destroyed:
            return None
        album = Album(album_id, self.__genre_ids, self.__artist_ids)
        widget = AlbumView(album,
                           self.storage_type,
                           ViewType.ARTIST)
        widget.show()
        widget.set_property("valign", Gtk.Align.START)
        self.__list.add(widget)
        return widget

    def __on_populated(self, view):
        """
            Add appears on albums
            @param view as ArtistViewBox
        """
        from lollypop.view_albums_line import AlbumsArtistAppearsOnLineView
        others_box = AlbumsArtistAppearsOnLineView(self.__artist_ids,
                                                   self.__genre_ids,
                                                   self.storage_type,
                                                   ViewType.SMALL |
                                                   ViewType.SCROLLED)
        others_box.set_margin_start(MARGIN)
        others_box.set_margin_end(MARGIN)
        others_box.populate()
        self.__list.add(others_box)
        self.__others_boxes.append(others_box)
