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

from gi.repository import GObject, Gio, GLib, GdkPixbuf

from PIL import Image, ImageFilter

from lollypop.define import ArtSize, App, ArtBehaviour
from lollypop.define import ALBUMS_PATH
from lollypop.logger import Logger


class BaseArt(GObject.GObject):
    """
        Base art manager
    """
    __gsignals__ = {
        "artwork-cleared": (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        "album-artwork-changed": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
        "artist-artwork-changed": (GObject.SignalFlags.RUN_FIRST,
                                   None, (str,)),
        "uri-artwork-found": (GObject.SignalFlags.RUN_FIRST, None,
                              (GObject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        """
            Init base art
        """
        GObject.GObject.__init__(self)

    def load_behaviour(self, pixbuf, cache_path, width, height, behaviour):
        """
            Load behaviour on pixbuf
            @param cache_path as str
            @param width as int
            @param height as int
            @param behaviour as ArtBehaviour
        """
        # Crop image as square
        if behaviour & ArtBehaviour.CROP_SQUARE:
            pixbuf = self._crop_pixbuf_square(pixbuf)
        # Crop image keeping ratio
        elif behaviour & ArtBehaviour.CROP:
            pixbuf = self._crop_pixbuf(pixbuf, width, height)

        # Handle blur
        if behaviour & ArtBehaviour.BLUR:
            _pixbuf = pixbuf
            pixbuf = _pixbuf.scale_simple(width,
                                          height,
                                          GdkPixbuf.InterpType.NEAREST)
            del _pixbuf
            pixbuf = self._get_blur(pixbuf, 25)
        elif behaviour & ArtBehaviour.BLUR_HARD:
            _pixbuf = pixbuf
            pixbuf = _pixbuf.scale_simple(width,
                                          height,
                                          GdkPixbuf.InterpType.NEAREST)
            pixbuf = self._get_blur(pixbuf, 50)
        elif behaviour & ArtBehaviour.BLUR_MAX:
            _pixbuf = pixbuf
            pixbuf = _pixbuf.scale_simple(width,
                                          height,
                                          GdkPixbuf.InterpType.NEAREST)
            del _pixbuf
            pixbuf = self._get_blur(pixbuf, 100)
        else:
            _pixbuf = pixbuf
            pixbuf = _pixbuf.scale_simple(width,
                                          height,
                                          GdkPixbuf.InterpType.BILINEAR)
            del _pixbuf
        if behaviour & ArtBehaviour.CACHE and cache_path is not None:
            if cache_path.endswith(".jpg"):
                pixbuf.savev(cache_path, "jpeg", ["quality"],
                             [str(App().settings.get_value(
                                 "cover-quality").get_int32())])
            else:
                pixbuf.savev(cache_path, "png", [None], [None])
        return pixbuf

    def update_art_size(self):
        """
            Update value with some check
        """
        value = App().settings.get_value("cover-size").get_int32()
        # Check value as user can enter bad value via dconf
        if value < 50 or value > 400:
            value = 200
        ArtSize.BIG = value
        ArtSize.BANNER = int(ArtSize.BIG * 150 / 200)
        ArtSize.MEDIUM = int(ArtSize.BIG * 100 / 200)
        ArtSize.SMALL = int(ArtSize.BIG * 50 / 200)

    def clean_store(self, filename):
        """
            @param filename as str
        """
        try:
            filepath = "%s/%s.%s" % (ALBUMS_PATH, filename, self._ext)
            f = Gio.File.new_for_path(filepath)
            if f.query_exists():
                f.delete()
        except Exception as e:
            Logger.error("Art::clean_store(): %s" % e)

    def save_pixbuf_from_data(self, path, data, width=-1, height=-1):
        """
            Save a pixbuf at path from data
            @param path as str
            @param data as bytes
            @param width as int
            @param height as int
        """
        # Create an empty file
        if data is None:
            f = Gio.File.new_for_path(path)
            fstream = f.replace(None, False,
                                Gio.FileCreateFlags.REPLACE_DESTINATION,
                                None)
            fstream.close()
        else:
            bytes = GLib.Bytes.new(data)
            stream = Gio.MemoryInputStream.new_from_bytes(bytes)
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
            if width != -1 and height != -1:
                pixbuf = pixbuf.scale_simple(width,
                                             height,
                                             GdkPixbuf.InterpType.BILINEAR)
            stream.close()
            pixbuf.savev(path, "jpeg", ["quality"],
                         [str(App().settings.get_value(
                             "cover-quality").get_int32())])
            del pixbuf

#######################
# PROTECTED           #
#######################
    def _crop_pixbuf(self, pixbuf, wanted_width, wanted_height):
        """
            Crop pixbuf
            @param pixbuf as GdkPixbuf.Pixbuf
            @param wanted_width as int
            @param wanted height as int
            @return GdkPixbuf.Pixbuf
        """
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        aspect = width / height
        wanted_aspect = wanted_width / wanted_height
        if aspect > wanted_aspect:
            new_width = height * wanted_aspect
            offset = (width - new_width)
            new_pixbuf = pixbuf.new_subpixbuf(offset / 2,
                                              0,
                                              width - offset,
                                              height)
        else:
            new_height = width / wanted_aspect
            offset = (height - new_height)
            new_pixbuf = pixbuf.new_subpixbuf(0,
                                              offset / 2,
                                              width,
                                              height - offset)
        del pixbuf
        return new_pixbuf

    def _crop_pixbuf_square(self, pixbuf):
        """
            Crop pixbuf as square
            @param pixbuf as GdkPixbuf.Pixbuf
            @return GdkPixbuf.Pixbuf
        """
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        if width == height:
            new_pixbuf = pixbuf
        elif width > height:
            diff = (width - height)
            new_pixbuf = pixbuf.new_subpixbuf(diff / 2,
                                              0,
                                              width - diff,
                                              height)
        else:
            diff = (height - width)
            new_pixbuf = pixbuf.new_subpixbuf(0,
                                              diff / 2,
                                              width,
                                              height - diff)
        del pixbuf
        return new_pixbuf

    def _get_blur(self, pixbuf, gaussian):
        """
            Blur surface using PIL
            @param pixbuf as GdkPixbuf.Pixbuf
            @param gaussian as int
            @return GdkPixbuf.Pixbuf
        """
        if pixbuf is None:
            return None
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        data = pixbuf.get_pixels()
        stride = pixbuf.get_rowstride()
        has_alpha = pixbuf.get_has_alpha()
        if has_alpha:
            mode = "RGBA"
            dst_row_stride = width * 4
        else:
            mode = "RGB"
            dst_row_stride = width * 3
        tmp = Image.frombytes(mode, (width, height),
                              data, "raw", mode, stride)
        tmp = tmp.filter(ImageFilter.GaussianBlur(gaussian))
        bytes = GLib.Bytes.new(tmp.tobytes())
        del pixbuf
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(bytes,
                                                 GdkPixbuf.Colorspace.RGB,
                                                 has_alpha,
                                                 8,
                                                 width,
                                                 height,
                                                 dst_row_stride)
        return pixbuf

#######################
# PRIVATE             #
#######################
