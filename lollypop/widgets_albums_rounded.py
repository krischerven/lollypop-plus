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

from gi.repository import GLib, Gdk, Gio

import cairo
from random import shuffle

from lollypop.define import App, Type
from lollypop.objects_album import Album
from lollypop.utils import get_round_surface, emit_signal
from lollypop.widgets_flowbox_rounded import RoundedFlowBoxWidget


class RoundedAlbumsWidget(RoundedFlowBoxWidget):
    """
        Rounded widget showing cover for 4 albums
    """
    _ALBUMS_COUNT = 4

    def __init__(self, data, name, sortname, view_type):
        """
            Init widget
            @param data as object
            @param name as str
            @param sortname as str
            @param art_size as int
        """
        RoundedFlowBoxWidget.__init__(self, data, name, sortname, view_type)
        self._genre = Type.NONE
        self.__album_ids = []
        self.__cancellable = Gio.Cancellable()
        self._scale_factor = self.get_scale_factor()
        self.connect("unmap", self.__on_unmap)

    def populate(self):
        """
            Populate widget content
        """
        RoundedFlowBoxWidget.populate(self)
        self._artwork.get_style_context().add_class("rounded-icon-large")

    def set_view_type(self, view_type):
        """
            Update artwork size
            @param view_type as ViewType
        """
        RoundedFlowBoxWidget.set_view_type(self, view_type)
        if len(self._get_album_ids()) == 1:
            self.__cover_size = self._art_size
        else:
            self.__cover_size = self._art_size / 2
        self._pixel_size = self._art_size / 8

    def set_artwork(self):
        """
            Set artwork
        """
        RoundedFlowBoxWidget.set_artwork(self)
        if App().art.artwork_exists_in_cache(self.artwork_name,
                                             "ROUNDED",
                                             self._art_size,
                                             self._art_size):
            App().task_helper.run(
                App().art.get_artwork_from_cache,
                self.artwork_name, "ROUNDED",
                self._art_size, self._art_size,
                callback=(self.__on_load_from_cache,))
        else:
            self.__album_ids = self._get_album_ids()
            shuffle(self.__album_ids)
            App().task_helper.run(self._create_surface, True)

#######################
# PROTECTED           #
#######################
    def _create_surface(self, set_surface):
        """
            Get artwork surface
            @param set_surface as bool
            @return cairo.Surface
        """
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24,
                                     self._art_size,
                                     self._art_size)
        ctx = cairo.Context(surface)
        ctx.rectangle(0, 0, self._art_size, self._art_size)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        album_ids = list(self.__album_ids)
        if len(album_ids) == 1:
            positions = [(0, 0)]
        else:
            positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
        if len(album_ids) == 2:
            album_ids.append(album_ids[1])
            album_ids.append(album_ids[0])
        if len(album_ids) == 3:
            album_ids.append(album_ids[0])
        self.__draw_surface(surface, ctx, positions, album_ids, set_surface)

#######################
# PRIVATE             #
#######################
    def __set_surface(self, surface):
        """
            Set artwork from surface
            @param surface as cairo.Surface
        """
        if self.__cancellable.is_cancelled():
            return
        rounded = get_round_surface(
            surface, self._scale_factor, self._art_size / 4)
        del surface
        self._artwork.set_from_surface(rounded)
        App().art.add_artwork_to_cache(self.artwork_name,
                                       rounded,
                                       "ROUNDED")
        del rounded
        emit_signal(self, "populated")

    def __draw_surface(self, surface, ctx, positions, album_ids, set_surface):
        """
            Draw surface for first available album
            @param surface as cairo.Surface
            @param ctx as Cairo.context
            @param positions as {}
            @param album_ids as [int]
            @param set_surface as bool
            @thread safe
        """
        # Workaround Gdk not being thread safe
        def draw_pixbuf(surface, ctx, pixbuf, positions, album_ids):
            if self.__cancellable.is_cancelled():
                return
            (x, y) = positions.pop(0)
            x *= self.__cover_size
            y *= self.__cover_size
            subsurface = Gdk.cairo_surface_create_from_pixbuf(
                pixbuf, self._scale_factor, None)
            del pixbuf
            ctx.translate(x, y)
            ctx.set_source_surface(subsurface, 0, 0)
            ctx.paint()
            ctx.translate(-x, -y)
            self.__draw_surface(surface, ctx, positions,
                                album_ids, set_surface)
            del surface
        if self.__cancellable.is_cancelled():
            return
        elif album_ids and len(positions) > 0:
            album_id = album_ids.pop(0)
            pixbuf = App().art.get_album_artwork(Album(album_id),
                                                 self.__cover_size,
                                                 self.__cover_size,
                                                 self._scale_factor)
            if pixbuf is None:
                GLib.idle_add(self.__draw_surface, surface,
                              ctx, positions, album_ids, set_surface)
            else:
                GLib.idle_add(draw_pixbuf, surface,
                              ctx, pixbuf, positions, album_ids)
        else:
            GLib.idle_add(self.__set_surface, surface)

    def __on_load_from_cache(self, pixbuf):
        """
            Set artwork surface
            @param pixbuf as GdkPixbuf.Pixbuf
        """
        if not self.__cancellable.is_cancelled() and pixbuf is not None:
            surface = Gdk.cairo_surface_create_from_pixbuf(
                pixbuf, self._artwork.get_scale_factor(), None)
            self._artwork.set_from_surface(
                    get_round_surface(surface, self._scale_factor,
                                      self._art_size / 4))
        emit_signal(self, "populated")

    def __on_unmap(self, widget):
        """
            Cancel drawing
            @param widget as Gtk.Widget
        """
        self.__cancellable.cancel()
        self.__cancellable = Gio.Cancellable()
