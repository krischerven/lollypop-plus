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

from gi.repository import Gtk, Pango, GLib, GObject

from gettext import gettext as _

from lollypop.define import App, ViewType, MARGIN_SMALL, IndicatorType
from lollypop.define import StorageType
from lollypop.widgets_indicator import IndicatorWidget
from lollypop.utils import ms_to_string, on_query_tooltip, popup_widget
from lollypop.utils import emit_signal


class TrackRow(Gtk.ListBoxRow):
    """
        A track row
    """

    __gsignals__ = {
        "removed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def get_best_height(widget):
        """
            Calculate widget height
            @param widget as Gtk.Widget
        """
        ctx = widget.get_pango_context()
        layout = Pango.Layout.new(ctx)
        layout.set_text("a", 1)
        font_height = int(layout.get_pixel_size()[1])
        # application.css
        min_height = 32
        if font_height > min_height:
            height = font_height
        else:
            height = min_height
        return height

    def __init__(self, track, album_artist_ids, view_type, show_track_number):
        """
            Init row widgets
            @param track as Track
            @param album_artist_ids as [int]
            @param view_type as ViewType
            @param show_track_number as bool
        """
        # We do not use Gtk.Builder for speed reasons
        Gtk.ListBoxRow.__init__(self)
        self.__view_type = view_type
        self.__show_track_number = show_track_number
        self._track = track
        self._grid = Gtk.Grid()
        self._grid.set_property("valign", Gtk.Align.CENTER)
        self._grid.set_column_spacing(5)
        self._grid.show()
        self._indicator = IndicatorWidget(self, view_type)
        self._indicator.show()
        self._grid.add(self._indicator)
        self._num_label = Gtk.Label.new()
        self._num_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._num_label.set_width_chars(4)
        self._num_label.get_style_context().add_class("dim-label")
        self._num_label.show()
        self.update_number_label()
        self._grid.add(self._num_label)
        self.__title_label = Gtk.Label.new(
            GLib.markup_escape_text(self._track.name))
        self.__title_label.set_use_markup(True)
        self.__title_label.set_property("has-tooltip", True)
        self.__title_label.connect("query-tooltip", on_query_tooltip)
        self.__title_label.set_property("hexpand", True)
        self.__title_label.set_property("halign", Gtk.Align.START)
        self.__title_label.set_property("xalign", 0)
        self.__title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.__title_label.show()
        self._grid.add(self.__title_label)
        featuring_artist_ids = track.get_featuring_artist_ids(album_artist_ids)
        if featuring_artist_ids:
            artists = []
            for artist_id in featuring_artist_ids:
                artists.append(App().artists.get_name(artist_id))
            artists_label = Gtk.Label.new(GLib.markup_escape_text(
                ", ".join(artists)))
            artists_label.set_use_markup(True)
            artists_label.set_property("has-tooltip", True)
            artists_label.connect("query-tooltip", on_query_tooltip)
            artists_label.set_property("hexpand", True)
            artists_label.set_property("halign", Gtk.Align.END)
            artists_label.set_ellipsize(Pango.EllipsizeMode.END)
            artists_label.set_opacity(0.3)
            artists_label.set_margin_end(5)
            artists_label.show()
            self._grid.add(artists_label)
        duration = ms_to_string(self._track.duration)
        self.__duration_label = Gtk.Label.new(duration)
        self.__duration_label.get_style_context().add_class("dim-label")
        self.__duration_label.show()
        self._grid.add(self.__duration_label)
        if self.__view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
            self.__action_button = Gtk.Button.new_from_icon_name(
               "list-remove-symbolic",
               Gtk.IconSize.MENU)
            self.__action_button.set_tooltip_text(
               _("Remove from playlist"))
        else:
            self.__action_button = Gtk.Button.new_from_icon_name(
               "view-more-symbolic",
               Gtk.IconSize.MENU)
        self.__action_button.show()
        self.__action_button.connect("clicked",
                                     self.__on_action_button_clicked)
        self.__action_button.set_margin_end(MARGIN_SMALL)
        self.__action_button.set_relief(Gtk.ReliefStyle.NONE)
        context = self.__action_button.get_style_context()
        context.add_class("menu-button")
        self._grid.add(self.__action_button)
        self.add(self._grid)
        self.set_indicator(self._get_indicator_type())
        self.update_duration()
        self.get_style_context().add_class("trackrow")

    def update_duration(self):
        """
            Update track duration
        """
        self._track.reset("duration")
        duration = ms_to_string(self._track.duration)
        self.__duration_label.set_label(duration)

    def set_indicator(self, indicator_type=None):
        """
            Show indicator
            @param indicator_type as IndicatorType
        """
        if indicator_type is None:
            indicator_type = self._get_indicator_type()
        self._indicator.clear()
        if indicator_type & IndicatorType.LOADING:
            self._indicator.set_opacity(1)
            self._indicator.load()
        elif indicator_type & IndicatorType.PLAY:
            self._indicator.set_opacity(1)
            self.set_state_flags(Gtk.StateFlags.VISITED, True)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.play_loved()
            else:
                self._indicator.play()
        else:
            self.unset_state_flags(Gtk.StateFlags.VISITED)
            if indicator_type & IndicatorType.LOVED:
                self._indicator.set_opacity(1)
                self._indicator.loved()
            elif indicator_type & IndicatorType.SKIP:
                self._indicator.set_opacity(1)
                self._indicator.skip()
            else:
                self._indicator.set_opacity(0)

    def update_number_label(self):
        """
            Update position label for row
        """
        if App().player.is_in_queue(self._track.id):
            self._num_label.get_style_context().add_class("queued")
            pos = App().player.get_track_position(self._track.id)
            self._num_label.set_text(str(pos))
            self._num_label.show()
        elif self.__show_track_number:
            self._num_label.get_style_context().remove_class("queued")
            # Just track number for albums or playlists if only one album
            if self.__view_type & ViewType.ALBUM or\
                    len(self._track.album.discs) == 1:
                self._num_label.set_text(str(self._track.number))
            # Prepend disc number
            elif len(self._track.album.discs) > 1:
                discnumber = App().tracks.get_discnumber(self._track.id)
                label = "(%s)  %s" % (discnumber, self._track.number)
                self._num_label.set_text(label)
            self._num_label.show()
        else:
            self._num_label.get_style_context().remove_class("queued")
            self._num_label.set_text("")
            self._num_label.hide()

    def popup_menu(self, parent, x=None, y=None):
        """
            Popup menu for track
            @param parent as Gtk.Widget
            @param x as int
            @param y as int
        """
        def on_hidden(widget, hide):
            self.set_indicator()

        from lollypop.menu_objects import TrackMenu, TrackMenuExt
        from lollypop.widgets_menu import MenuBuilder
        menu = TrackMenu(self._track, self.__view_type,
                         App().window.is_adaptive)
        menu_widget = MenuBuilder(menu)
        menu_widget.show()
        if not self._track.storage_type & StorageType.EPHEMERAL:
            menu_ext = TrackMenuExt(self._track)
            menu_ext.show()
            menu_widget.append_widget(menu_ext)
        popover = popup_widget(menu_widget, parent, x, y, self)
        if popover is None:
            menu_widget.connect("hidden", on_hidden)
        else:
            popover.connect("hidden", on_hidden)

    @property
    def name(self):
        """
            Get row name
            @return str
        """
        return self.__title_label.get_text()

    @property
    def track(self):
        """
            Get row track
            @return Track
        """
        return self._track

#######################
# PROTECTED           #
#######################
    def _get_indicator_type(self):
        """
            Get indicator type for current row
            @return IndicatorType
        """
        indicator_type = IndicatorType.NONE
        if App().player.current_track.id == self._track.id:
            indicator_type |= IndicatorType.PLAY
        if self._track.loved == 1:
            indicator_type |= IndicatorType.LOVED
        elif self._track.loved == -1:
            indicator_type |= IndicatorType.SKIP
        return indicator_type

#######################
# PRIVATE             #
#######################
    def __on_action_button_clicked(self, button):
        """
            Show row menu
            @param button as Gtk.Button
        """
        if self.__view_type & (ViewType.PLAYBACK | ViewType.PLAYLISTS):
            emit_signal(self, "removed")
        else:
            self.popup_menu(button)
