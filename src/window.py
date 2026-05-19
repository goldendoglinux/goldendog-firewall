import os
import json
import gettext

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk
from .style import apply_goldendog_accent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "..", "assets")
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


class FirewallWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("Goldendog Firewall"))
        self.set_default_size(760, 620)
        apply_goldendog_accent()
        self._register_icon()
        self.set_icon_name("firewall")
        self.rules_metadata = []
        self.interfaces = self._load_interfaces()

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        toolbar_view = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar_view)

        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(True)
        header.set_show_end_title_buttons(True)
        header.set_title_widget(Gtk.Label(label=_("Goldendog Firewall")))
        header.pack_start(self._build_menubar())
        toolbar_view.add_top_bar(header)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        toolbar_view.set_content(main_box)

        main_box.append(self._build_hero_header())
        main_box.append(self._build_status_section())
        main_box.append(self._build_settings_section())
        main_box.append(self._build_rules_section())

    # ── Icon registration ─────────────────────────────────────────────────────

    def _register_icon(self):
        icon_path = os.path.join(ASSETS_DIR, "firewall.svg")
        if os.path.isfile(icon_path):
            try:
                display = self.get_display()
                icon_theme = Gtk.IconTheme.get_for_display(display)
                icon_theme.add_search_path(ASSETS_DIR)
            except Exception as e:
                print(f"Warning: Could not register icon: {e}")

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menubar(self):
        self._setup_actions()

        menu_model = Gio.Menu()

        file_menu = Gio.Menu()
        file_menu.append(_("Exit"), "win.exit")
        menu_model.append_submenu(_("File"), file_menu)

        help_menu = Gio.Menu()
        help_menu.append(_("Help"), "win.help")
        help_menu.append(_("About"), "win.about")
        menu_model.append_submenu(_("Help"), help_menu)

        menubar = Gtk.PopoverMenuBar.new_from_model(menu_model)
        menubar.add_css_class("flat")
        return menubar

    def _setup_actions(self):
        exit_action = Gio.SimpleAction.new("exit", None)
        exit_action.connect("activate", lambda a, p: self.close())
        self.add_action(exit_action)

        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self._on_help)
        self.add_action(help_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

    def _on_help(self, _action, _param):
        dialog = self._build_dialog_shell(_("Documentation"), 340, 220)
        content = dialog.get_content()

        header = self._build_dialog_header(
            icon_name="text-x-generic-symbolic",
            title=_("Documentation"),
        )
        content.append(header)
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        body.set_margin_top(16)
        body.set_margin_bottom(16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        content.append(body)

        description = Gtk.Label(
            label=_(
                "Learn how to configure and use Goldendog Firewall from the official documentation."
            )
        )
        description.set_wrap(True)
        description.set_xalign(0.0)
        description.set_halign(Gtk.Align.START)
        description.add_css_class("dim-label")
        body.append(description)

        link_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        link_row.set_halign(Gtk.Align.START)
        link_icon = Gtk.Image.new_from_icon_name("adw-external-link-symbolic")
        link_icon.add_css_class("accent")
        link_row.append(link_icon)

        link = Gtk.Label()
        link.set_use_markup(True)
        link.set_markup(
            '<a href="https://goldendoglinux.org/docs/firewall">goldendoglinux.org/docs/firewall</a>'
        )
        link.set_xalign(0.0)
        link.set_halign(Gtk.Align.START)
        link.connect("activate-link", self._on_activate_link)
        link_row.append(link)
        body.append(link_row)

        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        content.append(self._build_dialog_footer(dialog))
        dialog.present()

    def _on_about(self, _action, _param):
        dialog = self._build_dialog_shell(_("About"), 340, 230)
        content = dialog.get_content()

        header = self._build_dialog_header(
            image_path=os.path.join(ASSETS_DIR, "firewall.svg"),
            title=_("Goldendog Firewall"),
            subtitle="v1.0.0",
        )
        content.append(header)
        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.set_margin_top(16)
        body.set_margin_bottom(16)
        body.set_margin_start(16)
        body.set_margin_end(16)
        content.append(body)

        description = Gtk.Label()
        description.set_use_markup(True)
        description.set_markup(
            _(
                'A simple UFW interface for <a href="https://goldendoglinux.org">Goldendog Linux</a>.'
            )
        )
        description.set_wrap(True)
        description.set_xalign(0.0)
        description.set_halign(Gtk.Align.START)
        description.connect("activate-link", self._on_activate_link)
        body.append(description)

        author_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        author_label = Gtk.Label(label=_("Author"))
        author_label.add_css_class("dim-label")
        author_label.set_xalign(0.0)
        author_label.set_halign(Gtk.Align.START)
        author_label.set_size_request(68, -1)
        author_row.append(author_label)
        author_link = Gtk.Label()
        author_link.set_use_markup(True)
        author_link.set_markup('<a href="https://github.com/alexiarstein">Alexia Michelle</a>')
        author_link.set_xalign(0.0)
        author_link.set_halign(Gtk.Align.START)
        author_link.connect("activate-link", self._on_activate_link)
        author_row.append(author_link)
        body.append(author_row)

        license_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        license_label = Gtk.Label(label=_("License"))
        license_label.add_css_class("dim-label")
        license_label.set_xalign(0.0)
        license_label.set_halign(Gtk.Align.START)
        license_label.set_size_request(68, -1)
        license_row.append(license_label)
        license_link = Gtk.Label()
        license_link.set_use_markup(True)
        license_link.set_markup(
            '<a href="https://www.gnu.org/licenses/gpl-3.0.html">GNU GPL v3.0</a>'
        )
        license_link.set_xalign(0.0)
        license_link.set_halign(Gtk.Align.START)
        license_link.connect("activate-link", self._on_activate_link)
        license_row.append(license_link)
        body.append(license_row)

        content.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        content.append(self._build_dialog_footer(dialog))
        dialog.present()

    def _build_dialog_shell(self, title, width, height):
        dialog = Adw.Window(transient_for=self, modal=True, title=title)
        dialog.set_default_size(width, height)
        dialog.set_resizable(False)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        dialog.set_content(content)
        return dialog

    def _build_dialog_header(self, title, subtitle=None, icon_name=None, image_path=None):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(12)
        header.set_margin_bottom(12)
        header.set_margin_start(16)
        header.set_margin_end(16)

        badge = Gtk.Box()
        badge.add_css_class("dialog-badge")
        badge.set_size_request(28, 28)
        badge.set_halign(Gtk.Align.START)
        badge.set_valign(Gtk.Align.START)

        if image_path and os.path.isfile(image_path):
            icon = Gtk.Image.new_from_file(image_path)
        else:
            icon = Gtk.Image.new_from_icon_name(icon_name or "dialog-information-symbolic")
        icon.set_pixel_size(15)
        badge.append(icon)
        header.append(badge)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        text_box.set_hexpand(True)
        header.append(text_box)

        title_label = Gtk.Label(label=title)
        title_label.set_xalign(0.0)
        title_label.set_halign(Gtk.Align.START)
        text_box.append(title_label)

        if subtitle:
            subtitle_label = Gtk.Label(label=subtitle)
            subtitle_label.set_xalign(0.0)
            subtitle_label.set_halign(Gtk.Align.START)
            subtitle_label.add_css_class("dim-label")
            subtitle_label.add_css_class("caption")
            text_box.append(subtitle_label)

        return header

    def _build_dialog_footer(self, dialog):
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        footer.set_margin_top(10)
        footer.set_margin_bottom(10)
        footer.set_margin_start(16)
        footer.set_margin_end(16)
        footer.set_halign(Gtk.Align.END)

        close_btn = Gtk.Button(label=_("Close"))
        close_btn.connect("clicked", lambda _btn: dialog.close())
        footer.append(close_btn)
        return footer

    def _on_activate_link(self, _label, uri):
        try:
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception:
            return True
        return True

    # ── Main sections ─────────────────────────────────────────────────────────

    def _build_hero_header(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        outer.set_margin_bottom(4)

        icon_path = os.path.join(ASSETS_DIR, "firewall.svg")
        if os.path.isfile(icon_path):
            shield = Gtk.Image.new_from_file(icon_path)
        else:
            shield = Gtk.Image.new_from_icon_name("security-high-symbolic")
        shield.set_pixel_size(84)
        shield.set_valign(Gtk.Align.CENTER)
        outer.append(shield)

        text_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_col.set_hexpand(True)
        text_col.set_valign(Gtk.Align.CENTER)
        outer.append(text_col)

        title = Gtk.Label()
        title.set_markup(f"<span size='x-large' weight='bold'>{_('Goldendog Firewall')}</span>")
        title.set_halign(Gtk.Align.START)
        text_col.append(title)

        subtitle = Gtk.Label(label=_("Protect your system enabling the firewall"))
        subtitle.set_halign(Gtk.Align.START)
        subtitle.add_css_class("dim-label")
        text_col.append(subtitle)

        return outer

    def _build_status_section(self):
        group = Adw.PreferencesGroup()
        group.set_title(_("Firewall Status"))

        row = Adw.ActionRow()
        row.set_title(_("Firewall"))
        row.set_subtitle(_("Turn firewall protection on or off"))
        self.status_switch = Gtk.Switch()
        self.status_switch.set_active(False)
        self.status_switch.set_valign(Gtk.Align.CENTER)
        row.add_suffix(self.status_switch)
        group.add(row)

        return group

    def _build_settings_section(self):
        group = Adw.PreferencesGroup()
        group.set_title(_("Firewall Settings"))

        incoming_row = Adw.ActionRow()
        incoming_row.set_title(_("Incoming"))
        incoming_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        incoming_box.set_valign(Gtk.Align.CENTER)
        self.incoming_accept_radio = Gtk.CheckButton(label=_("Accept"))
        self.incoming_deny_radio = Gtk.CheckButton(label=_("Deny"))
        self.incoming_deny_radio.set_group(self.incoming_accept_radio)
        self.incoming_deny_radio.set_active(True)
        incoming_box.append(self.incoming_accept_radio)
        incoming_box.append(self.incoming_deny_radio)
        incoming_row.add_suffix(incoming_box)
        group.add(incoming_row)

        outgoing_row = Adw.ActionRow()
        outgoing_row.set_title(_("Outgoing"))
        outgoing_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        outgoing_box.set_valign(Gtk.Align.CENTER)
        self.outgoing_accept_radio = Gtk.CheckButton(label=_("Accept"))
        self.outgoing_deny_radio = Gtk.CheckButton(label=_("Deny"))
        self.outgoing_deny_radio.set_group(self.outgoing_accept_radio)
        self.outgoing_accept_radio.set_active(True)
        outgoing_box.append(self.outgoing_accept_radio)
        outgoing_box.append(self.outgoing_deny_radio)
        outgoing_row.add_suffix(outgoing_box)
        group.add(outgoing_row)

        return group

    # ── Rules section ─────────────────────────────────────────────────────────

    def _build_rules_section(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_hexpand(True)
        box.set_vexpand(True)

        rules_title = Gtk.Label()
        rules_title.set_markup(f"<b>{_('Firewall Rules')}</b>")
        rules_title.set_halign(Gtk.Align.START)
        box.append(rules_title)

        # Scrollable rules list
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.append(scroll)

        # Model: (rule_number, rule_string, rule_name)
        self.rules_store = Gtk.ListStore(int, str, str)

        self.rules_view = Gtk.TreeView(model=self.rules_store)
        self.rules_view.set_headers_visible(True)
        self.rules_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.rules_view.set_activate_on_single_click(False)
        self._setup_rules_context_menu()

        num_renderer = Gtk.CellRendererText()
        col_num = Gtk.TreeViewColumn(_("Nº"), num_renderer, text=0)
        col_num.set_fixed_width(50)
        col_num.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.rules_view.append_column(col_num)

        rule_renderer = Gtk.CellRendererText()
        col_rule = Gtk.TreeViewColumn(_("Rule"), rule_renderer, text=1)
        col_rule.set_expand(True)
        self.rules_view.append_column(col_rule)

        name_renderer = Gtk.CellRendererText()
        col_name = Gtk.TreeViewColumn(_("Name"), name_renderer, text=2)
        col_name.set_expand(True)
        self.rules_view.append_column(col_name)

        scroll.set_child(self.rules_view)

        # Action bar (+ - edit)
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        action_bar.set_margin_top(4)
        action_bar.set_margin_bottom(2)
        box.append(action_bar)

        add_btn = self._build_asset_button("add.svg", _("Add rule"))
        add_btn.add_css_class("flat")
        add_btn.connect("clicked", self._on_add_rule)
        action_bar.append(add_btn)

        self.remove_btn = self._build_asset_button("remove.svg", _("Remove selected rule"))
        self.remove_btn.add_css_class("flat")
        self.remove_btn.connect("clicked", self._on_remove_rule)
        action_bar.append(self.remove_btn)

        self.edit_btn = self._build_asset_button("edit.svg", _("Edit selected rule"))
        self.edit_btn.add_css_class("flat")
        self.edit_btn.connect("clicked", self._on_edit_rule)
        action_bar.append(self.edit_btn)

        save_btn = Gtk.Button(label=_("Save and Apply Rules"))
        save_btn.add_css_class("pill")
        save_btn.add_css_class("suggested-action")
        save_btn.set_halign(Gtk.Align.END)
        save_btn.set_margin_top(4)
        save_btn.set_size_request(220, 42)
        save_btn.connect("clicked", self._on_save_rules)
        box.append(save_btn)

        return box

    # ── Rule actions (stubs — logic to be implemented) ────────────────────────

    def _on_add_rule(self, _button):
        from .add_rule_dialog import AddRuleDialog

        dialog = AddRuleDialog(transient_for=self, interfaces=self.interfaces)
        dialog.connect("rule-added", self._on_rule_added)
        dialog.present()

    def _on_rule_added(self, _dialog, rule_str, rule_name, metadata_json):
        n = len(self.rules_store) + 1
        self.rules_store.append([n, rule_str, rule_name])
        self.rules_metadata.append(json.loads(metadata_json))

    def _on_remove_rule(self, _button):
        index = self._get_selected_rule_index()
        self._delete_rule_by_index(index)

    def _on_edit_rule(self, _button):
        index = self._get_selected_rule_index()
        if index is None:
            return

        from .add_rule_dialog import AddRuleDialog

        dialog = AddRuleDialog(
            transient_for=self,
            initial_data=self.rules_metadata[index],
            interfaces=self.interfaces,
        )
        dialog.connect("rule-added", self._on_rule_edited, index)
        dialog.present()

    def _on_rule_edited(self, _dialog, rule_str, rule_name, metadata_json, index):
        if index is None or index < 0 or index >= len(self.rules_store):
            return
        self.rules_store[index][1] = rule_str
        self.rules_store[index][2] = rule_name
        self.rules_metadata[index] = json.loads(metadata_json)

    def _on_save_rules(self, _button):
        from .ufw_service import apply_firewall_configuration

        incoming_policy = "allow" if self.incoming_accept_radio.get_active() else "deny"
        outgoing_policy = "allow" if self.outgoing_accept_radio.get_active() else "deny"
        enabled = self.status_switch.get_active()

        rule_arg_sets = []
        for metadata in self.rules_metadata:
            for arg_set in metadata.get("ufw_arg_sets", []):
                rule_arg_sets.append(arg_set)

        ok, message = apply_firewall_configuration(
            enabled,
            incoming_policy,
            outgoing_policy,
            rule_arg_sets,
        )

        if ok:
            toast = Adw.Toast.new(_("Firewall configuration applied successfully."))
            self.toast_overlay.add_toast(toast)
            return

        dialog = Adw.MessageDialog.new(
            self,
            _("Could not apply firewall rules"),
            message,
        )
        dialog.add_response("ok", _("OK"))
        dialog.present()

    def _setup_rules_context_menu(self):
        self.rules_context_popover = Gtk.Popover()
        self.rules_context_popover.set_has_arrow(False)
        self.rules_context_popover.set_parent(self.rules_view)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        edit_btn = Gtk.Button(label=_("Edit"))
        edit_btn.add_css_class("flat")
        edit_btn.set_halign(Gtk.Align.FILL)
        edit_btn.connect("clicked", self._on_context_edit)
        menu_box.append(edit_btn)

        delete_btn = Gtk.Button(label=_("Delete"))
        delete_btn.add_css_class("flat")
        delete_btn.set_halign(Gtk.Align.FILL)
        delete_btn.connect("clicked", self._on_context_delete)
        menu_box.append(delete_btn)

        self.rules_context_popover.set_child(menu_box)

        gesture = Gtk.GestureClick()
        # Capture all pointer buttons and filter to secondary click in handler.
        gesture.set_button(0)
        gesture.connect("pressed", self._on_rules_right_click)
        self.rules_view.add_controller(gesture)

    def _on_rules_right_click(self, gesture, _n_press, x, y):
        if gesture.get_current_button() != Gdk.BUTTON_SECONDARY:
            return

        path_info = self.rules_view.get_path_at_pos(int(x), int(y))
        if path_info is not None:
            path, _column, _cell_x, _cell_y = path_info
            self.rules_view.set_cursor(path, None, False)
        elif self._get_selected_rule_index() is None:
            # No clicked row and no selected row: nothing to show actions for.
            return

        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        self.rules_context_popover.set_pointing_to(rect)
        self.rules_context_popover.popup()

    def _on_context_edit(self, _button):
        self.rules_context_popover.popdown()
        self._on_edit_rule(None)

    def _on_context_delete(self, _button):
        self.rules_context_popover.popdown()
        self._on_remove_rule(None)

    def _get_selected_rule_index(self):
        selection = self.rules_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return None
        path = model.get_path(tree_iter)
        indices = path.get_indices()
        if not indices:
            return None
        return indices[0]

    def _delete_rule_by_index(self, index):
        if index is None or index < 0 or index >= len(self.rules_store):
            return

        del self.rules_store[index]
        del self.rules_metadata[index]

        for i, row in enumerate(self.rules_store):
            row[0] = i + 1

    def _load_interfaces(self):
        from .ufw_service import list_network_interfaces

        return list_network_interfaces()

    def _build_asset_button(self, asset_name, tooltip):
        button = Gtk.Button()
        asset_path = os.path.join(ASSETS_DIR, asset_name)

        if os.path.isfile(asset_path):
            image = Gtk.Image.new_from_file(asset_path)
            image.set_pixel_size(16)
            button.set_child(image)
        button.set_tooltip_text(tooltip)
        return button
