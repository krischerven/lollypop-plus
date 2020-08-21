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

from gi.repository import Gtk, GLib, GObject, Handy

from lollypop.define import App, Type
from lollypop.utils import emit_signal
from lollypop.view import View
from lollypop.container_stack import StackContainer
from lollypop.container_notification import NotificationContainer
from lollypop.container_scanner import ScannerContainer
from lollypop.container_playlists import PlaylistsContainer
from lollypop.container_lists import ListsContainer
from lollypop.container_views import ViewsContainer
from lollypop.container_filter import FilterContainer
from lollypop.progressbar import ProgressBar


class Grid(Gtk.Grid):
    def do_get_preferred_width(self):
        return 200, 700


class Container(Gtk.Overlay, NotificationContainer,
                ScannerContainer, PlaylistsContainer,
                ListsContainer, ViewsContainer, FilterContainer):
    """
        Main view management
    """

    __gsignals__ = {
        "can-go-back-changed": (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    def __init__(self):
        """
            Init container
            @param view_type as ViewType, will be appended to any created view
        """
        Gtk.Overlay.__init__(self)
        NotificationContainer.__init__(self)
        ScannerContainer.__init__(self)
        PlaylistsContainer.__init__(self)
        ViewsContainer.__init__(self)

    def setup(self):
        """
            Setup container
        """
        self.__widget = Handy.Leaflet()
        self.__widget.show()
        self.__sub_widget = Handy.Leaflet()
        self.__sub_widget.show()
        ListsContainer.__init__(self)
        self.__paned_position_id = None
        self.__focused_view = None
        self._stack = StackContainer()
        self._stack.show()
        self.__progress = ProgressBar()
        self.__progress.get_style_context().add_class("progress-bottom")
        self.__progress.set_property("valign", Gtk.Align.END)
        self.add_overlay(self.__progress)
        search_action = App().lookup_action("search")
        search_action.connect("activate", self.__on_search_activate)
        self.__widget.add(self.sidebar)
        self.__grid_view = Grid()
        self.__grid_view.set_orientation(Gtk.Orientation.VERTICAL)
        self.__grid_view.show()
        self.__sub_widget.add(self.left_list)
        self.__sub_widget.add(self.__grid_view)
        self.__grid_view.attach(self._stack, 0, 0, 1, 1)
        self.__widget.add(self.__sub_widget)
        self.__widget.set_visible_child(self.__sub_widget)
        self.__sub_widget.set_visible_child(self.__grid_view)
        self.add(self.__widget)
        FilterContainer.__init__(self)

    def stop(self):
        """
            Stop current view from processing
        """
        view = self._stack.get_visible_child()
        if view is not None:
            view.stop()

    def reload_view(self):
        """
            Reload current view
        """
        view = self._stack.get_visible_child()
        if view is not None and view.args is not None:
            from lollypop.view_artist_box import ArtistViewBox
            from lollypop.view_artist_list import ArtistViewList
            show_tracks = App().settings.get_value("show-artist-tracks")
            if view.__class__ == ArtistViewBox and show_tracks:
                cls = ArtistViewList
            elif view.__class__ == ArtistViewList and not show_tracks:
                cls = ArtistViewBox
            else:
                cls = view.__class__
            new_view = cls(**view.args)
            new_view.populate()
            new_view.show()
            self._stack.add(new_view)
            self._stack.set_visible_child(new_view)
        else:
            App().lookup_action("reload").change_state(GLib.Variant("b", True))

    def set_focused_view(self, view):
        """
            Set focused view
            @param view as View
        """
        self.__focused_view = view

    def go_back(self):
        """
            Go back in history
        """
        if self._stack.history.count > 0:
            self._stack.go_back()
        elif self.__sub_widget.get_folded() and\
                self.__sub_widget.get_visible_child() != self.left_list:
            self.__sub_widget.set_visible_child(self.left_list)
            self._stack.clear()
        elif self.__widget.get_folded() and\
                self.__widget.get_visible_child() != self.sidebar:
            self.__widget.set_visible_child(self.sidebar)
            self._stack.clear()
        emit_signal(self, "can-go-back-changed", self.can_go_back)

    @property
    def can_go_back(self):
        """
            True if can go back
            @return bool
        """
        if self.__widget.get_folded():
            return self.__widget.get_visible_child() != self._sidebar
        else:
            return self._stack.history.count > 0

    @property
    def widget(self):
        """
            Get main widget
            @return Handy.Leaflet
        """
        return self.__widget

    @property
    def sub_widget(self):
        """
            Get sub widget
            @return Handy.Leaflet
        """
        return self.__sub_widget

    @property
    def grid_view(self):
        """
            Get grid view
            @return Gtk.Grid
        """
        return self.__grid_view

    @property
    def focused_view(self):
        """
            Get focused view
            @return View
        """
        return self.__focused_view

    @property
    def view(self):
        """
            Get current view
            @return View
        """
        view = self._stack.get_visible_child()
        if view is not None and isinstance(view, View):
            return view
        return None

    @property
    def stack(self):
        """
            Container stack
            @return stack as Gtk.Stack
        """
        return self._stack

    @property
    def progress(self):
        """
            Progress bar
            @return ProgressBar
        """
        return self.__progress

############
# PRIVATE  #
############
    def __show_settings_dialog(self):
        """
            Show settings dialog if view exists in stack
        """
        from lollypop.view_settings import SettingsChildView
        from lollypop.view_settings import SettingsView
        if isinstance(self.view, SettingsChildView) or\
                isinstance(self.view, SettingsView):
            action = App().lookup_action("settings")
            GLib.idle_add(action.activate,
                          GLib.Variant("i", self.view.type))

    def __on_search_activate(self, action, variant):
        """
            @param action as Gio.SimpleAction
            @param variant as GLib.Variant
        """
        if App().window.folded:
            search = variant.get_string()
            App().window.container.show_view([Type.SEARCH], search)

    def __on_paned_position(self, paned, param):
        """
            Save paned position
            @param paned as Gtk.Paned
            @param param as GParamSpec
        """
        def save_position():
            self.__paned_position_id = None
            position = paned.get_property(param.name)
            # We do not want to save position if folded
            if App().window is not None and App().window.folded:
                return
            App().settings.set_value("paned-listview-width",
                                     GLib.Variant("i",
                                                  position))
        # We delay position saving
        # Useful for adative mode where position get garbaged
        if self.__paned_position_id is not None:
            GLib.source_remove(self.__paned_position_id)
        self.__paned_position_id = GLib.timeout_add(
            1000, save_position)
