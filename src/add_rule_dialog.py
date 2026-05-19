import gi
import json
import os
import gettext

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GObject, Gtk
from .style import apply_goldendog_accent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_LOCALE_DIR = "/usr/share/locale"
LOCAL_LOCALE_DIR = os.path.join(SCRIPT_DIR, "..", "locale")
LOCALE_DIR = (
    SYSTEM_LOCALE_DIR
    if os.path.exists(os.path.join(SYSTEM_LOCALE_DIR, "es", "LC_MESSAGES", "goldendog-firewall.mo"))
    else LOCAL_LOCALE_DIR
)

gettext.bindtextdomain("goldendog-firewall", LOCALE_DIR)
gettext.textdomain("goldendog-firewall")
_ = gettext.gettext


class AddRuleDialog(Adw.Window):
    """
    Dialog to add a new firewall rule.
    Emits 'rule-added' with (rule_str, rule_name, metadata_json) when the user clicks Add.
    """

    __gsignals__ = {
        "rule-added": (GObject.SignalFlags.RUN_FIRST, None, (str, str, str)),
    }

    def __init__(self, transient_for=None, initial_data=None, interfaces=None):
        super().__init__()
        self.set_title(_("Add a Firewall Rule"))
        apply_goldendog_accent()
        self.interfaces = [_("All Interfaces")]
        if interfaces:
            for iface in interfaces:
                if iface and iface != _("All Interfaces") and iface not in self.interfaces:
                    self.interfaces.append(iface)
        self.set_default_size(540, 460)
        self.set_modal(True)
        self.set_resizable(False)
        if transient_for:
            self.set_transient_for(transient_for)

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(True)
        toolbar_view.add_top_bar(header)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_view.set_content(outer)

        # ── Notebook (Simple / Advanced) ──────────────────────────────────────
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        self.notebook.set_show_border(False)
        outer.append(self.notebook)

        self.notebook.append_page(
            self._build_simple_tab(), Gtk.Label(label=_("Simple"))
        )
        self.notebook.append_page(
            self._build_advanced_tab(), Gtk.Label(label=_("Advanced"))
        )

        outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # ── Bottom buttons ────────────────────────────────────────────────────
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(10)
        btn_box.set_margin_bottom(10)
        btn_box.set_margin_end(12)
        outer.append(btn_box)

        close_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        close_box.append(Gtk.Image.new_from_icon_name("window-close-symbolic"))
        close_box.append(Gtk.Label(label=_("Close")))
        close_btn = Gtk.Button()
        close_btn.set_child(close_box)
        close_btn.connect("clicked", lambda _: self.close())
        btn_box.append(close_btn)

        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        add_box.append(Gtk.Image.new_from_icon_name("list-add-symbolic"))
        add_label = _("Save") if initial_data else _("Add")
        add_box.append(Gtk.Label(label=add_label))
        add_btn = Gtk.Button()
        add_btn.set_child(add_box)
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_clicked)
        btn_box.append(add_btn)

        if initial_data:
            self._load_initial_data(initial_data)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _form_row(self, label_text, widget):
        """Return a horizontal box with a fixed-width label and a widget."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        lbl = Gtk.Label(label=label_text)
        lbl.set_halign(Gtk.Align.START)
        lbl.set_size_request(90, -1)
        box.append(lbl)
        box.append(widget)
        return box

    def _dropdown(self, items):
        dd = Gtk.DropDown.new_from_strings(items)
        dd.set_hexpand(True)
        return dd

    def _entry(self, placeholder):
        e = Gtk.Entry()
        e.set_placeholder_text(placeholder)
        e.set_hexpand(True)
        return e

    def _set_dropdown_text(self, dropdown, text):
        model = dropdown.get_model()
        if model is None:
            return
        for idx in range(model.get_n_items()):
            item = model.get_item(idx)
            if item and item.get_string() == text:
                dropdown.set_selected(idx)
                return

    def _load_initial_data(self, data):
        mode = data.get("mode", "simple")
        if mode == "advanced":
            self.notebook.set_current_page(1)
            self.a_name.set_text(data.get("name", ""))
            self._set_dropdown_text(self.a_policy, data.get("policy", _("Allow")))
            self._set_dropdown_text(self.a_direction, data.get("direction", _("In")))
            self._set_dropdown_text(self.a_interface, data.get("interface", _("All Interfaces")))
            self._set_dropdown_text(self.a_protocol, data.get("protocol", _("Both")))
            self.a_from_ip.set_text(data.get("from_ip", ""))
            self.a_from_port.set_text(data.get("from_port", ""))
            self.a_to_ip.set_text(data.get("to_ip", ""))
            self.a_to_port.set_text(data.get("to_port", ""))
            return

        self.notebook.set_current_page(0)
        self.s_name.set_text(data.get("name", ""))
        self._set_dropdown_text(self.s_policy, data.get("policy", _("Allow")))
        self._set_dropdown_text(self.s_direction, data.get("direction", _("In")))
        self._set_dropdown_text(self.s_protocol, data.get("protocol", _("Both")))
        self._set_dropdown_text(self.s_interface, data.get("interface", _("All Interfaces")))
        self.s_port.set_text(data.get("port", ""))

    # ── Simple tab ────────────────────────────────────────────────────────────

    def _build_simple_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        self.s_name = self._entry(_("Rule description"))
        box.append(self._form_row(_("Name:"), self.s_name))

        self.s_policy = self._dropdown([_("Allow"), _("Deny"), _("Reject")])
        box.append(self._form_row(_("Policy:"), self.s_policy))

        self.s_direction = self._dropdown([_("In"), _("Out"), _("Both")])
        box.append(self._form_row(_("Direction:"), self.s_direction))

        self.s_protocol = self._dropdown(["TCP", "UDP", _("Both")])
        box.append(self._form_row(_("Protocol:"), self.s_protocol))

        self.s_interface = self._dropdown(self.interfaces)
        box.append(self._form_row(_("Interface:"), self.s_interface))

        port_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        port_box.set_hexpand(True)
        self.s_port = self._entry(_("Port or service"))
        port_box.append(self.s_port)
        port_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        port_btn.add_css_class("circular")
        port_btn.set_tooltip_text(_("Browse services"))
        port_box.append(port_btn)
        box.append(self._form_row(_("Port:"), port_box))

        return box

    # ── Advanced tab ──────────────────────────────────────────────────────────

    def _build_advanced_tab(self):
        """
        Advanced rules can override simple ones.
        Example: deny all incoming but allow port 80 for a web server.
        No 'Insert position' or 'Log' fields — kept intentionally simple.
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        self.a_name = self._entry(_("Rule description"))
        box.append(self._form_row(_("Name:"), self.a_name))

        self.a_policy = self._dropdown([_("Allow"), _("Deny"), _("Reject")])
        box.append(self._form_row(_("Policy:"), self.a_policy))

        self.a_direction = self._dropdown([_("In"), _("Out"), _("Both")])
        box.append(self._form_row(_("Direction:"), self.a_direction))

        self.a_interface = self._dropdown(self.interfaces)
        box.append(self._form_row(_("Interface:"), self.a_interface))

        self.a_protocol = self._dropdown(["TCP", "UDP", _("Both")])
        box.append(self._form_row(_("Protocol:"), self.a_protocol))

        # From: IP + IP picker + Port
        from_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        from_box.set_hexpand(True)
        self.a_from_ip = self._entry(_("IP / network"))
        from_ip_btn = Gtk.Button.new_from_icon_name("network-wired-symbolic")
        from_ip_btn.add_css_class("circular")
        from_ip_btn.set_tooltip_text(_("Pick address"))
        self.a_from_port = self._entry(_("Port"))
        from_box.append(self.a_from_ip)
        from_box.append(from_ip_btn)
        from_box.append(self.a_from_port)
        box.append(self._form_row(_("From:"), from_box))

        # To: IP + IP picker + Port
        to_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        to_box.set_hexpand(True)
        self.a_to_ip = self._entry(_("IP / network"))
        to_ip_btn = Gtk.Button.new_from_icon_name("network-wired-symbolic")
        to_ip_btn.add_css_class("circular")
        to_ip_btn.set_tooltip_text(_("Pick address"))
        self.a_to_port = self._entry(_("Port"))
        to_box.append(self.a_to_ip)
        to_box.append(to_ip_btn)
        to_box.append(self.a_to_port)
        box.append(self._form_row(_("To:"), to_box))

        return box

    # ── Add button handler (stub) ─────────────────────────────────────────────

    def _on_add_clicked(self, _button):
        page = self.notebook.get_current_page()

        if page == 0:
            # Simple rule
            policy = self._selected_text(self.s_policy)
            direction = self._selected_text(self.s_direction)
            protocol = self._selected_text(self.s_protocol)
            interface = self._selected_text(self.s_interface)
            port = self.s_port.get_text().strip()
            name = self.s_name.get_text().strip()

            parts = [policy.lower(), direction.lower()]
            if interface != _("All Interfaces"):
                parts.append(f"on {interface}")
            if protocol != _("Both"):
                parts.append(protocol.lower())
            if port:
                parts.append(port)
            rule_str = " ".join(parts)

            ufw_arg_sets = self._build_simple_ufw_args(policy, direction, protocol, interface, port)
            metadata = {
                "mode": "simple",
                "name": name,
                "policy": policy,
                "direction": direction,
                "protocol": protocol,
                "interface": interface,
                "port": port,
                "rule_str": rule_str,
                "ufw_arg_sets": ufw_arg_sets,
            }
        else:
            # Advanced rule
            policy = self._selected_text(self.a_policy)
            direction = self._selected_text(self.a_direction)
            protocol = self._selected_text(self.a_protocol)
            interface = self._selected_text(self.a_interface)
            from_ip = self.a_from_ip.get_text().strip()
            from_port = self.a_from_port.get_text().strip()
            to_ip = self.a_to_ip.get_text().strip()
            to_port = self.a_to_port.get_text().strip()
            name = self.a_name.get_text().strip()

            parts = [policy.lower(), direction.lower()]
            if interface != _("All Interfaces"):
                parts.append(f"on {interface}")
            if protocol != _("Both"):
                parts.append(protocol.lower())
            if from_ip or from_port:
                from_part = "from"
                if from_ip:
                    from_part += f" {from_ip}"
                if from_port:
                    from_part += f" port {from_port}"
                parts.append(from_part)
            if to_ip or to_port:
                to_part = "to"
                if to_ip:
                    to_part += f" {to_ip}"
                if to_port:
                    to_part += f" port {to_port}"
                parts.append(to_part)
            rule_str = " ".join(parts)

            ufw_arg_sets = self._build_advanced_ufw_args(
                policy,
                direction,
                protocol,
                interface,
                from_ip,
                from_port,
                to_ip,
                to_port,
            )
            metadata = {
                "mode": "advanced",
                "name": name,
                "policy": policy,
                "direction": direction,
                "protocol": protocol,
                "interface": interface,
                "from_ip": from_ip,
                "from_port": from_port,
                "to_ip": to_ip,
                "to_port": to_port,
                "rule_str": rule_str,
                "ufw_arg_sets": ufw_arg_sets,
            }

        if rule_str and metadata["ufw_arg_sets"]:
            self.emit("rule-added", rule_str, name, json.dumps(metadata))
            self.close()

    def _selected_text(self, dropdown):
        item = dropdown.get_selected_item()
        return item.get_string() if item else ""

    def _build_simple_ufw_args(self, policy, direction, protocol, interface, port):
        action = policy.lower()
        directions = ["in", "out"] if direction == _("Both") else [direction.lower()]
        arg_sets = []

        for current_direction in directions:
            args = [action, current_direction]
            if interface != _("All Interfaces"):
                args.extend(["on", interface])

            if port:
                args.extend(["to", "any", "port", port])

            if protocol != _("Both"):
                args.extend(["proto", protocol.lower()])

            arg_sets.append(args)

        return arg_sets

    def _build_advanced_ufw_args(
        self,
        policy,
        direction,
        protocol,
        interface,
        from_ip,
        from_port,
        to_ip,
        to_port,
    ):
        action = policy.lower()
        directions = ["in", "out"] if direction == _("Both") else [direction.lower()]
        arg_sets = []

        for current_direction in directions:
            args = [action, current_direction]
            if interface != _("All Interfaces"):
                args.extend(["on", interface])

            if protocol != _("Both"):
                args.extend(["proto", protocol.lower()])

            args.extend(["from", from_ip if from_ip else "any"])
            if from_port:
                args.extend(["port", from_port])

            args.extend(["to", to_ip if to_ip else "any"])
            if to_port:
                args.extend(["port", to_port])

            arg_sets.append(args)

        return arg_sets
