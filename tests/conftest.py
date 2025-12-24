"""Pytest fixtures for tests."""

import pytest

# Sample transcript for testing
SAMPLE_TRANSCRIPT = """[10:00 AM] Alice Smith: Welcome everyone to the project kickoff meeting.

[10:01 AM] Bob Johnson: Thanks Alice. Excited to get started.

[10:02 AM] Alice Smith: Our main goal is to launch the new product by Q4. Bob, can you give us an update on the technical requirements?

[10:03 AM] Bob Johnson: We'll need to build three main components: the frontend, backend API, and database. Estimated timeline is 12 weeks.

[10:04 AM] Carol Davis: What about the budget? Do we have approval?

[10:05 AM] Alice Smith: Yes, we have a $50,000 budget approved for this quarter. Carol, you'll manage the finances.

[10:06 AM] Bob Johnson: We should also consider hiring one more engineer to meet the deadline.

[10:07 AM] Alice Smith: Agreed. I'll work with HR on the job posting this week.

[10:08 AM] Carol Davis: Any risks we should be aware of?

[10:09 AM] Bob Johnson: The main risk is the third-party API integration. If they have delays, it could push our timeline back.

[10:10 AM] Alice Smith: Let's plan for that contingency. Great meeting everyone!"""

SAMPLE_SUMMARY = """The team held a project kickoff meeting to plan the launch of a new product by Q4. The project will consist of three main components (frontend, backend API, and database) with a 12-week timeline. A budget of $50,000 has been approved, which Carol will manage. The team decided to hire an additional engineer to meet the deadline, and Alice will coordinate with HR. The main risk identified is potential delays from third-party API integration."""


@pytest.fixture
def sample_transcript():
    """Provide a sample transcript for testing."""
    return SAMPLE_TRANSCRIPT


@pytest.fixture
def sample_summary():
    """Provide a sample summary for testing."""
    return SAMPLE_SUMMARY


@pytest.fixture
def temp_transcript_file(tmp_path):
    """Create a temporary transcript file."""
    file_path = tmp_path / "test_meeting.txt"
    file_path.write_text(SAMPLE_TRANSCRIPT)
    return file_path
