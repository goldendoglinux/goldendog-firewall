import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio


class FirewallApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="org.goldendoglinux.firewall",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        from .window import FirewallWindow

        win = FirewallWindow(application=app)
        win.present()
