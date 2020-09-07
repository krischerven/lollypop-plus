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

from gi.repository import Gtk, GObject

from lollypop.define import App, ViewType, MARGIN
from lollypop.view_tracks_album import AlbumTracksView
from lollypop.widgets_banner_album import AlbumBannerWidget
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.utils import emit_signal
from lollypop.helper_gestures import GesturesHelper


class AlbumWidget(Gtk.Grid, SignalsHelper):
    """
        Show artist albums and tracks
    """

    __gsignals__ = {
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    @signals_map
    def __init__(self, album, storage_type, view_type):
        """
            Init album widget
            @param album as Album
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        Gtk.Grid.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.__tracks_view = None
        self.__view_type = view_type
        self.__storage_type = storage_type
        self.__album = album
        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().player, "duration-changed", "_on_duration_changed"),
        ]

    def populate(self):
        """
            Populate widget
        """
        self.__revealer = Gtk.Revealer.new()
        self.__revealer.show()
        self.__banner = AlbumBannerWidget(self.__album, self.__storage_type,
                                          self.__view_type)
        self.__banner.show()
        self.__banner.connect("populated", self.__on_banner_populated)
        self.__banner.populate()
        self.add(self.__banner)
        self.add(self.__revealer)
        self.__gesture = GesturesHelper(self.__banner,
                                        primary_press_callback=self._on_press)
        self.get_style_context().add_class("album-banner")
        if App().settings.get_value("show-artist-tracks"):
            self.__revealer.set_transition_type(
                Gtk.RevealerTransitionType.NONE)
            self.__populate()

    def reveal_child(self):
        """
            Reveal tracks
        """
        self.__revealer.set_transition_type(
                Gtk.RevealerTransitionType.NONE)
        self.__populate()
        self.__revealer.set_reveal_child(True)

    def do_get_preferred_width(self):
        return (200, 600)

    @property
    def banner(self):
        """
            Get banner
            @return BannerWidget
        """
        return self.__banner

    @property
    def name(self):
        """
            Get name
            @return str
        """
        return self.__album.name

    @property
    def album(self):
        """
            Get album
            @return Album
        """
        return self.__album

    @property
    def is_populated(self):
        """
            True if populated
            @return bool
        """
        return True

    @property
    def args(self):
        """
            Get default args for __class__
            @return {}
        """
        return {"album": self.__album,
                "storage_type": self.storage_type,
                "view_type": self.view_type & ~ViewType.SMALL}

    @property
    def filtered(self):
        """
            Get filtered children
            @return [Gtk.Widget]
        """
        if self.__tracks_view is None:
            self.__populate()
        filtered = self.__tracks_view.children
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
    def _on_press(self, x, y, event):
        """
            Show tracks
            @param x as int
            @param y as int
            @param event as Gdk.Event
        """
        self.__populate()

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
    def __populate(self):
        """
            Populate the view with album
        """
        if self.__tracks_view is None:
            self.__tracks_view = AlbumTracksView(self.__album,
                                                 self.__view_type)
            self.__tracks_view.show()
            self.__tracks_view.set_margin_start(MARGIN)
            self.__tracks_view.set_margin_end(MARGIN)
            self.__tracks_view.populate()
            self.__tracks_view.connect("populated", self.__on_tracks_populated)
            self.__revealer.add(self.__tracks_view)
        self.__revealer.set_reveal_child(
            not self.__revealer.get_reveal_child())

    def __on_tracks_populated(self, view):
        """
            Populate remaining discs
            @param view as TracksView
        """
        if not self.__tracks_view.is_populated:
            self.__tracks_view.populate()

    def __on_banner_populated(self, widget):
        """
            Emit populated signal
            @param widget as Gtk.Widget
        """
        emit_signal(self, "populated")
