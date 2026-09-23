from typing import TYPE_CHECKING

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Input, Label

from kanban_tui.classes.task import Task

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


class FilterBar(Horizontal):
    """Inline, session-only board search."""

    app: "KanbanTui"
    BINDINGS = [Binding("escape", "close", "Close search", show=False, priority=True)]
    category_names: dict[int, str]

    def __init__(self) -> None:
        super().__init__(id="filter_bar", classes="-hidden")
        self.category_names = {}

    def compose(self):
        yield Label("Search", id="filter_prompt")
        yield Input(
            placeholder="Search title, description, or category with :category",
            id="filter_query",
        )

    def on_mount(self) -> None:
        self.refresh_category_names()
        self.watch(self.app, "task_list", self.refresh_category_names)

    def refresh_category_names(self) -> None:
        self.category_names = {
            category.category_id: category.name
            for category in self.app.backend.get_all_categories()
        }

    @on(Input.Changed, "#filter_query")
    async def update_filter(self, event: Input.Changed) -> None:
        query = event.value.strip().casefold()
        self.app.filter_query = query
        await self.app.get_screen("board").query_one("KanbanBoard").refresh_columns()

    def action_close(self) -> None:
        self.add_class("-hidden")
        self.app.set_focus(None)

    def matches(self, task: Task) -> bool:
        query = getattr(self.app, "filter_query", "")
        category_name = (
            self.category_names.get(task.category, "")
            if task.category is not None
            else ""
        )
        if query.startswith(":"):
            category_query = query[1:].strip()
            return not category_query or category_query in category_name.casefold()
        searchable = f"{task.title}\n{task.description}\n{category_name}".casefold()
        return not query or query in searchable
