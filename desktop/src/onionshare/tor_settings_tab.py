# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from PySide2 import QtCore, QtWidgets, QtGui
import sys
import platform
import re
import os

from onionshare_cli.settings import Settings
from onionshare_cli.onion import Onion

from . import strings
from .widgets import Alert
from .tor_connection import TorConnectionWidget
from .moat_dialog import MoatDialog


class TorSettingsTab(QtWidgets.QWidget):
    """
    Settings dialog.
    """

    close_this_tab = QtCore.Signal()

    def __init__(self, common, tab_id):
        super(TorSettingsTab, self).__init__()

        self.common = common
        self.common.log("TorSettingsTab", "__init__")

        self.system = platform.system()
        self.tab_id = tab_id

        # Connection type: either automatic, control port, or socket file

        # Bundled Tor
        self.connection_type_bundled_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_bundled_option")
        )
        self.connection_type_bundled_radio.toggled.connect(
            self.connection_type_bundled_toggled
        )

        # Bundled Tor doesn't work on dev mode in Windows or Mac
        if (self.system == "Windows" or self.system == "Darwin") and getattr(
            sys, "onionshare_dev_mode", False
        ):
            self.connection_type_bundled_radio.setEnabled(False)

        # Bridge options for bundled tor

        (
            self.tor_path,
            self.tor_geo_ip_file_path,
            self.tor_geo_ipv6_file_path,
            self.obfs4proxy_file_path,
            self.snowflake_file_path,
        ) = self.common.gui.get_tor_paths()

        bridges_label = QtWidgets.QLabel(strings._("gui_settings_tor_bridges_label"))
        bridges_label.setWordWrap(True)

        self.bridge_use_checkbox = QtWidgets.QCheckBox(
            strings._("gui_settings_bridge_use_checkbox")
        )
        self.bridge_use_checkbox.stateChanged.connect(
            self.bridge_use_checkbox_state_changed
        )

        # Built-in bridge
        self.bridge_builtin_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_radio_builtin")
        )
        self.bridge_builtin_radio.toggled.connect(self.bridge_builtin_radio_toggled)
        self.bridge_builtin_dropdown = QtWidgets.QComboBox()
        self.bridge_builtin_dropdown.currentTextChanged.connect(
            self.bridge_builtin_dropdown_changed
        )
        if self.obfs4proxy_file_path and os.path.isfile(self.obfs4proxy_file_path):
            self.bridge_builtin_dropdown.addItem("obfs4")
            self.bridge_builtin_dropdown.addItem("meek-azure")
        if self.snowflake_file_path and os.path.isfile(self.snowflake_file_path):
            self.bridge_builtin_dropdown.addItem("snowflake")

        # Request a bridge from torproject.org (moat)
        self.bridge_moat_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_moat_radio_option")
        )
        self.bridge_moat_radio.toggled.connect(self.bridge_moat_radio_toggled)
        self.bridge_moat_button = QtWidgets.QPushButton(
            strings._("gui_settings_bridge_moat_button")
        )
        self.bridge_moat_button.clicked.connect(self.bridge_moat_button_clicked)
        self.bridge_moat_textbox = QtWidgets.QPlainTextEdit()
        self.bridge_moat_textbox.setMinimumHeight(100)
        self.bridge_moat_textbox.setMaximumHeight(100)
        self.bridge_moat_textbox.setReadOnly(True)
        self.bridge_moat_textbox.setWordWrapMode(QtGui.QTextOption.NoWrap)
        bridge_moat_textbox_options_layout = QtWidgets.QVBoxLayout()
        bridge_moat_textbox_options_layout.addWidget(self.bridge_moat_button)
        bridge_moat_textbox_options_layout.addWidget(self.bridge_moat_textbox)
        self.bridge_moat_textbox_options = QtWidgets.QWidget()
        self.bridge_moat_textbox_options.setLayout(bridge_moat_textbox_options_layout)
        self.bridge_moat_textbox_options.hide()

        # Custom bridges radio and textbox
        self.bridge_custom_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_bridge_custom_radio_option")
        )
        self.bridge_custom_radio.toggled.connect(self.bridge_custom_radio_toggled)
        self.bridge_custom_textbox = QtWidgets.QPlainTextEdit()
        self.bridge_custom_textbox.setMinimumHeight(100)
        self.bridge_custom_textbox.setMaximumHeight(100)
        self.bridge_custom_textbox.setPlaceholderText(
            strings._("gui_settings_bridge_custom_placeholder")
        )

        bridge_custom_textbox_options_layout = QtWidgets.QVBoxLayout()
        bridge_custom_textbox_options_layout.addWidget(self.bridge_custom_textbox)

        self.bridge_custom_textbox_options = QtWidgets.QWidget()
        self.bridge_custom_textbox_options.setLayout(
            bridge_custom_textbox_options_layout
        )
        self.bridge_custom_textbox_options.hide()

        # Bridge settings layout
        bridge_settings_layout = QtWidgets.QVBoxLayout()
        bridge_settings_layout.addWidget(self.bridge_builtin_radio)
        bridge_settings_layout.addWidget(self.bridge_builtin_dropdown)
        bridge_settings_layout.addWidget(self.bridge_moat_radio)
        bridge_settings_layout.addWidget(self.bridge_moat_textbox_options)
        bridge_settings_layout.addWidget(self.bridge_custom_radio)
        bridge_settings_layout.addWidget(self.bridge_custom_textbox_options)
        self.bridge_settings = QtWidgets.QWidget()
        self.bridge_settings.setLayout(bridge_settings_layout)

        # Bridges layout/widget
        bridges_layout = QtWidgets.QVBoxLayout()
        bridges_layout.addWidget(bridges_label)
        bridges_layout.addWidget(self.bridge_use_checkbox)
        bridges_layout.addWidget(self.bridge_settings)

        self.bridges = QtWidgets.QWidget()
        self.bridges.setLayout(bridges_layout)

        # Automatic
        self.connection_type_automatic_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_automatic_option")
        )
        self.connection_type_automatic_radio.toggled.connect(
            self.connection_type_automatic_toggled
        )

        # Control port
        self.connection_type_control_port_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_control_port_option")
        )
        self.connection_type_control_port_radio.toggled.connect(
            self.connection_type_control_port_toggled
        )

        connection_type_control_port_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_control_port_label")
        )
        self.connection_type_control_port_extras_address = QtWidgets.QLineEdit()
        self.connection_type_control_port_extras_port = QtWidgets.QLineEdit()
        connection_type_control_port_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_control_port_extras_layout.addWidget(
            connection_type_control_port_extras_label
        )
        connection_type_control_port_extras_layout.addWidget(
            self.connection_type_control_port_extras_address
        )
        connection_type_control_port_extras_layout.addWidget(
            self.connection_type_control_port_extras_port
        )

        self.connection_type_control_port_extras = QtWidgets.QWidget()
        self.connection_type_control_port_extras.setLayout(
            connection_type_control_port_extras_layout
        )
        self.connection_type_control_port_extras.hide()

        # Socket file
        self.connection_type_socket_file_radio = QtWidgets.QRadioButton(
            strings._("gui_settings_connection_type_socket_file_option")
        )
        self.connection_type_socket_file_radio.toggled.connect(
            self.connection_type_socket_file_toggled
        )

        connection_type_socket_file_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_socket_file_label")
        )
        self.connection_type_socket_file_extras_path = QtWidgets.QLineEdit()
        connection_type_socket_file_extras_layout = QtWidgets.QHBoxLayout()
        connection_type_socket_file_extras_layout.addWidget(
            connection_type_socket_file_extras_label
        )
        connection_type_socket_file_extras_layout.addWidget(
            self.connection_type_socket_file_extras_path
        )

        self.connection_type_socket_file_extras = QtWidgets.QWidget()
        self.connection_type_socket_file_extras.setLayout(
            connection_type_socket_file_extras_layout
        )
        self.connection_type_socket_file_extras.hide()

        # Tor SOCKS address and port
        gui_settings_socks_label = QtWidgets.QLabel(
            strings._("gui_settings_socks_label")
        )
        self.connection_type_socks_address = QtWidgets.QLineEdit()
        self.connection_type_socks_port = QtWidgets.QLineEdit()
        connection_type_socks_layout = QtWidgets.QHBoxLayout()
        connection_type_socks_layout.addWidget(gui_settings_socks_label)
        connection_type_socks_layout.addWidget(self.connection_type_socks_address)
        connection_type_socks_layout.addWidget(self.connection_type_socks_port)

        self.connection_type_socks = QtWidgets.QWidget()
        self.connection_type_socks.setLayout(connection_type_socks_layout)
        self.connection_type_socks.hide()

        # Authentication options
        self.authenticate_no_auth_checkbox = QtWidgets.QCheckBox(
            strings._("gui_settings_authenticate_no_auth_option")
        )
        self.authenticate_no_auth_checkbox.toggled.connect(
            self.authenticate_no_auth_toggled
        )

        authenticate_password_extras_label = QtWidgets.QLabel(
            strings._("gui_settings_password_label")
        )
        self.authenticate_password_extras_password = QtWidgets.QLineEdit("")
        authenticate_password_extras_layout = QtWidgets.QHBoxLayout()
        authenticate_password_extras_layout.addWidget(
            authenticate_password_extras_label
        )
        authenticate_password_extras_layout.addWidget(
            self.authenticate_password_extras_password
        )

        self.authenticate_password_extras = QtWidgets.QWidget()
        self.authenticate_password_extras.setLayout(authenticate_password_extras_layout)
        self.authenticate_password_extras.hide()

        # Group for Tor settings
        tor_settings_layout = QtWidgets.QVBoxLayout()
        tor_settings_layout.addWidget(self.connection_type_control_port_extras)
        tor_settings_layout.addWidget(self.connection_type_socket_file_extras)
        tor_settings_layout.addWidget(self.connection_type_socks)
        tor_settings_layout.addWidget(self.authenticate_no_auth_checkbox)
        tor_settings_layout.addWidget(self.authenticate_password_extras)
        self.tor_settings_group = QtWidgets.QGroupBox(
            strings._("gui_settings_controller_extras_label")
        )
        self.tor_settings_group.setLayout(tor_settings_layout)
        self.tor_settings_group.hide()

        # Put the radios into their own group so they are exclusive
        connection_type_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_radio_group_layout.addWidget(self.connection_type_bundled_radio)
        connection_type_radio_group_layout.addWidget(
            self.connection_type_automatic_radio
        )
        connection_type_radio_group_layout.addWidget(
            self.connection_type_control_port_radio
        )
        connection_type_radio_group_layout.addWidget(
            self.connection_type_socket_file_radio
        )
        connection_type_radio_group_layout.addStretch()
        connection_type_radio_group = QtWidgets.QGroupBox(
            strings._("gui_settings_connection_type_label")
        )
        connection_type_radio_group.setLayout(connection_type_radio_group_layout)

        # The Bridges options are not exclusive (enabling Bridges offers obfs4 or custom bridges)
        connection_type_bridges_radio_group_layout = QtWidgets.QVBoxLayout()
        connection_type_bridges_radio_group_layout.addWidget(self.bridges)
        self.connection_type_bridges_radio_group = QtWidgets.QGroupBox(
            strings._("gui_settings_tor_bridges")
        )
        self.connection_type_bridges_radio_group.setLayout(
            connection_type_bridges_radio_group_layout
        )
        self.connection_type_bridges_radio_group.hide()

        # Connection type layout
        connection_type_layout = QtWidgets.QVBoxLayout()
        connection_type_layout.addWidget(self.tor_settings_group)
        connection_type_layout.addWidget(self.connection_type_bridges_radio_group)
        connection_type_layout.addStretch()

        # Settings are in columns
        columns_layout = QtWidgets.QHBoxLayout()
        columns_layout.addWidget(connection_type_radio_group)
        columns_layout.addSpacing(20)
        columns_layout.addLayout(connection_type_layout, stretch=1)
        columns_wrapper = QtWidgets.QWidget()
        columns_wrapper.setFixedHeight(400)
        columns_wrapper.setLayout(columns_layout)

        # Tor connection widget
        self.tor_con = TorConnectionWidget(self.common)
        self.tor_con.success.connect(self.tor_con_success)
        self.tor_con.fail.connect(self.tor_con_fail)
        self.tor_con.hide()
        self.tor_con_type = None

        # Error label
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet(self.common.gui.css["tor_settings_error"])
        self.error_label.setWordWrap(True)

        # Buttons
        self.test_tor_button = QtWidgets.QPushButton(
            strings._("gui_settings_connection_type_test_button")
        )
        self.test_tor_button.clicked.connect(self.test_tor_clicked)
        self.save_button = QtWidgets.QPushButton(strings._("gui_settings_button_save"))
        self.save_button.clicked.connect(self.save_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.error_label, stretch=1)
        buttons_layout.addSpacing(20)
        buttons_layout.addWidget(self.test_tor_button)
        buttons_layout.addWidget(self.save_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(columns_wrapper)
        layout.addStretch()
        layout.addWidget(self.tor_con)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        self.reload_settings()

    def reload_settings(self):
        # Load settings, and fill them in
        self.old_settings = Settings(self.common)
        self.old_settings.load()

        connection_type = self.old_settings.get("connection_type")
        if connection_type == "bundled":
            if self.connection_type_bundled_radio.isEnabled():
                self.connection_type_bundled_radio.setChecked(True)
            else:
                # If bundled tor is disabled, fallback to automatic
                self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == "automatic":
            self.connection_type_automatic_radio.setChecked(True)
        elif connection_type == "control_port":
            self.connection_type_control_port_radio.setChecked(True)
        elif connection_type == "socket_file":
            self.connection_type_socket_file_radio.setChecked(True)
        self.connection_type_control_port_extras_address.setText(
            self.old_settings.get("control_port_address")
        )
        self.connection_type_control_port_extras_port.setText(
            str(self.old_settings.get("control_port_port"))
        )
        self.connection_type_socket_file_extras_path.setText(
            self.old_settings.get("socket_file_path")
        )
        self.connection_type_socks_address.setText(
            self.old_settings.get("socks_address")
        )
        self.connection_type_socks_port.setText(
            str(self.old_settings.get("socks_port"))
        )
        auth_type = self.old_settings.get("auth_type")
        if auth_type == "no_auth":
            self.authenticate_no_auth_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.authenticate_no_auth_checkbox.setChecked(QtCore.Qt.Unchecked)
        self.authenticate_password_extras_password.setText(
            self.old_settings.get("auth_password")
        )

        if self.old_settings.get("no_bridges"):
            self.bridge_use_checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.bridge_settings.hide()

        else:
            self.bridge_use_checkbox.setCheckState(QtCore.Qt.Checked)
            self.bridge_settings.show()

            builtin_obfs4 = self.old_settings.get("tor_bridges_use_obfs4")
            builtin_meek_azure = self.old_settings.get(
                "tor_bridges_use_meek_lite_azure"
            )
            builtin_snowflake = self.old_settings.get("tor_bridges_use_snowflake")

            if builtin_obfs4 or builtin_meek_azure or builtin_snowflake:
                self.bridge_builtin_radio.setChecked(True)
                self.bridge_builtin_dropdown.show()
                if builtin_obfs4:
                    self.bridge_builtin_dropdown.setCurrentText("obfs4")
                elif builtin_meek_azure:
                    self.bridge_builtin_dropdown.setCurrentText("meek-azure")
                elif builtin_snowflake:
                    self.bridge_builtin_dropdown.setCurrentText("snowflake")

                self.bridge_moat_textbox_options.hide()
                self.bridge_custom_textbox_options.hide()
            else:
                self.bridge_builtin_radio.setChecked(False)
                self.bridge_builtin_dropdown.hide()

                use_moat = self.old_settings.get("tor_bridges_use_moat")
                self.bridge_moat_radio.setChecked(use_moat)
                if use_moat:
                    self.bridge_builtin_dropdown.hide()
                    self.bridge_custom_textbox_options.hide()

                moat_bridges = self.old_settings.get("tor_bridges_use_moat_bridges")
                self.bridge_moat_textbox.document().setPlainText(moat_bridges)
                if len(moat_bridges.strip()) > 0:
                    self.bridge_moat_textbox_options.show()
                else:
                    self.bridge_moat_textbox_options.hide()

                custom_bridges = self.old_settings.get("tor_bridges_use_custom_bridges")
                if len(custom_bridges.strip()) != 0:
                    self.bridge_custom_radio.setChecked(True)
                    self.bridge_custom_textbox.setPlainText(custom_bridges)

                    self.bridge_builtin_dropdown.hide()
                    self.bridge_moat_textbox_options.hide()
                    self.bridge_custom_textbox_options.show()

    def connection_type_bundled_toggled(self, checked):
        """
        Connection type bundled was toggled
        """
        self.common.log("TorSettingsTab", "connection_type_bundled_toggled")
        if checked:
            self.tor_settings_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.show()

    def bridge_use_checkbox_state_changed(self, state):
        """
        'Use a bridge' checkbox changed
        """
        if state == QtCore.Qt.Checked:
            self.bridge_settings.show()
            self.bridge_builtin_radio.click()
            self.bridge_builtin_dropdown.setCurrentText("obfs4")
        else:
            self.bridge_settings.hide()

    def bridge_builtin_radio_toggled(self, checked):
        """
        'Select a built-in bridge' radio button toggled
        """
        if checked:
            self.bridge_builtin_dropdown.show()
            self.bridge_custom_textbox_options.hide()
            self.bridge_moat_textbox_options.hide()

    def bridge_builtin_dropdown_changed(self, selection):
        """
        Build-in bridge selection changed
        """
        if selection == "meek-azure":
            # Alert the user about meek's costliness if it looks like they're turning it on
            if not self.old_settings.get("tor_bridges_use_meek_lite_azure"):
                Alert(
                    self.common,
                    strings._("gui_settings_meek_lite_expensive_warning"),
                    QtWidgets.QMessageBox.Warning,
                )

    def bridge_moat_radio_toggled(self, checked):
        """
        Moat (request bridge) bridges option was toggled. If checked, show moat bridge options.
        """
        if checked:
            self.bridge_builtin_dropdown.hide()
            self.bridge_custom_textbox_options.hide()
            self.bridge_moat_textbox_options.show()

    def bridge_moat_button_clicked(self):
        """
        Request new bridge button clicked
        """
        self.common.log("TorSettingsTab", "bridge_moat_button_clicked")

        moat_dialog = MoatDialog(self.common)
        moat_dialog.got_bridges.connect(self.bridge_moat_got_bridges)
        moat_dialog.exec_()

    def bridge_moat_got_bridges(self, bridges):
        """
        Got new bridges from moat
        """
        self.common.log("TorSettingsTab", "bridge_moat_got_bridges")
        self.bridge_moat_textbox.document().setPlainText(bridges)
        self.bridge_moat_textbox.show()

    def bridge_custom_radio_toggled(self, checked):
        """
        Custom bridges option was toggled. If checked, show custom bridge options.
        """
        if checked:
            self.bridge_builtin_dropdown.hide()
            self.bridge_moat_textbox_options.hide()
            self.bridge_custom_textbox_options.show()

    def connection_type_automatic_toggled(self, checked):
        """
        Connection type automatic was toggled. If checked, hide authentication fields.
        """
        self.common.log("TorSettingsTab", "connection_type_automatic_toggled")
        if checked:
            self.tor_settings_group.hide()
            self.connection_type_socks.hide()
            self.connection_type_bridges_radio_group.hide()

    def connection_type_control_port_toggled(self, checked):
        """
        Connection type control port was toggled. If checked, show extra fields
        for Tor control address and port. If unchecked, hide those extra fields.
        """
        self.common.log("TorSettingsTab", "connection_type_control_port_toggled")
        if checked:
            self.tor_settings_group.show()
            self.connection_type_control_port_extras.show()
            self.connection_type_socks.show()
            self.connection_type_bridges_radio_group.hide()
        else:
            self.connection_type_control_port_extras.hide()

    def connection_type_socket_file_toggled(self, checked):
        """
        Connection type socket file was toggled. If checked, show extra fields
        for socket file. If unchecked, hide those extra fields.
        """
        self.common.log("TorSettingsTab", "connection_type_socket_file_toggled")
        if checked:
            self.tor_settings_group.show()
            self.connection_type_socket_file_extras.show()
            self.connection_type_socks.show()
            self.connection_type_bridges_radio_group.hide()
        else:
            self.connection_type_socket_file_extras.hide()

    def authenticate_no_auth_toggled(self, checked):
        """
        Authentication option no authentication was toggled.
        """
        self.common.log("TorSettingsTab", "authenticate_no_auth_toggled")
        if checked:
            self.authenticate_password_extras.hide()
        else:
            self.authenticate_password_extras.show()

    def test_tor_clicked(self):
        """
        Test Tor Settings button clicked. With the given settings, see if we can
        successfully connect and authenticate to Tor.
        """
        self.common.log("TorSettingsTab", "test_tor_clicked")

        self.error_label.setText("")

        settings = self.settings_from_fields()
        if not settings:
            return

        self.test_tor_button.hide()
        self.save_button.hide()

        self.test_onion = Onion(
            self.common,
            use_tmp_dir=True,
            get_tor_paths=self.common.gui.get_tor_paths,
        )

        self.tor_con_type = "test"
        self.tor_con.show()
        self.tor_con.start(settings, True, self.test_onion)

    def save_clicked(self):
        """
        Save button clicked. Save current settings to disk.
        """
        self.common.log("TorSettingsTab", "save_clicked")

        self.error_label.setText("")

        def changed(s1, s2, keys):
            """
            Compare the Settings objects s1 and s2 and return true if any values
            have changed for the given keys.
            """
            for key in keys:
                if s1.get(key) != s2.get(key):
                    return True
            return False

        settings = self.settings_from_fields()
        if settings:
            # Save the new settings
            settings.save()

            # If Tor isn't connected, or if Tor settings have changed, Reinitialize
            # the Onion object
            reboot_onion = False
            if not self.common.gui.local_only:
                if self.common.gui.onion.is_authenticated():
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "Connected to Tor"
                    )

                    if changed(
                        settings,
                        self.old_settings,
                        [
                            "connection_type",
                            "control_port_address",
                            "control_port_port",
                            "socks_address",
                            "socks_port",
                            "socket_file_path",
                            "auth_type",
                            "auth_password",
                            "no_bridges",
                            "tor_bridges_use_obfs4",
                            "tor_bridges_use_meek_lite_azure",
                            "tor_bridges_use_custom_bridges",
                        ],
                    ):

                        reboot_onion = True

                else:
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "Not connected to Tor"
                    )
                    # Tor isn't connected, so try connecting
                    reboot_onion = True

                # Do we need to reinitialize Tor?
                if reboot_onion:
                    # Reinitialize the Onion object
                    self.common.log(
                        "TorSettingsTab", "save_clicked", "rebooting the Onion"
                    )
                    self.common.gui.onion.cleanup()

                    self.test_tor_button.hide()
                    self.save_button.hide()

                    self.tor_con_type = "save"
                    self.tor_con.show()
                    self.tor_con.start(settings)
                else:
                    self.close_this_tab.emit()
            else:
                self.close_this_tab.emit()

    def tor_con_success(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.test_tor_button.show()
        self.save_button.show()

        if self.tor_con_type == "test":
            Alert(
                self.common,
                strings._("settings_test_success").format(
                    self.test_onion.tor_version,
                    self.test_onion.supports_ephemeral,
                    self.test_onion.supports_stealth,
                    self.test_onion.supports_v3_onions,
                ),
                title=strings._("gui_settings_connection_type_test_button"),
            )
            self.test_onion.cleanup()

        elif self.tor_con_type == "save":
            if (
                self.common.gui.onion.is_authenticated()
                and not self.tor_con.wasCanceled()
            ):
                self.close_this_tab.emit()

        self.tor_con_type = None

    def tor_con_fail(self, msg):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.test_tor_button.show()
        self.save_button.show()

        self.error_label.setText(msg)

        if self.tor_con_type == "test":
            self.test_onion.cleanup()

        self.tor_con_type = None

    def settings_from_fields(self):
        """
        Return a Settings object that's full of values from the settings dialog.
        """
        self.common.log("TorSettingsTab", "settings_from_fields")
        settings = Settings(self.common)
        settings.load()  # To get the last update timestamp

        # Tor connection
        if self.connection_type_bundled_radio.isChecked():
            settings.set("connection_type", "bundled")
        if self.connection_type_automatic_radio.isChecked():
            settings.set("connection_type", "automatic")
        if self.connection_type_control_port_radio.isChecked():
            settings.set("connection_type", "control_port")
        if self.connection_type_socket_file_radio.isChecked():
            settings.set("connection_type", "socket_file")

        settings.set(
            "control_port_address",
            self.connection_type_control_port_extras_address.text(),
        )
        settings.set(
            "control_port_port", self.connection_type_control_port_extras_port.text()
        )
        settings.set(
            "socket_file_path", self.connection_type_socket_file_extras_path.text()
        )

        settings.set("socks_address", self.connection_type_socks_address.text())
        settings.set("socks_port", self.connection_type_socks_port.text())

        if self.authenticate_no_auth_checkbox.checkState() == QtCore.Qt.Checked:
            settings.set("auth_type", "no_auth")
        else:
            settings.set("auth_type", "password")

        settings.set("auth_password", self.authenticate_password_extras_password.text())

        # Whether we use bridges
        if self.bridge_use_checkbox.checkState() == QtCore.Qt.Checked:
            settings.set("no_bridges", False)

            if self.bridge_builtin_radio.isChecked():
                selection = self.bridge_builtin_dropdown.currentText()
                if selection == "obfs4":
                    settings.set("tor_bridges_use_obfs4", True)
                    settings.set("tor_bridges_use_meek_lite_azure", False)
                    settings.set("tor_bridges_use_snowflake", False)
                elif selection == "meek-azure":
                    settings.set("tor_bridges_use_obfs4", False)
                    settings.set("tor_bridges_use_meek_lite_azure", True)
                    settings.set("tor_bridges_use_snowflake", False)
                elif selection == "snowflake":
                    settings.set("tor_bridges_use_obfs4", False)
                    settings.set("tor_bridges_use_meek_lite_azure", False)
                    settings.set("tor_bridges_use_snowflake", True)

                settings.set("tor_bridges_use_moat", False)
                settings.set("tor_bridges_use_custom_bridges", "")

            if self.bridge_moat_radio.isChecked():
                settings.set("tor_bridges_use_obfs4", False)
                settings.set("tor_bridges_use_meek_lite_azure", False)
                settings.set("tor_bridges_use_snowflake", False)

                settings.set("tor_bridges_use_moat", True)

                moat_bridges = self.bridge_moat_textbox.toPlainText()
                if moat_bridges.strip() == "":
                    self.error_label.setText(
                        strings._("gui_settings_moat_bridges_invalid")
                    )
                    return False

                settings.set(
                    "tor_bridges_use_moat_bridges",
                    moat_bridges,
                )

                settings.set("tor_bridges_use_custom_bridges", "")

            if self.bridge_custom_radio.isChecked():
                settings.set("tor_bridges_use_obfs4", False)
                settings.set("tor_bridges_use_meek_lite_azure", False)
                settings.set("tor_bridges_use_snowflake", False)
                settings.set("tor_bridges_use_moat", False)

                new_bridges = []
                bridges = self.bridge_custom_textbox.toPlainText().split("\n")
                bridges_valid = False
                for bridge in bridges:
                    if bridge != "":
                        # Check the syntax of the custom bridge to make sure it looks legitimate
                        ipv4_pattern = re.compile(
                            "(obfs4\s+)?(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]):([0-9]+)(\s+)([A-Z0-9]+)(.+)$"
                        )
                        ipv6_pattern = re.compile(
                            "(obfs4\s+)?\[(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\]:[0-9]+\s+[A-Z0-9]+(.+)$"
                        )
                        meek_lite_pattern = re.compile(
                            "(meek_lite)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)(\s)+url=(.+)(\s)+front=(.+)"
                        )
                        snowflake_pattern = re.compile(
                            "(snowflake)(\s)+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+)(\s)+([0-9A-Z]+)"
                        )
                        if (
                            ipv4_pattern.match(bridge)
                            or ipv6_pattern.match(bridge)
                            or meek_lite_pattern.match(bridge)
                            or snowflake_pattern.match(bridge)
                        ):
                            new_bridges.append(bridge)
                            bridges_valid = True

                if bridges_valid:
                    new_bridges = "\n".join(new_bridges) + "\n"
                    settings.set("tor_bridges_use_custom_bridges", new_bridges)
                else:
                    self.error_label.setText(
                        strings._("gui_settings_tor_bridges_invalid")
                    )
                    return False
        else:
            settings.set("no_bridges", True)

        return settings

    def closeEvent(self, e):
        self.common.log("TorSettingsTab", "closeEvent")

        # On close, if Tor isn't connected, then quit OnionShare altogether
        if not self.common.gui.local_only:
            if not self.common.gui.onion.is_authenticated():
                self.common.log(
                    "TorSettingsTab",
                    "closeEvent",
                    "Closing while not connected to Tor",
                )

                # Wait 1ms for the event loop to finish, then quit
                QtCore.QTimer.singleShot(1, self.common.gui.qtapp.quit)