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


from lollypop.widgets_tracks import TracksWidget
from lollypop.helper_signals import SignalsHelper, signals_map
from lollypop.define import App, ViewType, IndicatorType
from lollypop.define import Size
from lollypop.helper_size_allocation import SizeAllocationHelper


class TracksView(Gtk.Bin, SignalsHelper, SizeAllocationHelper):
    """
        Responsive view showing tracks
    """

    __gsignals__ = {
        "activated": (GObject.SignalFlags.RUN_FIRST,
                      None, (GObject.TYPE_PYOBJECT,)),
        "populated": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "track-removed": (GObject.SignalFlags.RUN_FIRST, None,
                          (GObject.TYPE_PYOBJECT,)),
    }

    @signals_map
    def __init__(self, view_type):
        """
            Init view
            @param album as Album
            @param view_type as ViewType
        """
        Gtk.Bin.__init__(self)
        self.__view_type = view_type
        self._tracks_widget_left = {}
        self._tracks_widget_right = {}
        self._responsive_widget = None
        self.__orientation = None
        self.connect("realize", self.__on_realize)
        return [
            (App().player, "loading-changed", "_on_loading_changed")
        ]

    def get_current_ordinate(self, parent):
        """
            If current track in widget, return it ordinate,
            @param parent widget as Gtk.Widget
            @return y as int
        """
        for child in self.children:
            if child.id == App().player.current_track.id:
                return child.translate_coordinates(parent, 0, 0)[1]
        return None

    def set_playing_indicator(self):
        """
            Set playing indicator
        """
        pass

    def update_duration(self, track_id):
        """
            Update track duration
            @param track_id as int
        """
        pass

    @property
    def children(self):
        """
            Return all rows
            @return [Gtk.ListBoxRow]
        """
        return []

    @property
    def boxes(self):
        """
            Get available list boxes
            @return [Gtk.ListBox]
        """
        return []

    @property
    def view_type(self):
        """
            Get view type
            @return ViewType
        """
        return self.__view_type

#######################
# PROTECTED           #
#######################
    def _handle_width_allocate(self, allocation):
        """
            Change columns disposition
            @param allocation as Gtk.Allocation
        """
        if SizeAllocationHelper._handle_width_allocate(self, allocation):
            if allocation.width >= Size.NORMAL:
                orientation = Gtk.Orientation.HORIZONTAL
            else:
                orientation = Gtk.Orientation.VERTICAL
            if self.__orientation != orientation:
                self._set_orientation(orientation)

    def _init(self):
        """
            Init main widget
            @return bool
        """
        if self._responsive_widget is None:
            self._responsive_widget = Gtk.Grid()
            self._responsive_widget.set_column_spacing(20)
            self._responsive_widget.set_column_homogeneous(True)
            self._responsive_widget.set_property("valign", Gtk.Align.START)
            self.add(self._responsive_widget)
            self._responsive_widget.show()
            return True

    def _add_disc_container(self, disc_number):
        """
            Add disc container to box
            @param disc_number as int
        """
        self._tracks_widget_left[disc_number] = TracksWidget(self.__view_type)
        self._tracks_widget_right[disc_number] = TracksWidget(self.__view_type)
        self._tracks_widget_left[disc_number].connect("activated",
                                                      self._on_activated)
        self._tracks_widget_right[disc_number].connect("activated",
                                                       self._on_activated)

    def _add_tracks(self, widget, tracks, position=0):
        """
            Add tracks to widget
            @param widget as Gtk.ListBox
            @param tracks as [Track]
        """
        pass

    def _set_orientation(self, orientation):
        """
            Set columns orientation
            @param orientation as Gtk.Orientation
        """
        if self.__orientation == orientation:
            return False
        self.__orientation = orientation
        for child in self._responsive_widget.get_children():
            self._responsive_widget.remove(child)
        return True

    def _on_loading_changed(self, player, status, track):
        """
            Update row loading status
            @param player as Player
            @param status as bool
            @param track as Track
        """
        for row in self.children:
            if row.track.id == track.id:
                row.set_indicator(IndicatorType.LOADING)
            else:
                row.set_indicator()

    def _on_activated(self, widget, track):
        """
            Handle playback
            @param widget as TracksWidget
            @param track as Track
        """
        pass

#######################
# PRIVATE             #
#######################
    def __on_realize(self, widget):
        """
            Set initial orientation
            @param widget as Gtk.Widget
            @param window as AdaptiveWindow
            @param orientation as Gtk.Orientation
        """
        if self.__view_type & ViewType.SINGLE_COLUMN or\
                App().settings.get_value("force-single-column"):
            self._set_orientation(Gtk.Orientation.VERTICAL)
        elif self.__view_type & ViewType.TWO_COLUMNS:
            self._set_orientation(Gtk.Orientation.HORIZONTAL)
        else:
            # We need to listen to parent allocation as currently, we have
            # no children
            SizeAllocationHelper.__init__(self, True)
