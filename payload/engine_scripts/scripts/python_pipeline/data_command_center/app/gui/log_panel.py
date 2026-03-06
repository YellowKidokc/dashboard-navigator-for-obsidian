"""
Log Panel - Logs and run metadata display

Shows:
- Live log messages
- Run results and metadata
- History of recent runs
"""

import logging
from datetime import datetime
from typing import Any

import customtkinter as ctk

logger = logging.getLogger(__name__)


class LogPanel(ctk.CTkFrame):
    """Panel for displaying logs and run metadata."""

    # Color mapping for log levels
    LEVEL_COLORS = {
        "DEBUG": "gray",
        "INFO": "white",
        "WARNING": "yellow",
        "ERROR": "red",
        "SUCCESS": "green",
    }

    def __init__(self, parent):
        super().__init__(parent)

        self._log_entries: list[tuple[str, str, str]] = []
        self._max_entries = 1000

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the panel widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Section: Run Result
        self.result_label = ctk.CTkLabel(
            self,
            text="Last Run Result",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.result_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.result_frame = ctk.CTkFrame(self, height=150)
        self.result_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)

        self.result_text = ctk.CTkTextbox(
            self.result_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.result_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.result_text.insert("1.0", "No runs yet")
        self.result_text.configure(state="disabled")

        # Section: Log Messages
        self.log_header = ctk.CTkFrame(self, fg_color="transparent")
        self.log_header.grid(row=2, column=0, padx=10, pady=(15, 5), sticky="ew")
        self.log_header.grid_columnconfigure(0, weight=1)

        self.log_label = ctk.CTkLabel(
            self.log_header,
            text="Log Messages",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.log_label.grid(row=0, column=0, sticky="w")

        self.clear_btn = ctk.CTkButton(
            self.log_header,
            text="Clear",
            width=60,
            height=24,
            command=self._clear_logs,
        )
        self.clear_btn.grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.log_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        # Configure tags for colored output
        # Note: CustomTkinter textbox has limited tag support
        # We'll use prefixes to indicate level

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Add a log message.

        Args:
            message: The log message.
            level: Log level (DEBUG, INFO, WARNING, ERROR, SUCCESS).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"

        self._log_entries.append((timestamp, level, message))

        # Trim if too many entries
        if len(self._log_entries) > self._max_entries:
            self._log_entries = self._log_entries[-self._max_entries:]
            self._refresh_log_display()
        else:
            # Append to display
            self.log_text.configure(state="normal")
            self.log_text.insert("end", entry + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _refresh_log_display(self) -> None:
        """Refresh the entire log display."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")

        for timestamp, level, message in self._log_entries:
            entry = f"[{timestamp}] [{level}] {message}\n"
            self.log_text.insert("end", entry)

        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_logs(self) -> None:
        """Clear all log messages."""
        self._log_entries.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def show_run_result(self, result: dict[str, Any]) -> None:
        """
        Display a run result.

        Args:
            result: Run result dictionary with keys like:
                - run_id
                - status
                - started_at
                - completed_at
                - duration_seconds
                - rows_inserted
                - error
        """
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")

        # Format the result
        lines = []

        status = result.get("status", "unknown")
        status_icon = "✓" if status == "success" else "✗"
        lines.append(f"Status: {status_icon} {status.upper()}")

        if result.get("run_id"):
            lines.append(f"Run ID: {result['run_id']}")

        if result.get("script_name"):
            version = result.get("script_version", "?")
            lines.append(f"Script: {result['script_name']} v{version}")

        if result.get("target_db"):
            lines.append(f"Database: {result['target_db']}")

        if result.get("started_at"):
            lines.append(f"Started: {result['started_at']}")

        if result.get("duration_seconds") is not None:
            lines.append(f"Duration: {result['duration_seconds']:.1f}s")

        lines.append("")  # Blank line

        # Result details
        run_result = result.get("result", {})
        if run_result:
            lines.append("Results:")
            if run_result.get("rows_downloaded"):
                lines.append(f"  Rows downloaded: {run_result['rows_downloaded']}")
            if run_result.get("rows_inserted"):
                lines.append(f"  Rows inserted: {run_result['rows_inserted']}")
            if run_result.get("rows_updated"):
                lines.append(f"  Rows updated: {run_result['rows_updated']}")
            if run_result.get("warnings"):
                lines.append(f"  Warnings: {len(run_result['warnings'])}")
                for warning in run_result["warnings"][:5]:
                    lines.append(f"    - {warning}")

        # Error if present
        if result.get("error"):
            lines.append("")
            lines.append(f"Error: {result['error']}")

        self.result_text.insert("1.0", "\n".join(lines))
        self.result_text.configure(state="disabled")

        # Also log the result
        if status == "success":
            self.log(f"Run completed: {result.get('run_id', 'unknown')}", "SUCCESS")
        else:
            self.log(f"Run failed: {result.get('error', 'unknown error')}", "ERROR")


class RunHistoryPanel(ctk.CTkFrame):
    """Panel showing history of recent runs."""

    def __init__(self, parent):
        super().__init__(parent)

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the panel widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Run History",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # History list
        self.history_frame = ctk.CTkScrollableFrame(self)
        self.history_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.history_frame.grid_columnconfigure(0, weight=1)

    def set_history(self, runs: list[dict]) -> None:
        """
        Update the run history display.

        Args:
            runs: List of run result dictionaries.
        """
        # Clear existing
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        if not runs:
            label = ctk.CTkLabel(
                self.history_frame,
                text="No runs yet",
                text_color="gray",
            )
            label.grid(row=0, column=0, pady=10)
            return

        for i, run in enumerate(reversed(runs[-20:])):  # Last 20 runs
            self._add_history_entry(i, run)

    def _add_history_entry(self, row: int, run: dict) -> None:
        """Add a single history entry."""
        frame = ctk.CTkFrame(self.history_frame)
        frame.grid(row=row, column=0, pady=2, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        # Status icon
        status = run.get("status", "unknown")
        icon = "✓" if status == "success" else "✗"
        color = "green" if status == "success" else "red"

        status_label = ctk.CTkLabel(
            frame,
            text=icon,
            text_color=color,
            width=20,
        )
        status_label.grid(row=0, column=0, padx=5, pady=5)

        # Script name and time
        script_name = run.get("script_name", "Unknown")
        started = run.get("started_at", "")
        if isinstance(started, str) and "T" in started:
            started = started.split("T")[1][:8]  # Just time part

        info_label = ctk.CTkLabel(
            frame,
            text=f"{script_name} @ {started}",
            anchor="w",
        )
        info_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Duration
        duration = run.get("duration_seconds")
        if duration is not None:
            dur_label = ctk.CTkLabel(
                frame,
                text=f"{duration:.1f}s",
                text_color="gray",
            )
            dur_label.grid(row=0, column=2, padx=5, pady=5)
