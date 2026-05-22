"""FilesScreen — two-pane file explorer for ARGUS."""

from __future__ import annotations

import shutil
from pathlib import Path

import psutil
from rich.markdown import Markdown
from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DirectoryTree, Input, Label, Static


# ── Helper: file metadata line ────────────────────────────────────────────────

def _file_meta(path: Path) -> str:
    """Return a one-line Rich markup summary of file metadata."""
    try:
        st = path.stat()
        size = st.st_size
        # Human-readable size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024.0:
                size_str = f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
                break
            size /= 1024.0
        else:
            size_str = f"{size:.1f} TB"

        import time
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
        mode = oct(st.st_mode)[-3:]
        return (
            f"[dim]Size:[/] [cyan]{size_str}[/]  "
            f"[dim]Modified:[/] [cyan]{mtime}[/]  "
            f"[dim]Perms:[/] [cyan]{mode}[/]"
        )
    except Exception:
        return "[dim]No metadata available[/]"


# ── Confirm Delete dialog ─────────────────────────────────────────────────────

class ConfirmDelete(ModalScreen[bool]):
    """Modal confirmation dialog for deleting a file or directory."""

    DEFAULT_CSS = """
    ConfirmDelete {
        align: center middle;
        background: $background 80%;
    }
    #delete-box {
        background: $panel;
        border: round $error;
        padding: 2 3;
        width: 58;
        height: 9;
        align: center middle;
    }
    #delete-label {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #delete-dim {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 1;
    }
    #delete-buttons {
        layout: horizontal;
        align: center middle;
        width: 100%;
        height: auto;
    }
    #delete-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    def compose(self) -> ComposeResult:
        with Vertical(id="delete-box"):
            yield Label(
                f"[bold red]Delete {'directory' if self._path.is_dir() else 'file'}?[/]",
                id="delete-label",
            )
            yield Label(
                f"[dim]{str(self._path)[-50:]}[/]",
                id="delete-dim",
            )
            with Horizontal(id="delete-buttons"):
                yield Button("Delete", variant="error", id="btn-delete")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-delete")


# ── New Directory dialog ──────────────────────────────────────────────────────

class NewDirDialog(ModalScreen[str | None]):
    """Modal dialog for creating a new directory."""

    DEFAULT_CSS = """
    NewDirDialog {
        align: center middle;
        background: $background 80%;
    }
    #newdir-box {
        background: $panel;
        border: round $primary;
        padding: 2 3;
        width: 52;
        height: 8;
        align: center middle;
    }
    #newdir-label {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #newdir-input {
        width: 30;
        margin-bottom: 1;
    }
    #newdir-buttons {
        layout: horizontal;
        align: center middle;
        width: 100%;
        height: auto;
    }
    #newdir-buttons Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="newdir-box"):
            yield Label("[bold]New Directory[/]", id="newdir-label")
            yield Input(placeholder="Directory name", id="newdir-input")
            with Horizontal(id="newdir-buttons"):
                yield Button("Create", variant="primary", id="btn-create")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#newdir-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            name = self.query_one("#newdir-input", Input).value.strip()
            self.dismiss(name if name else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self.query_one("#btn-create", Button).press()


# ── Rename dialog ─────────────────────────────────────────────────────────────

class RenameDialog(ModalScreen[str | None]):
    """Modal dialog for renaming a file or directory."""

    DEFAULT_CSS = """
    RenameDialog {
        align: center middle;
        background: $background 80%;
    }
    #rename-box {
        background: $panel;
        border: round $primary;
        padding: 2 3;
        width: 56;
        height: 9;
        align: center middle;
    }
    #rename-label {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #rename-input {
        width: 34;
        margin-bottom: 1;
    }
    #rename-buttons {
        layout: horizontal;
        align: center middle;
        width: 100%;
        height: auto;
    }
    #rename-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    def compose(self) -> ComposeResult:
        with Vertical(id="rename-box"):
            yield Label(
                f"[bold]Rename:[/] [dim]{self._path.name[:40]}[/]",
                id="rename-label",
            )
            yield Input(
                value=self._path.name,
                id="rename-input",
            )
            with Horizontal(id="rename-buttons"):
                yield Button("Rename", variant="primary", id="btn-rename")
                yield Button("Cancel", variant="default", id="btn-cancel")

    def on_mount(self) -> None:
        inp = self.query_one("#rename-input", Input)
        inp.focus()
        # Select the stem (everything before the last dot) for easy editing
        inp.cursor_position = len(self._path.stem)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-rename":
            name = self.query_one("#rename-input", Input).value.strip()
            self.dismiss(name if name else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, _: Input.Submitted) -> None:
        self.query_one("#btn-rename", Button).press()


# ── Main File Explorer Screen ─────────────────────────────────────────────────

class FilesScreen(Screen):
    """Two-pane file explorer with directory tree and preview pane."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("slash", "search_focus", "Search"),
        Binding("d", "delete_path", "Delete"),
        Binding("n", "new_dir", "New Dir"),
        Binding("r", "rename_path", "Rename"),
        Binding("backspace", "go_parent", "Up"),
    ]

    DEFAULT_CSS = """
    FilesScreen {
        layout: vertical;
        background: $background;
    }
    #files-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
        border-bottom: solid $border;
    }
    #files-header-title {
        width: 1fr;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #files-back-btn {
        width: auto;
        min-width: 12;
        height: 3;
    }
    #files-search-row {
        height: 3;
        background: $surface;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
        display: none;
    }
    #files-search-label {
        width: auto;
        content-align: left middle;
        color: $text-muted;
        margin-right: 1;
    }
    #files-search-input {
        width: 40;
    }
    #files-body {
        layout: horizontal;
        height: 1fr;
    }
    #files-tree {
        width: 35%;
        border-right: solid $border;
        background: $panel;
    }
    #files-preview {
        width: 65%;
        padding: 1 2;
        overflow-y: auto;
        background: $background;
    }
    #files-meta {
        height: 1;
        background: $surface;
        color: $text-muted;
        content-align: left middle;
        padding: 0 2;
    }
    #files-footer {
        height: 1;
        background: $surface;
        color: $foreground;
        content-align: center middle;
    }
    """

    # Track the currently selected path for file operations
    _selected_path: reactive[Path | None] = reactive(None)
    _cwd: reactive[Path] = reactive(Path.home())

    def compose(self) -> ComposeResult:
        home = Path.home()
        with Horizontal(id="files-header"):
            yield Label(f"📁 File Explorer — {home}", id="files-header-title")
            yield Button("← Back", id="files-back-btn", variant="default")
        with Horizontal(id="files-search-row"):
            yield Label("/  Search:", id="files-search-label")
            yield Input(placeholder="Type to filter...", id="files-search-input")
        with Horizontal(id="files-body"):
            yield DirectoryTree(str(home), id="files-tree")
            yield Static(
                "[dim]Select a file in the tree to preview it.[/]",
                id="files-preview",
            )
        yield Label("", id="files-meta")
        yield Label(
            "Enter Open  d Delete  n New Dir  r Rename  / Search  Backspace Up  Esc/q Back",
            id="files-footer",
        )

    # ── Directory tree events ─────────────────────────────────────────────────

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Preview a file when selected in the tree."""
        path = event.path  # already a Path in Textual 8
        self._selected_path = path
        self._update_header(path.parent)
        self._update_meta(path)
        self._preview_file(path)

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Track current directory when a directory node is expanded/selected."""
        path = event.path
        self._selected_path = path
        self._cwd = path
        self._update_header(path)
        self._update_meta(path)
        preview = self.query_one("#files-preview", Static)
        try:
            children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            lines = [f"[bold] {path}[/]\n"]
            dirs = [p for p in children if p.is_dir()]
            files = [p for p in children if p.is_file()]
            if dirs:
                lines.append(f"[cyan]Directories ({len(dirs)}):[/]")
                for d in dirs[:30]:
                    lines.append(f"  [cyan]{d.name}/[/]")
                if len(dirs) > 30:
                    lines.append(f"  [dim]… {len(dirs) - 30} more[/]")
                lines.append("")
            if files:
                lines.append(f"[green]Files ({len(files)}):[/]")
                for f in files[:50]:
                    try:
                        sz = f.stat().st_size
                        sz_str = f"{sz:,} B" if sz < 1024 else f"{sz // 1024} KB"
                    except Exception:
                        sz_str = "?"
                    lines.append(f"  {f.name:<40} [dim]{sz_str}[/]")
                if len(files) > 50:
                    lines.append(f"  [dim]… {len(files) - 50} more[/]")
            preview.update("\n".join(lines))
        except PermissionError:
            preview.update("[red]Permission denied[/]")
        except Exception as exc:
            preview.update(f"[red]Error reading directory: {exc}[/]")

    # ── Preview helpers ───────────────────────────────────────────────────────

    def _update_header(self, path: Path) -> None:
        try:
            self.query_one("#files-header-title", Label).update(
                f"📁 File Explorer — {path}"
            )
        except Exception:
            pass

    def _update_meta(self, path: Path) -> None:
        try:
            self.query_one("#files-meta", Label).update(_file_meta(path))
        except Exception:
            pass

    def _preview_file(self, path: Path) -> None:
        """Render file contents in the preview pane with syntax highlighting."""
        preview = self.query_one("#files-preview", Static)
        try:
            st = path.stat()
            size = st.st_size
            if size > 512_000:
                preview.update(
                    f"[yellow]File too large to preview ({size:,} bytes)[/]\n\n"
                    + _file_meta(path)
                )
                return

            suffix = path.suffix.lower()

            # Markdown rendering
            if suffix == ".md":
                try:
                    text = path.read_text(errors="replace")
                    preview.update(Markdown(text))
                    return
                except Exception:
                    pass

            # Syntax-highlighted code
            _CODE_EXTS = {
                ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
                ".toml", ".sh", ".bash", ".zsh", ".fish", ".css", ".scss",
                ".html", ".xml", ".rs", ".go", ".c", ".cpp", ".h", ".hpp",
                ".java", ".rb", ".php", ".swift", ".kt", ".scala", ".r",
                ".sql", ".lua", ".vim", ".conf", ".ini", ".env", ".tf",
                ".dockerfile", ".makefile",
            }
            if suffix in _CODE_EXTS or path.name.lower() in {
                "dockerfile", "makefile", "gemfile", "rakefile", "procfile",
            }:
                lang = suffix.lstrip(".")
                lang_map = {
                    "yml": "yaml", "sh": "bash", "zsh": "bash", "fish": "bash",
                    "jsx": "javascript", "tsx": "typescript", "tf": "hcl",
                    "conf": "ini", "dockerfile": "docker", "makefile": "makefile",
                }
                lang = lang_map.get(lang, lang) or "text"
                try:
                    text = path.read_text(errors="replace")
                    preview.update(
                        Syntax(text, lang, theme="monokai", line_numbers=True)
                    )
                    return
                except Exception:
                    pass

            # Binary / image detection
            _BIN_EXTS = {
                ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
                ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
                ".exe", ".so", ".dylib", ".bin", ".pyc", ".pyo",
            }
            if suffix in _BIN_EXTS:
                preview.update(
                    f"[dim]Binary file — no preview available[/]\n\n"
                    + _file_meta(path)
                )
                return

            # Plain text fallback
            try:
                text = path.read_text(errors="replace")
                # Truncate very long plain-text files
                if len(text) > 10_000:
                    text = text[:10_000] + "\n\n[dim]… truncated[/]"
                preview.update(text)
            except Exception as exc:
                preview.update(f"[red]Cannot read file: {exc}[/]")

        except FileNotFoundError:
            preview.update("[red]File not found[/]")
        except PermissionError:
            preview.update("[red]Permission denied[/]")
        except Exception as exc:
            preview.update(f"[red]Cannot preview: {exc}[/]")

    # ── Actions ───────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "files-back-btn":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_go_parent(self) -> None:
        """Navigate the tree root up one directory level."""
        tree = self.query_one("#files-tree", DirectoryTree)
        current = Path(tree.path)
        parent = current.parent
        if parent != current:
            tree.path = str(parent)
            self._cwd = parent
            self._update_header(parent)

    def action_search_focus(self) -> None:
        """Show the search bar and focus it."""
        row = self.query_one("#files-search-row")
        row.display = True
        self.query_one("#files-search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Hide search bar on Enter."""
        if event.input.id == "files-search-input":
            row = self.query_one("#files-search-row")
            row.display = False
            self.query_one("#files-tree", DirectoryTree).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live filter: walk tree to matching nodes (basic name filter)."""
        if event.input.id != "files-search-input":
            return
        query = event.value.strip().lower()
        preview = self.query_one("#files-preview", Static)
        if not query:
            preview.update("[dim]Select a file in the tree to preview it.[/]")
            return
        # Search from cwd
        try:
            matches: list[Path] = []
            for p in self._cwd.rglob("*"):
                if query in p.name.lower():
                    matches.append(p)
                if len(matches) >= 100:
                    break
            if matches:
                lines = [f"[bold]Search results for '[cyan]{query}[/]':[/]\n"]
                for m in matches:
                    rel = m.relative_to(self._cwd)
                    if m.is_dir():
                        lines.append(f"  [cyan]{rel}/[/]")
                    else:
                        lines.append(f"  {rel}")
                preview.update("\n".join(lines))
            else:
                preview.update(f"[dim]No files matching '[yellow]{query}[/]'[/]")
        except Exception as exc:
            preview.update(f"[red]Search error: {exc}[/]")

    def action_delete_path(self) -> None:
        """Delete the currently selected file or directory (with confirmation)."""
        path = self._selected_path
        if path is None:
            self.app.notify("No file selected", severity="warning")
            return

        def _on_confirm(confirmed: bool) -> None:
            if not confirmed:
                return
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    self.app.notify(f"Deleted directory: {path.name}", severity="warning")
                else:
                    path.unlink()
                    self.app.notify(f"Deleted file: {path.name}", severity="warning")
                # Reload the tree
                tree = self.query_one("#files-tree", DirectoryTree)
                tree.reload()
                self._selected_path = None
                self.query_one("#files-preview", Static).update(
                    "[dim]Select a file in the tree to preview it.[/]"
                )
                self.query_one("#files-meta", Label).update("")
            except PermissionError:
                self.app.notify(f"Permission denied: cannot delete {path.name}", severity="error")
            except Exception as exc:
                self.app.notify(f"Delete failed: {exc}", severity="error")

        self.app.push_screen(ConfirmDelete(path), _on_confirm)

    def action_new_dir(self) -> None:
        """Create a new directory inside the current directory."""
        base = (
            self._selected_path.parent
            if self._selected_path and self._selected_path.is_file()
            else (self._selected_path or self._cwd)
        )

        def _on_name(name: str | None) -> None:
            if not name:
                return
            new_path = base / name
            try:
                new_path.mkdir(parents=False, exist_ok=False)
                self.app.notify(f"Created directory: {name}", severity="information")
                tree = self.query_one("#files-tree", DirectoryTree)
                tree.reload()
            except FileExistsError:
                self.app.notify(f"Already exists: {name}", severity="error")
            except PermissionError:
                self.app.notify("Permission denied", severity="error")
            except Exception as exc:
                self.app.notify(f"Failed: {exc}", severity="error")

        self.app.push_screen(NewDirDialog(), _on_name)

    def action_rename_path(self) -> None:
        """Rename the currently selected file or directory."""
        path = self._selected_path
        if path is None:
            self.app.notify("No file selected", severity="warning")
            return

        def _on_name(name: str | None) -> None:
            if not name or name == path.name:
                return
            new_path = path.parent / name
            try:
                path.rename(new_path)
                self.app.notify(
                    f"Renamed: {path.name} → {name}", severity="information"
                )
                tree = self.query_one("#files-tree", DirectoryTree)
                tree.reload()
                self._selected_path = new_path
            except FileExistsError:
                self.app.notify(f"Already exists: {name}", severity="error")
            except PermissionError:
                self.app.notify("Permission denied", severity="error")
            except Exception as exc:
                self.app.notify(f"Rename failed: {exc}", severity="error")

        self.app.push_screen(RenameDialog(path), _on_name)
