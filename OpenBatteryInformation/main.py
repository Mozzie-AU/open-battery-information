#!/usr/bin/env python3
# OBI-1 Diagnostic Tool
# Copyright (C) 2026 Ray Ellison
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Portions Derived from "Open Battery Information" 
# Copyright (c) 2024 Martin Jansson (MIT License)

import gi
import os
import sys
import threading
import re

# 1. FIX PATHS
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk

# 2. ROBUST IMPORTS
try:
    from interfaces.arduino_obi import SerialInterface
    from modules.makita_lxt import MakitaModule
    print("Modules loaded successfully.")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)

class ObiApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id="org.obi.diagnostic.v1", **kwargs)
        self.comm = None
        self.makita = None

    def do_activate(self):
        self.win = Adw.ApplicationWindow(application=self)
        self.win.set_default_size(1100, 950)

        # Backend Init
        if self.comm is None:
            self.comm = SerialInterface(debug_callback=self.update_debug)
            self.makita = MakitaModule(self.comm)

        # --- NEW TOP-LEVEL LAYOUT ---
        outer_storage = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # HeaderBar with Centered Title
        header_bar = Adw.HeaderBar()
        title_widget = Adw.WindowTitle(title="OBI-1: Makita LXT Diagnostic")
        header_bar.set_title_widget(title_widget)
        outer_storage.append(header_bar)

        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        outer_storage.append(main_box)
        
        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sidebar.set_margin_top(16)
        sidebar.set_margin_bottom(16)
        sidebar.set_margin_start(16)
        sidebar.set_margin_end(16)
        sidebar.set_size_request(280, -1)
        
        sidebar.append(Gtk.Label(label="Connection", xalign=0))
        
        raw_ports = self.comm.get_available_ports() or []
        sorted_ports = sorted(raw_ports, reverse=True) 
        display_ports = sorted_ports if sorted_ports else ["No Ports Found"]
        
        self.port_dropdown = Gtk.DropDown.new_from_strings(display_ports)
        sidebar.append(self.port_dropdown)

        self.btn_connect = Gtk.Button(label="Connect")
        self.btn_connect.add_css_class("suggested-action")
        self.btn_connect.connect("clicked", self.on_connect_toggle)
        sidebar.append(self.btn_connect)
        main_box.append(sidebar)

        # Content Area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20, hexpand=True)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)

        # Buttons Grid (3 Columns)
        btn_grid = Gtk.Grid(column_spacing=12, row_spacing=12, halign=Gtk.Align.CENTER)
        
        self.btn_read_static = Gtk.Button(label="Read Model")
        self.btn_read_static.connect("clicked", lambda x: self.run_async(self.do_read_static))
        
        self.btn_read_live = Gtk.Button(label="Read Live")
        self.btn_read_live.connect("clicked", lambda x: self.run_async(self.do_read_live))

        self.btn_led_on = Gtk.Button(label="LEDs ON")
        self.btn_led_on.connect("clicked", lambda x: self.run_async(lambda: self.makita.set_leds(True)))

        self.btn_led_off = Gtk.Button(label="LEDs OFF")
        self.btn_led_off.connect("clicked", lambda x: self.run_async(lambda: self.makita.set_leds(False)))
        
        self.btn_clear_errors = Gtk.Button(label="Clear Battery Errors")
        self.btn_clear_errors.add_css_class("destructive-action") 
        self.btn_clear_errors.connect("clicked", self.on_clear_clicked)

        btn_grid.attach(self.btn_read_static, 0, 0, 1, 1)
        btn_grid.attach(self.btn_read_live, 1, 0, 1, 1)
        btn_grid.attach(self.btn_led_on, 2, 0, 1, 1)
        btn_grid.attach(self.btn_clear_errors, 0, 1, 2, 1)
        btn_grid.attach(self.btn_led_off, 2, 1, 1, 1)
        
        content.append(btn_grid)

        # Data Display List
        self.data_list = Gtk.ListBox()
        self.data_list.add_css_class("boxed-list")
        self.data_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.rows = {} 
        params = ["Model", "ROM ID", "Charge count", "State", "Pack Voltage", 
                  "Cell 1", "Cell 2", "Cell 3", "Cell 4", "Cell 5", "Temp Cell"]
        for p in params:
            row = Adw.ActionRow(title=p)
            row.set_subtitle("---")
            self.data_list.append(row)
            self.rows[p] = row

        scroll = Gtk.ScrolledWindow(min_content_height=400, vexpand=True)
        scroll.set_child(self.data_list)
        content.append(scroll)

        # Log View
        debug_frame = Gtk.Frame(label="Serial Communication Log")
        self.debug_buffer = Gtk.TextBuffer()
        self.debug_view = Gtk.TextView(buffer=self.debug_buffer, editable=False)
        log_scroll = Gtk.ScrolledWindow(min_content_height=180, vexpand=False)
        log_scroll.set_child(self.debug_view)
        debug_frame.set_child(log_scroll)
        content.append(debug_frame)

        main_box.append(content)
        
        self.win.set_content(outer_storage)
        self.win.present()

    def update_ui_rows(self, data_dict):
        for key, value in data_dict.items():
            if key in self.rows:
                color = "#3584e4"  # Default Blue
                
                # 1. Check for low voltage on Cells (< 2.5V)
                if key.startswith("Cell"):
                    try:
                        # Extract numeric value (e.g., "2.4V" -> 2.4)
                        num_val = float(re.findall(r"\d+\.\d+", str(value))[0])
                        if num_val < 2.5:
                            color = "#e01b24"  # Adwaita Red
                    except (ValueError, IndexError):
                        pass
                
                # 2. Check for high temperature (> 60°C)
                elif key == "Temp Cell":
                    try:
                        # Extract numeric value (e.g., "62C" -> 62)
                        temp_val = float(re.findall(r"\d+", str(value))[0])
                        if temp_val >= 60:
                            color = "#e01b24"  # Adwaita Red
                    except (ValueError, IndexError):
                        pass

                markup = f"<span weight='heavy' size='large' color='{color}'>{value}</span>"
                self.rows[key].set_subtitle(markup)
                self.rows[key].set_use_markup(True)

    def on_connect_toggle(self, btn):
        if not self.comm.serial.is_open:
            port_idx = self.port_dropdown.get_selected()
            if port_idx == Gtk.INVALID_LIST_POSITION: return
            port_name = self.port_dropdown.get_model().get_string(port_idx)
            if self.comm.connect(port_name):
                btn.set_label("Disconnect")
                btn.add_css_class("destructive-action")
        else:
            self.comm.disconnect()
            btn.set_label("Connect")
            btn.remove_css_class("destructive-action")

    def on_clear_clicked(self, btn):
        btn.set_sensitive(False)
        def run():
            success = self.makita.clear_battery_errors()
            GLib.idle_add(lambda: btn.set_sensitive(True))
            if success:
                self.run_async(self.do_read_live)
        threading.Thread(target=run, daemon=True).start()

    def do_read_static(self):
        data = self.makita.read_static_info()
        GLib.idle_add(self.update_ui_rows, data)

    def do_read_live(self):
        data = self.makita.read_live_data()
        GLib.idle_add(self.update_ui_rows, data)

    def run_async(self, func):
        threading.Thread(target=func, daemon=True).start()

    def update_debug(self, text):
        GLib.idle_add(self._append_debug, text)

    def _append_debug(self, text):
        end_iter = self.debug_buffer.get_end_iter()
        self.debug_buffer.insert(end_iter, f"{text}\n")
        mark = self.debug_buffer.create_mark(None, self.debug_buffer.get_end_iter(), False)
        self.debug_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

if __name__ == "__main__":
    app = ObiApp()
    sys.exit(app.run(sys.argv))
