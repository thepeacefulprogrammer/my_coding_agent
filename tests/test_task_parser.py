"""
Unit tests for the TaskParser class.

This module tests the markdown task file parser functionality including:
- Parsing markdown task files with nested task structures
- Reading task status (completed/incomplete)
- Updating task status and marking completion
- Managing the "Relevant Files" section
- Adding new tasks and subtasks
- Preserving markdown structure and formatting
"""

import tempfile
from pathlib import Path

import pytest
from src.my_coding_agent.core.task_parser import TaskItem, TaskParser, TaskSection


class TestTaskItem:
    """Test suite for TaskItem data class."""

    def test_task_item_creation(self):
        """Test TaskItem can be created with basic properties."""
        task = TaskItem(
            id="1.1", title="Test task", completed=False, level=1, line_number=5
        )

        assert task.id == "1.1"
        assert task.title == "Test task"
        assert not task.completed
        assert task.level == 1
        assert task.line_number == 5
        assert task.subtasks == []
        assert task.parent_id is None

    def test_task_item_with_subtasks(self):
        """Test TaskItem with subtasks."""
        subtask = TaskItem(
            id="1.1.1", title="Subtask", completed=True, level=2, line_number=6
        )
        task = TaskItem(
            id="1.1",
            title="Parent task",
            completed=False,
            level=1,
            line_number=5,
            subtasks=[subtask],
        )

        assert len(task.subtasks) == 1
        assert task.subtasks[0].title == "Subtask"
        assert task.subtasks[0].completed

    def test_task_item_is_parent_complete(self):
        """Test checking if all subtasks are complete."""
        subtask1 = TaskItem(
            id="1.1.1", title="Subtask 1", completed=True, level=2, line_number=6
        )
        subtask2 = TaskItem(
            id="1.1.2", title="Subtask 2", completed=True, level=2, line_number=7
        )
        task = TaskItem(
            id="1.1",
            title="Parent task",
            completed=False,
            level=1,
            line_number=5,
            subtasks=[subtask1, subtask2],
        )

        assert task.all_subtasks_complete()

        # Make one subtask incomplete
        subtask2.completed = False
        assert not task.all_subtasks_complete()

    def test_task_item_no_subtasks_complete(self):
        """Test that task with no subtasks returns True for all_subtasks_complete."""
        task = TaskItem(id="1.1", title="Task", completed=False, level=1, line_number=5)
        assert task.all_subtasks_complete()


class TestTaskSection:
    """Test suite for TaskSection data class."""

    def test_task_section_creation(self):
        """Test TaskSection can be created with basic properties."""
        section = TaskSection(
            id="1.0", title="Test Section", completed=False, line_number=3, tasks=[]
        )

        assert section.id == "1.0"
        assert section.title == "Test Section"
        assert not section.completed
        assert section.line_number == 3
        assert section.tasks == []

    def test_task_section_with_tasks(self):
        """Test TaskSection with tasks."""
        task1 = TaskItem(
            id="1.1", title="Task 1", completed=True, level=1, line_number=4
        )
        task2 = TaskItem(
            id="1.2", title="Task 2", completed=False, level=1, line_number=5
        )

        section = TaskSection(
            id="1.0",
            title="Test Section",
            completed=False,
            line_number=3,
            tasks=[task1, task2],
        )

        assert len(section.tasks) == 2
        assert section.tasks[0].title == "Task 1"
        assert section.tasks[1].title == "Task 2"

    def test_task_section_is_complete(self):
        """Test checking if all tasks in section are complete."""
        task1 = TaskItem(
            id="1.1", title="Task 1", completed=True, level=1, line_number=4
        )
        task2 = TaskItem(
            id="1.2", title="Task 2", completed=True, level=1, line_number=5
        )

        section = TaskSection(
            id="1.0",
            title="Test Section",
            completed=False,
            line_number=3,
            tasks=[task1, task2],
        )

        assert section.all_tasks_complete()

        # Make one task incomplete
        task2.completed = False
        assert not section.all_tasks_complete()


class TestTaskParser:
    """Test suite for TaskParser class."""

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown content for testing."""
        return """## Relevant Files

- `file1.py` - Description 1
- `file2.py` - Description 2

## Tasks

- [x] 1.0 Completed Section
  - [x] 1.1 Completed task
  - [x] 1.2 Another completed task

- [ ] 2.0 Incomplete Section
  - [x] 2.1 Completed subtask
  - [ ] 2.2 Incomplete subtask
    - [x] 2.2.1 Nested completed task
    - [ ] 2.2.2 Nested incomplete task
  - [ ] 2.3 Another incomplete subtask

- [ ] 3.0 Empty Section
"""

    @pytest.fixture
    def temp_task_file(self, sample_markdown):
        """Create a temporary task file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(sample_markdown)
            f.flush()
            yield Path(f.name)

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    def test_task_parser_initialization(self, temp_task_file):
        """Test TaskParser can be initialized with a file path."""
        parser = TaskParser(temp_task_file)
        assert parser.file_path == temp_task_file
        assert parser.sections == []
        assert parser.relevant_files == []

    def test_parse_task_file(self, temp_task_file):
        """Test parsing a complete task file."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Should have parsed 3 sections
        assert len(parser.sections) == 3

        # Check first section
        section1 = parser.sections[0]
        assert section1.id == "1.0"
        assert section1.title == "Completed Section"
        assert section1.completed  # Should be marked complete
        assert len(section1.tasks) == 2

        # Check second section
        section2 = parser.sections[1]
        assert section2.id == "2.0"
        assert section2.title == "Incomplete Section"
        assert not section2.completed
        assert len(section2.tasks) == 3

        # Check nested tasks
        task_2_2 = section2.tasks[1]  # Task 2.2
        assert task_2_2.id == "2.2"
        assert task_2_2.title == "Incomplete subtask"
        assert not task_2_2.completed
        assert len(task_2_2.subtasks) == 2

        # Check deeply nested task
        nested_task = task_2_2.subtasks[0]
        assert nested_task.id == "2.2.1"
        assert nested_task.title == "Nested completed task"
        assert nested_task.completed

    def test_parse_relevant_files(self, temp_task_file):
        """Test parsing the relevant files section."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        assert len(parser.relevant_files) == 2
        assert "file1.py" in parser.relevant_files[0]
        assert "Description 1" in parser.relevant_files[0]
        assert "file2.py" in parser.relevant_files[1]
        assert "Description 2" in parser.relevant_files[1]

    def test_mark_task_complete(self, temp_task_file):
        """Test marking a task as complete."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Mark task 2.2 as complete
        success = parser.mark_task_complete("2.2")
        assert success

        # Find the task and verify it's marked complete
        section2 = parser.sections[1]
        task_2_2 = next(t for t in section2.tasks if t.id == "2.2")
        assert task_2_2.completed

    def test_mark_parent_complete_when_all_subtasks_done(self, temp_task_file):
        """Test that parent tasks are marked complete when all subtasks are done."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Complete the remaining subtask in 2.2
        parser.mark_task_complete("2.2.2")

        # Parent task 2.2 should now be complete since all subtasks are done
        section2 = parser.sections[1]
        task_2_2 = next(t for t in section2.tasks if t.id == "2.2")
        assert task_2_2.completed

    def test_mark_section_complete_when_all_tasks_done(self, temp_task_file):
        """Test that sections are marked complete when all tasks are done."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Complete all remaining tasks in section 2.0
        # Task 2.1 is already complete
        # For task 2.2, we need to complete its subtasks first
        parser.mark_task_complete("2.2.2")  # Complete the incomplete subtask
        parser.mark_task_complete("2.2")  # Now we can complete the parent
        parser.mark_task_complete("2.3")  # Complete the other task

        # Section 2.0 should now be complete
        section2 = parser.sections[1]
        assert section2.completed

    def test_add_new_task(self, temp_task_file):
        """Test adding a new task to a section."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Add a new task to section 2.0
        success = parser.add_task("2.0", "2.4", "New task description")
        assert success

        # Verify the task was added
        section2 = parser.sections[1]
        assert len(section2.tasks) == 4
        new_task = section2.tasks[-1]
        assert new_task.id == "2.4"
        assert new_task.title == "New task description"
        assert not new_task.completed

    def test_add_new_subtask(self, temp_task_file):
        """Test adding a new subtask to an existing task."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Add a new subtask to task 2.2
        success = parser.add_subtask("2.2", "2.2.3", "New subtask description")
        assert success

        # Verify the subtask was added
        section2 = parser.sections[1]
        task_2_2 = next(t for t in section2.tasks if t.id == "2.2")
        assert len(task_2_2.subtasks) == 3
        new_subtask = task_2_2.subtasks[-1]
        assert new_subtask.id == "2.2.3"
        assert new_subtask.title == "New subtask description"
        assert not new_subtask.completed

    def test_add_relevant_file(self, temp_task_file):
        """Test adding a new file to the relevant files section."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        initial_count = len(parser.relevant_files)
        parser.add_relevant_file("new_file.py", "New file description")

        assert len(parser.relevant_files) == initial_count + 1
        assert "new_file.py" in parser.relevant_files[-1]
        assert "New file description" in parser.relevant_files[-1]

    def test_save_to_file(self, temp_task_file):
        """Test saving the parsed and modified content back to file."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Make some changes
        parser.mark_task_complete("2.2")
        parser.add_relevant_file("test.py", "Test file")

        # Save changes
        parser.save()

        # Read the file back and verify changes
        content = temp_task_file.read_text()
        assert "[x] 2.2 Incomplete subtask" in content
        assert "test.py" in content
        assert "Test file" in content

    def test_find_task_by_id(self, temp_task_file):
        """Test finding tasks by their ID."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        # Find a top-level task
        task = parser.find_task("2.1")
        assert task is not None
        assert task.id == "2.1"
        assert task.title == "Completed subtask"

        # Find a nested task
        nested_task = parser.find_task("2.2.1")
        assert nested_task is not None
        assert nested_task.id == "2.2.1"
        assert nested_task.title == "Nested completed task"

        # Try to find non-existent task
        missing_task = parser.find_task("99.99")
        assert missing_task is None

    def test_get_task_statistics(self, temp_task_file):
        """Test getting statistics about task completion."""
        parser = TaskParser(temp_task_file)
        parser.parse()

        stats = parser.get_statistics()

        assert "total_sections" in stats
        assert "completed_sections" in stats
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "completion_percentage" in stats

        assert stats["total_sections"] == 3
        assert (
            stats["completed_sections"] == 1
        )  # Only section 1.0 is complete (section 3.0 is empty but not complete)
        assert stats["total_tasks"] > 0
        assert 0 <= stats["completion_percentage"] <= 100

    def test_invalid_file_handling(self):
        """Test handling of invalid or non-existent files."""
        invalid_path = Path("non_existent_file.md")
        parser = TaskParser(invalid_path)

        with pytest.raises(FileNotFoundError):
            parser.parse()

    def test_malformed_markdown_handling(self):
        """Test handling of malformed markdown content."""
        malformed_content = """## Tasks
Not a valid task list
- This is not a task checkbox
[x] Missing hyphen
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(malformed_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            parser = TaskParser(temp_path)
            parser.parse()  # Should not crash
            assert len(parser.sections) == 0  # No valid sections found
        finally:
            temp_path.unlink(missing_ok=True)
