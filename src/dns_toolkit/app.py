
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
)


class DNSToolkitApp(App[None]):
    TITLE = "DNS Toolkit"
    SUB_TITLE = "Authoritative DNS Configuration"

    CSS = """
    Screen {
        layout: vertical;
    }

    #workspace {
        height: 1fr;
    }

    #sidebar {
        width: 24;
        border-right: solid $primary;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #content {
        width: 1fr;
        padding: 1 2;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #status {
        height: auto;
        border: round $primary;
        padding: 1;
        margin-bottom: 1;
    }

    #zone-table {
        height: 10;
        margin-bottom: 1;
    }

    #help {
        height: auto;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("question_mark", "help", "Help"),
    ]

    SECTIONS = [
        "Dashboard",
        "Zones",
        "Records",
        "Diagnostics",
        "Settings",
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="workspace"):
            with Vertical(id="sidebar"):
                yield Label("NAVIGATION", id="sidebar-title")
                yield ListView(
                    *[
                        ListItem(Label(section), id=f"nav-{section.lower()}")
                        for section in self.SECTIONS
                    ],
                    initial_index=0,
                    id="navigation",
                )

            with Vertical(id="content"):
                yield Static(
                    "DNS TOOLKIT",
                    classes="section-title",
                    id="page-title",
                )
                yield Static(
                    "Local BIND 9 | Configuration preview mode",
                    id="status",
                )
                yield Static("Configured zones", classes="section-title")
                yield DataTable(id="zone-table")
                yield Static(
                    "Select a section from the navigation panel.",
                    id="page-description",
                )
                yield Static(
                    "Preview-first | No system changes until explicitly applied",
                    id="help",
                )

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#zone-table", DataTable)
        table.add_columns("Zone", "Type", "Records", "Status")
        table.cursor_type = "row"

        # These are illustrative rows, not real DNS configuration.
        table.add_row("example.test", "Primary", "4", "Draft")
        table.add_row("lab.test", "Primary", "2", "Draft")

    def on_list_view_selected(
        self, event: ListView.Selected
    ) -> None:
        if event.item.id is None:
            return

        section = event.item.id.removeprefix("nav-")
        title = section.replace("_", " ").title()

        self.query_one("#page-title", Static).update(title)

        descriptions = {
            "dashboard": "Overview of DNS Toolkit.",
            "zones": "Create, inspect, and edit DNS zones.",
            "records": "Manage A, AAAA, CNAME, MX, NS, TXT, and PTR records.",
            "diagnostics": "Inspect DNS responses and validate configurations.",
            "settings": "Configure file paths and DNS backend options.",
        }

        self.query_one("#page-description", Static).update(
            descriptions.get(section, "Section under development.")
        )

    def action_help(self) -> None:
        self.notify(
            "Use the arrow keys to navigate. Press Enter to select. "
            "Press Q to quit.",
            title="DNS Toolkit Help",
        )
