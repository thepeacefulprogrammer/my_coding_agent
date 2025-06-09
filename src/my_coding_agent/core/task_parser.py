"""
Markdown Task File Parser

This module provides functionality to parse, manipulate, and save markdown task files.
It supports nested task structures, task completion tracking, and managing relevant files sections.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TaskItem:
    """Represents a single task item in a markdown task list."""

    id: str
    title: str
    completed: bool
    level: int
    line_number: int
    subtasks: list["TaskItem"] = field(default_factory=list)
    parent_id: str | None = None

    def all_subtasks_complete(self) -> bool:
        """Check if all subtasks are completed.

        Returns:
            True if all subtasks are complete or if there are no subtasks
        """
        if not self.subtasks:
            return True
        return all(subtask.completed for subtask in self.subtasks)

    def add_subtask(self, subtask: "TaskItem") -> None:
        """Add a subtask to this task.

        Args:
            subtask: The subtask to add
        """
        subtask.parent_id = self.id
        self.subtasks.append(subtask)


@dataclass
class TaskSection:
    """Represents a section containing multiple tasks."""

    id: str
    title: str
    completed: bool
    line_number: int
    tasks: list[TaskItem] = field(default_factory=list)

    def all_tasks_complete(self) -> bool:
        """Check if all tasks in this section are completed.

        Returns:
            True if all tasks are complete AND there are tasks, False if empty or incomplete
        """
        if not self.tasks:
            return False  # Empty sections are not considered complete
        return all(
            task.completed and task.all_subtasks_complete() for task in self.tasks
        )

    def add_task(self, task: TaskItem) -> None:
        """Add a task to this section.

        Args:
            task: The task to add
        """
        self.tasks.append(task)


class TaskParser:
    """Parser for markdown task files with nested task structures."""

    def __init__(self, file_path: Path):
        """Initialize the task parser.

        Args:
            file_path: Path to the markdown task file
        """
        self.file_path = Path(file_path)
        self.sections: list[TaskSection] = []
        self.relevant_files: list[str] = []
        self._lines: list[str] = []
        self._parsed = False

    def parse(self) -> None:
        """Parse the markdown task file and extract task structure."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Task file not found: {self.file_path}")

        self._lines = self.file_path.read_text().splitlines()
        self.sections = []
        self.relevant_files = []

        current_section: TaskSection | None = None
        current_task: TaskItem | None = None
        in_relevant_files = False
        in_tasks = False

        for line_num, line in enumerate(self._lines, 1):
            line = line.rstrip()

            # Track sections
            if line.strip() == "## Relevant Files":
                in_relevant_files = True
                in_tasks = False
                continue
            elif line.strip() == "## Tasks":
                in_relevant_files = False
                in_tasks = True
                continue
            elif line.startswith("## "):
                in_relevant_files = False
                in_tasks = False
                continue

            # Parse relevant files
            if in_relevant_files and line.strip().startswith("- `"):
                self.relevant_files.append(line.strip())
                continue

            # Parse tasks
            if in_tasks and line.strip():
                # Match task items: - [x] or - [ ] followed by ID and title
                task_match = re.match(
                    r"^(\s*)- \[([ x])\]\s+(\d+(?:\.\d+)*)\s+(.+)$", line
                )
                if task_match:
                    indent, completed_char, task_id, title = task_match.groups()
                    level = len(indent) // 2  # Assuming 2 spaces per indentation level
                    completed = completed_char == "x"

                    task_item = TaskItem(
                        id=task_id,
                        title=title,
                        completed=completed,
                        level=level,
                        line_number=line_num,
                    )

                    if level == 0:
                        # Top-level section
                        current_section = TaskSection(
                            id=task_id,
                            title=title,
                            completed=completed,
                            line_number=line_num,
                            tasks=[],
                        )
                        self.sections.append(current_section)
                        current_task = None
                    elif level == 1 and current_section:
                        # Task under a section
                        current_section.add_task(task_item)
                        current_task = task_item
                    elif level >= 2 and current_task:
                        # Subtask - find the appropriate parent
                        parent_task = self._find_parent_task(
                            current_section, task_item.id, level
                        )
                        if parent_task:
                            parent_task.add_subtask(task_item)

        # Update completion status based on subtasks/tasks
        self._update_completion_status()
        self._parsed = True

    def _find_parent_task(
        self, section: TaskSection, task_id: str, level: int
    ) -> TaskItem | None:
        """Find the parent task for a subtask based on ID hierarchy.

        Args:
            section: The section to search in
            task_id: The ID of the task to find parent for
            level: The indentation level of the task

        Returns:
            The parent task if found, None otherwise
        """
        # Split the task ID to find parent (e.g., "2.2.1" -> parent is "2.2")
        parts = task_id.split(".")
        if len(parts) <= 1:
            return None

        parent_id = ".".join(parts[:-1])

        # Search for parent in the section's tasks and their subtasks
        def find_task_recursive(
            tasks: list[TaskItem], target_id: str
        ) -> TaskItem | None:
            for task in tasks:
                if task.id == target_id:
                    return task
                found = find_task_recursive(task.subtasks, target_id)
                if found:
                    return found
            return None

        return find_task_recursive(section.tasks, parent_id)

    def _update_completion_status(self) -> None:
        """Update completion status for parent tasks and sections based on their children."""
        for section in self.sections:
            # Update task completion based on subtasks (recursive)
            for task in section.tasks:
                self._update_task_completion_recursive(task)

            # Update section completion based on all tasks and their subtasks
            section.completed = section.all_tasks_complete()

    def _update_task_completion_recursive(self, task: TaskItem) -> None:
        """Recursively update task completion based on all subtasks.

        Args:
            task: The task to update
        """
        # First update all subtasks recursively
        for subtask in task.subtasks:
            self._update_task_completion_recursive(subtask)

        # If this task has subtasks and all are complete, mark this task as complete
        if task.subtasks and all(subtask.completed for subtask in task.subtasks):
            task.completed = True

    def mark_task_complete(self, task_id: str) -> bool:
        """Mark a task as completed and update parent completion status.

        Args:
            task_id: The ID of the task to mark as complete

        Returns:
            True if the task was found and marked complete, False otherwise
        """
        task = self.find_task(task_id)
        if task:
            task.completed = True

            # Update parent completion status recursively
            self._update_completion_status()
            return True
        return False

    def find_task(self, task_id: str) -> TaskItem | None:
        """Find a task by its ID across all sections.

        Args:
            task_id: The ID of the task to find

        Returns:
            The task if found, None otherwise
        """

        def search_tasks(tasks: list[TaskItem]) -> TaskItem | None:
            for task in tasks:
                if task.id == task_id:
                    return task
                found = search_tasks(task.subtasks)
                if found:
                    return found
            return None

        for section in self.sections:
            if section.id == task_id:
                # Return a dummy task item for sections (for consistency)
                return TaskItem(
                    id=section.id,
                    title=section.title,
                    completed=section.completed,
                    level=0,
                    line_number=section.line_number,
                )

            found = search_tasks(section.tasks)
            if found:
                return found

        return None

    def add_task(self, section_id: str, task_id: str, title: str) -> bool:
        """Add a new task to a section.

        Args:
            section_id: The ID of the section to add the task to
            task_id: The ID for the new task
            title: The title of the new task

        Returns:
            True if the task was added successfully, False otherwise
        """
        section = next((s for s in self.sections if s.id == section_id), None)
        if section:
            new_task = TaskItem(
                id=task_id,
                title=title,
                completed=False,
                level=1,
                line_number=len(self._lines) + 1,
            )
            section.add_task(new_task)
            return True
        return False

    def add_subtask(self, parent_task_id: str, subtask_id: str, title: str) -> bool:
        """Add a new subtask to an existing task.

        Args:
            parent_task_id: The ID of the parent task
            subtask_id: The ID for the new subtask
            title: The title of the new subtask

        Returns:
            True if the subtask was added successfully, False otherwise
        """
        parent_task = self.find_task(parent_task_id)
        if parent_task:
            new_subtask = TaskItem(
                id=subtask_id,
                title=title,
                completed=False,
                level=parent_task.level + 1,
                line_number=len(self._lines) + 1,
                parent_id=parent_task_id,
            )
            parent_task.add_subtask(new_subtask)
            return True
        return False

    def add_relevant_file(self, file_path: str, description: str) -> None:
        """Add a new file to the relevant files section.

        Args:
            file_path: The path to the file
            description: Description of the file
        """
        file_entry = f"- `{file_path}` - {description}"
        self.relevant_files.append(file_entry)

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about task completion.

        Returns:
            Dictionary with completion statistics
        """
        total_sections = len(self.sections)
        completed_sections = sum(1 for s in self.sections if s.completed)

        total_tasks = 0
        completed_tasks = 0

        def count_tasks(tasks: list[TaskItem]) -> tuple[int, int]:
            total = len(tasks)
            complete = sum(1 for t in tasks if t.completed)

            for task in tasks:
                sub_total, sub_complete = count_tasks(task.subtasks)
                total += sub_total
                complete += sub_complete

            return total, complete

        for section in self.sections:
            section_total, section_complete = count_tasks(section.tasks)
            total_tasks += section_total
            completed_tasks += section_complete

        completion_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        return {
            "total_sections": total_sections,
            "completed_sections": completed_sections,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": completion_percentage,
        }

    def save(self) -> None:
        """Save the current state back to the markdown file."""
        if not self._parsed:
            raise RuntimeError("Cannot save before parsing")

        output_lines: list[str] = []

        # Write relevant files section
        if self.relevant_files:
            output_lines.append("## Relevant Files")
            output_lines.append("")
            for file_entry in self.relevant_files:
                output_lines.append(file_entry)
            output_lines.append("")

        # Write tasks section
        output_lines.append("## Tasks")
        output_lines.append("")

        for section in self.sections:
            # Write section header
            status = "x" if section.completed else " "
            output_lines.append(f"- [{status}] {section.id} {section.title}")

            # Write tasks in the section
            for task in section.tasks:
                self._write_task_recursive(task, output_lines, 1)

            output_lines.append("")

        # Write to file
        self.file_path.write_text("\n".join(output_lines))

    def _write_task_recursive(
        self, task: TaskItem, output_lines: list[str], level: int
    ) -> None:
        """Recursively write a task and its subtasks to the output.

        Args:
            task: The task to write
            output_lines: List to append output lines to
            level: The indentation level
        """
        indent = "  " * level
        status = "x" if task.completed else " "
        output_lines.append(f"{indent}- [{status}] {task.id} {task.title}")

        # Write subtasks
        for subtask in task.subtasks:
            self._write_task_recursive(subtask, output_lines, level + 1)
