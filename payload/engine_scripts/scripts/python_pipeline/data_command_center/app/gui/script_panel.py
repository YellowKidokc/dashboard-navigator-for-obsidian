"""
Script Panel - Script selection and parameter rendering

Renders parameters automatically from SCRIPT_SPEC.
Handles script selection, parameter editing, and run/schedule actions.
"""

import logging
from typing import Any, Callable

import customtkinter as ctk

logger = logging.getLogger(__name__)


class ScriptPanel(ctk.CTkFrame):
    """Panel for script selection and parameter configuration."""

    def __init__(
        self,
        parent,
        on_run: Callable[[str, dict, str], None] | None = None,
        on_schedule: Callable[[str, dict, str, int], None] | None = None,
    ):
        super().__init__(parent)

        self._scripts: dict[str, dict] = {}
        self._current_script: str | None = None
        self._param_widgets: dict[str, Any] = {}
        self._on_run = on_run
        self._on_schedule = on_schedule
        self._connections: list[str] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the panel widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Section: Script Selection
        self.script_label = ctk.CTkLabel(
            self,
            text="Available Scripts",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.script_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.script_listbox = ctk.CTkScrollableFrame(self, height=150)
        self.script_listbox.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.script_listbox.grid_columnconfigure(0, weight=1)

        # Section: Parameters
        self.params_label = ctk.CTkLabel(
            self,
            text="Parameters",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.params_label.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="nw")

        self.params_frame = ctk.CTkScrollableFrame(self)
        self.params_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        self.params_frame.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Section: Target Database
        self.db_label = ctk.CTkLabel(
            self,
            text="Target Database",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.db_label.grid(row=4, column=0, padx=10, pady=(15, 5), sticky="w")

        self.db_var = ctk.StringVar()
        self.db_dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.db_var,
            values=["No connections"],
            width=200,
        )
        self.db_dropdown.grid(row=5, column=0, padx=10, pady=5, sticky="w")

        # Section: Actions
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.grid(row=6, column=0, padx=10, pady=15, sticky="ew")
        self.actions_frame.grid_columnconfigure((0, 1), weight=1)

        self.run_btn = ctk.CTkButton(
            self.actions_frame,
            text="▶ Run Now",
            command=self._handle_run,
            state="disabled",
        )
        self.run_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.schedule_btn = ctk.CTkButton(
            self.actions_frame,
            text="⏱ Schedule",
            command=self._handle_schedule,
            state="disabled",
        )
        self.schedule_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def set_scripts(self, scripts: list[dict]) -> None:
        """
        Update the list of available scripts.

        Args:
            scripts: List of script info dicts with 'name', 'version', 'spec' keys.
        """
        # Clear existing script buttons
        for widget in self.script_listbox.winfo_children():
            widget.destroy()

        self._scripts.clear()

        for script in scripts:
            name = script["name"]
            version = script.get("version", "?")
            self._scripts[name] = script

            btn = ctk.CTkButton(
                self.script_listbox,
                text=f"{name} (v{version})",
                anchor="w",
                command=lambda n=name: self._select_script(n),
            )
            btn.grid(sticky="ew", pady=2)

        if scripts:
            self._select_script(scripts[0]["name"])

    def set_connections(self, connections: list[str]) -> None:
        """Update available database connections."""
        self._connections = connections
        if connections:
            self.db_dropdown.configure(values=connections)
            self.db_var.set(connections[0])
        else:
            self.db_dropdown.configure(values=["No connections"])
            self.db_var.set("No connections")

    def _select_script(self, name: str) -> None:
        """Select a script and render its parameters."""
        if name not in self._scripts:
            return

        self._current_script = name
        script = self._scripts[name]

        # Update target DB options if specified
        spec = script.get("spec", {})
        target_db = spec.get("target_db", {})
        db_options = target_db.get("options", [])
        db_default = target_db.get("default")

        if db_options:
            self.db_dropdown.configure(values=db_options)
            if db_default:
                self.db_var.set(db_default)
            else:
                self.db_var.set(db_options[0])

        # Render parameters
        self._render_parameters(spec.get("parameters", {}))

        # Enable action buttons
        self.run_btn.configure(state="normal")
        self.schedule_btn.configure(state="normal")

    def _render_parameters(self, parameters: dict[str, dict]) -> None:
        """Render parameter input widgets from SCRIPT_SPEC."""
        # Clear existing parameter widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        self._param_widgets.clear()

        if not parameters:
            label = ctk.CTkLabel(
                self.params_frame,
                text="No configurable parameters",
                text_color="gray",
            )
            label.grid(row=0, column=0, pady=10)
            return

        row = 0
        for param_name, param_def in parameters.items():
            param_type = param_def.get("type", "str")
            default = param_def.get("default", "")
            description = param_def.get("description", "")

            # Label
            label = ctk.CTkLabel(
                self.params_frame,
                text=param_name,
                font=ctk.CTkFont(weight="bold"),
            )
            label.grid(row=row, column=0, padx=5, pady=5, sticky="w")

            # Widget based on type
            widget = self._create_param_widget(param_def, param_type, default)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            self._param_widgets[param_name] = (widget, param_type)

            # Description tooltip
            if description:
                desc_label = ctk.CTkLabel(
                    self.params_frame,
                    text=description,
                    font=ctk.CTkFont(size=10),
                    text_color="gray",
                )
                desc_label.grid(row=row + 1, column=0, columnspan=2, padx=5, sticky="w")
                row += 1

            row += 1

    def _create_param_widget(
        self,
        param_def: dict,
        param_type: str,
        default: Any,
    ) -> ctk.CTkBaseClass:
        """Create appropriate widget for parameter type."""
        if param_type == "select":
            options = param_def.get("options", [])
            var = ctk.StringVar(value=str(default))
            widget = ctk.CTkOptionMenu(
                self.params_frame,
                variable=var,
                values=[str(o) for o in options],
            )
            widget._var = var
            return widget

        elif param_type == "int":
            var = ctk.StringVar(value=str(default))
            widget = ctk.CTkEntry(self.params_frame, textvariable=var)
            widget._var = var

            # Add validation hints
            min_val = param_def.get("min")
            max_val = param_def.get("max")
            if min_val is not None or max_val is not None:
                widget._min = min_val
                widget._max = max_val

            return widget

        elif param_type == "bool":
            var = ctk.BooleanVar(value=bool(default))
            widget = ctk.CTkCheckBox(
                self.params_frame,
                text="",
                variable=var,
            )
            widget._var = var
            return widget

        else:  # str or default
            var = ctk.StringVar(value=str(default) if default else "")
            widget = ctk.CTkEntry(self.params_frame, textvariable=var)
            widget._var = var
            return widget

    def _get_config(self) -> dict[str, Any]:
        """Get current parameter configuration."""
        config = {}

        for param_name, (widget, param_type) in self._param_widgets.items():
            var = widget._var
            value = var.get()

            # Convert to appropriate type
            if param_type == "int":
                try:
                    value = int(value)
                    # Apply min/max constraints
                    if hasattr(widget, "_min") and widget._min is not None:
                        value = max(value, widget._min)
                    if hasattr(widget, "_max") and widget._max is not None:
                        value = min(value, widget._max)
                except ValueError:
                    value = 0

            elif param_type == "bool":
                value = bool(value)

            config[param_name] = value

        return config

    def _handle_run(self) -> None:
        """Handle run button click."""
        if not self._current_script or not self._on_run:
            return

        config = self._get_config()
        target_db = self.db_var.get()

        self._on_run(self._current_script, config, target_db)

    def _handle_schedule(self) -> None:
        """Handle schedule button click."""
        if not self._current_script or not self._on_schedule:
            return

        config = self._get_config()
        target_db = self.db_var.get()

        # Show schedule dialog
        from .app_window import ScheduleDialog

        def on_confirm(interval: int):
            self._on_schedule(self._current_script, config, target_db, interval)

        dialog = ScheduleDialog(self, self._current_script, on_confirm)
