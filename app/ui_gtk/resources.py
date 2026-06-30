"""A small always-visible CPU / RAM readout for the header bar.

Cheap, system-wide sampling — the same approach as the sysmon-widget: each
tick is just two ``psutil`` calls that read one ``/proc`` file apiece
(``cpu_percent(interval=None)`` → ``/proc/stat``, ``virtual_memory()`` →
``/proc/meminfo``). No process-tree walk (which would scan all of ``/proc``
every tick and drive the app's own CPU up), so the monitor stays nearly
free while still spiking visibly when ffmpeg / magick run.
"""

from __future__ import annotations

import psutil
from gi.repository import GLib, Gtk

_INTERVAL_SECONDS = 2
_MB = 1024 * 1024


class ResourceMonitor:
    """Owns a label widget (``.widget``) that self-updates with CPU / RAM."""

    def __init__(self) -> None:
        self.widget = Gtk.Label(label="CPU —  ·  RAM —")
        self.widget.add_css_class("resource-monitor")
        self.widget.set_tooltip_text("System CPU and memory in use")

        psutil.cpu_percent(interval=None)  # prime the baseline for the first delta
        self._tick()
        self._source_id = GLib.timeout_add_seconds(_INTERVAL_SECONDS, self._tick)

    def _tick(self) -> bool:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        used_mb = round((memory.total - memory.available) / _MB)
        self.widget.set_label(f"CPU {cpu:.0f}%  ·  RAM {used_mb} MB")
        return True  # keep the timeout alive

    def stop(self) -> None:
        if getattr(self, "_source_id", 0):
            GLib.source_remove(self._source_id)
            self._source_id = 0
