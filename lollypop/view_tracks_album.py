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

from gi.repository import GLib, Gtk, Pango

from gettext import gettext as _

from lollypop.widgets_row_track import TrackRow
from lollypop.objects_album import Album
from lollypop.logger import Logger
from lollypop.utils import set_cursor_type, emit_signal
from lollypop.define import App, Type, ViewType
from lollypop.view_tracks import TracksView


class AlbumTracksView(TracksView):
    """
        Responsive view showing an album tracks
    """

    def __init__(self, album, view_type):
        """
            Init view
            @param album as Album
            @param view_type as ViewType
        """
        TracksView.__init__(self, view_type)
        self.__album = album
        self.__discs = []
        self.__discs_to_load = []
        self.__populated = False
        self.__show_tag_tracknumber = App().settings.get_value(
            "show-tag-tracknumber")

    def populate(self):
        """
            Populate tracks lazy
        """
        self._init()
        if self.__discs_to_load:
            disc = self.__discs_to_load.pop(0)
            disc_number = disc.number
            tracks = disc.tracks
            items = []
            if self.view_type & ViewType.SINGLE_COLUMN:
                items.append((self._tracks_widget_left[0], tracks))
            else:
                mid_tracks = int(0.5 + len(tracks) / 2)
                items.append((self._tracks_widget_left[disc_number],
                              tracks[:mid_tracks]))
                items.append((self._tracks_widget_right[disc_number],
                              tracks[mid_tracks:]))
            self.__load_disc(items, disc_number)
        else:
            self.__populated = True
            emit_signal(self, "populated")
            if not self.children:
                label = Gtk.Label.new(_("All tracks skipped"))
                label.show()
                self._responsive_widget.insert_row(0)
                self._responsive_widget.attach(label, 0, 0, 2, 1)

    def append_row(self, track):
        """
            Append a track
            ONE COLUMN ONLY
            @param track as Track
            @param position as int
        """
        self._init()
        if not self.is_populated:
            self.populate()
        self.__album.append_track(track)
        for key in self._tracks_widget_left.keys():
            self._add_tracks(self._tracks_widget_left[key], [track])
            return

    def append_rows(self, tracks):
        """
            Add track rows
            ONE COLUMN ONLY
            @param tracks as [Track]
        """
        self._init()
        if not self.is_populated:
            self.populate()
        self.__album.append_tracks(tracks)
        for key in self._tracks_widget_left.keys():
            self._add_tracks(self._tracks_widget_left[key], tracks)
            return

    def remove_row(self, track):
        """
            Remove row for track
            @param track as Track
        """
        self.__album.remove_track(track)
        for child in self.children:
            if child.track == track:
                child.destroy()

    def set_playing_indicator(self):
        """
            Set playing indicator
        """
        try:
            for disc in self.__discs:
                self._tracks_widget_left[disc.number].update_playing(
                    App().player.current_track.id)
                self._tracks_widget_right[disc.number].update_playing(
                    App().player.current_track.id)
        except Exception as e:
            Logger.error("TrackView::set_playing_indicator(): %s" % e)

    def update_duration(self, track_id):
        """
            Update track duration
            @param track_id as int
        """
        try:
            for disc in self.__discs:
                number = disc.number
                self._tracks_widget_left[number].update_duration(track_id)
                self._tracks_widget_right[number].update_duration(track_id)
        except Exception as e:
            Logger.error("TrackView::update_duration(): %s" % e)

    def set_view_type(self, view_type):
        """
            Update view type
            @param view_type as ViewType
        """
        self._view_type = view_type
        for child in self.children:
            child.set_view_type(view_type)

    @property
    def children(self):
        """
            Return all rows
            @return [Gtk.ListBoxRow]
        """
        rows = []
        for disc in self.__discs:
            for widget in [
                self._tracks_widget_left[disc.number],
                self._tracks_widget_right[disc.number]
            ]:
                rows += widget.get_children()
        return rows

    @property
    def boxes(self):
        """
            @return [Gtk.ListBox]
        """
        boxes = []
        for widget in self._tracks_widget_left.values():
            boxes.append(widget)
        for widget in self._tracks_widget_right.values():
            boxes.append(widget)
        return boxes

    @property
    def discs(self):
        """
            Get widget discs
            @return [Discs]
        """
        return self.__discs

    @property
    def is_populated(self):
        """
            Return True if populated
            @return bool
        """
        return self.__populated

#######################
# PROTECTED           #
#######################
    def _init(self):
        """
            Init main widget
        """
        if TracksView._init(self):
            if self.view_type & ViewType.SINGLE_COLUMN:
                self.__discs = [self.__album.one_disc]
            else:
                self.__discs = self.__album.discs
            for disc in self.__discs:
                self._add_disc_container(disc.number)
            self.__discs_to_load = list(self.__discs)

    def _add_tracks(self, widget, tracks, position=0):
        """
            Add tracks to widget
            @param widget as Gtk.ListBox
            @param tracks as [Track]
        """
        for track in tracks:
            # If user does not want to show real tracknumber and we are
            # in album view, calculate a fake tracknumber
            if not self.__show_tag_tracknumber and\
                    self.view_type & ViewType.ALBUM:
                track.set_number(position + 1)
            row = TrackRow(track, self.__album.artist_ids, self.view_type,
                           self.__show_tag_tracknumber)
            row.show()
            row.connect("removed", self.__on_track_row_removed)
            widget.add(row)
            position += 1

    def _set_orientation(self, orientation):
        """
            Set columns orientation
            @param orientation as Gtk.Orientation
        """
        if not TracksView._set_orientation(self, orientation):
            return
        idx = 0
        # Vertical
        ##########################
        #  --------Label-------- #
        #  |     Column 1      | #
        #  |     Column 2      | #
        ##########################
        # Horizontal
        ###########################
        # ---------Label--------- #
        # | Column 1 | Column 2 | #
        ###########################
        for disc in self.__discs:
            show_label = len(self.__discs) > 1
            disc_names = self.__album.disc_names(disc.number)
            if show_label or disc_names:
                if disc_names:
                    disc_text = ", ".join(disc_names)
                elif show_label:
                    disc_text = _("Disc %s") % disc.number
                label = Gtk.Label.new()
                label.set_ellipsize(Pango.EllipsizeMode.END)
                label.set_text(disc_text)
                label.set_property("halign", Gtk.Align.START)
                label.get_style_context().add_class("dim-label")
                label.show()
                eventbox = Gtk.EventBox()
                eventbox.connect("realize", set_cursor_type)
                eventbox.set_tooltip_text(_("Play"))
                eventbox.connect("button-press-event",
                                 self.__on_disc_button_press_event,
                                 disc)
                eventbox.add(label)
                eventbox.show()
                if orientation == Gtk.Orientation.VERTICAL:
                    self._responsive_widget.attach(
                        eventbox, 0, idx, 1, 1)
                else:
                    self._responsive_widget.attach(
                        eventbox, 0, idx, 2, 1)
                idx += 1
            if orientation == Gtk.Orientation.VERTICAL:
                self._responsive_widget.attach(
                          self._tracks_widget_left[disc.number],
                          0, idx, 2, 1)
                idx += 1
            else:
                self._responsive_widget.attach(
                          self._tracks_widget_left[disc.number],
                          0, idx, 1, 1)
            if not self.view_type & ViewType.SINGLE_COLUMN:
                if orientation == Gtk.Orientation.VERTICAL:
                    self._responsive_widget.attach(
                               self._tracks_widget_right[disc.number],
                               0, idx, 2, 1)
                else:
                    self._responsive_widget.attach(
                               self._tracks_widget_right[disc.number],
                               1, idx, 1, 1)
            idx += 1

    def _on_loading_changed(self, player, status, track):
        """
            Update row loading status
            @param player as Player
            @param status as bool
            @param track as Track
        """
        if self.__album.is_web:
            TracksView._on_loading_changed(self, player, status, track)

    def _on_album_updated(self, scanner, album_id):
        """
            On album modified, disable it
            @param scanner as CollectionScanner
            @param album_id as int
        """
        if self.__album.id != album_id:
            return
        removed = False
        for dic in [self._tracks_widget_left, self._tracks_widget_right]:
            for widget in dic.values():
                for child in widget.get_children():
                    if child.track.album.id == Type.NONE:
                        removed = True
        if removed:
            for dic in [self._tracks_widget_left, self._tracks_widget_right]:
                for widget in dic.values():
                    for child in widget.get_children():
                        child.destroy()
            self.__discs = list(self.__discs)
            self.__set_duration()
            self.populate()

    def __on_track_row_removed(self, row):
        """
            Pass signal
            @param row as TrackRow
        """
        emit_signal(self, "track-removed", row)

    def _on_activated(self, widget, track):
        """
            Handle playback if album or pass signal
            @param widget as TracksWidget
            @param track as Track
        """
        if self.view_type & ViewType.ALBUM:
            tracks = []
            for child in self.children:
                if child.track.loved != -1:
                    tracks.append(child.track)
                child.set_state_flags(Gtk.StateFlags.NORMAL, True)
            # Do not update album list if in party or album already available
            playback_track = App().player.track_in_playback(track)
            if playback_track is not None:
                App().player.load(playback_track)
            elif not App().player.is_party:
                album = Album(track.album.id, [], [])
                album.set_tracks(tracks)
                if not App().settings.get_value("append-albums"):
                    App().player.clear_albums()
                App().player.add_album(album)
                App().player.load(album.get_track(track.id))
            else:
                App().player.load(track)
        else:
            emit_signal(self, "activated", track)

#######################
# PRIVATE             #
#######################
    def __load_disc(self, items, disc_number, position=0):
        """
            Load discs
            @param items as (TrackWidget, [Tracks])
            @param disc_number as int
            @param position as int
        """
        if items:
            (widget, tracks) = items.pop(0)
            self._add_tracks(widget, tracks, position)
            position += len(tracks)
            widget.show()
            GLib.idle_add(self.__load_disc, items, disc_number, position)
        else:
            emit_signal(self, "populated")

    def __on_disc_button_press_event(self, button, event, disc):
        """
            Add disc to playback
            @param button as Gtk.Button
            @param event as Gdk.ButtonEvent
            @param disc as Disc
        """
        album = Album(disc.album.id)
        album.set_tracks(disc.tracks)
        App().player.play_album(album)
