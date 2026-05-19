import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gdk, Gtk


def apply_goldendog_accent():
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(
        b"""
        switch:checked {
            background-color: #02c265;
        }

        checkbutton:checked > check,
        checkbutton:checked > radio {
            background-color: #02c265;
            border-color: #02c265;
        }

        button.suggested-action {
            background: #02c265;
            color: #ffffff;
            border-color: #02c265;
        }

        button.suggested-action:hover {
            background: #15d36f;
            border-color: #15d36f;
        }

        button.suggested-action:active {
            background: #01a755;
            border-color: #01a755;
        }

        .dialog-badge {
            background: rgba(2, 194, 101, 0.18);
            border-radius: 9px;
            padding: 6px;
        }
        """
    )
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
