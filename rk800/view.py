from typing import Optional
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style


class ViewManager:
    """Centralized view manager for all terminal output with color coding"""

    def __init__(self):
        self.debug_enabled = False

        # Color theme
        self.colors = {
            "success": "#98fb98",
            "warning": "#f0e68c",
            "error": "#ba55d3",
            "info": "#87cefa",
            "debug": "#888888",
            "text": "#e7e7e7",
            "prompt": "#ffc0cb",
        }

        # Message prefixes
        self.prefixes = {
            "success": "[+]",
            "warning": "[!]",
            "error": "[-]",
            "info": "[*]",
            "debug": "[?]",
        }

        self.style = Style.from_dict(
            {
                "success": self.colors["success"],
                "warning": self.colors["warning"],
                "error": self.colors["error"],
                "info": self.colors["info"],
                "debug": self.colors["debug"],
                "text": self.colors["text"],
                "prompt": self.colors["prompt"],
            }
        )

    def _print_with_prefix(
        self,
        message: str,
        prefix: str,
        prefix_style: str,
        text_color: Optional[str] = None,
    ) -> None:
        """Prints message with a styled prefix.

        Args:
            message (str): The message to display.
            prefix (str): The prefix to display (e.g., "[+]", "[-]").
            prefix_style (str): The style class for the prefix.
            text_color (Optional[str]): Optional custom text color override.
        """
        for line in message.split("\n"):
            text_style = f"#{text_color}" if text_color else "class:text"
            formatted_text = FormattedText(
                [
                    (prefix_style, prefix),
                    (text_style, f" {line}"),
                ]
            )
            print_formatted_text(formatted_text, style=self.style)

    def success(self, message: str, text_color: Optional[str] = None) -> None:
        """Prints success message with [+] prefix."""
        self._print_with_prefix(
            message, self.prefixes["success"], "class:success", text_color
        )

    def warning(self, message: str, text_color: Optional[str] = None) -> None:
        """Prints warning message with [!] prefix."""
        self._print_with_prefix(
            message, self.prefixes["warning"], "class:warning", text_color
        )

    def error(self, message: str, text_color: Optional[str] = None) -> None:
        """Prints error message with [-] prefix."""
        self._print_with_prefix(
            message, self.prefixes["error"], "class:error", text_color
        )

    def info(self, message: str, text_color: Optional[str] = None) -> None:
        """Prints info message with [*] prefix."""
        self._print_with_prefix(
            message, self.prefixes["info"], "class:info", text_color
        )

    def debug(self, message: str, text_color: Optional[str] = None) -> None:
        """Prints debug message if debug is enabled."""
        if self.debug_enabled:
            self._print_with_prefix(
                message, self.prefixes["debug"], "class:debug", text_color
            )

    def enable_debug(self) -> None:
        """Enable debug messages."""
        self.debug_enabled = True

    def disable_debug(self) -> None:
        """Disable debug messages."""
        self.debug_enabled = False

    def clear_screen(self) -> None:
        """Clear the terminal screen and scrollback buffer."""
        print("\033[3J\033[2J\033[H", end="")

    def get_prompt_style(self) -> list:
        """Get the prompt style for input."""
        return [("class:prompt", "rk800> ")]
