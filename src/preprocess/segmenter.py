"""Transcript segmentation utilities."""

import re
from datetime import datetime
from typing import Dict, List, Optional


class TranscriptSegment:
    """Represents a segment of transcript."""

    def __init__(
        self,
        speaker: str,
        text: str,
        timestamp: Optional[str] = None,
        start_line: Optional[int] = None,
    ):
        """
        Initialize transcript segment.

        Args:
            speaker: Speaker name
            text: Segment text
            timestamp: Optional timestamp
            start_line: Optional line number in original transcript
        """
        self.speaker = speaker
        self.text = text
        self.timestamp = timestamp
        self.start_line = start_line

    def to_dict(self) -> Dict:
        """Convert segment to dictionary."""
        return {
            "speaker": self.speaker,
            "text": self.text,
            "timestamp": self.timestamp,
            "start_line": self.start_line,
        }


def segment_by_speaker(text: str) -> List[TranscriptSegment]:
    """
    Segment transcript by speaker turns.

    Handles formats like:
    - [TIME] Speaker Name: text
    - Speaker Name: text
    - Speaker: text

    Args:
        text: Raw transcript text

    Returns:
        List of TranscriptSegment objects
    """
    segments = []

    # Pattern to match speaker lines
    # Matches: [timestamp] Speaker Name: text OR Speaker Name: text
    pattern = r"(?:\[(.*?)\]\s+)?([A-Z][a-zA-Z\s\.]+?):\s*(.+?)(?=(?:\n\[|\n[A-Z][a-zA-Z\s\.]+?:|\Z))"

    matches = re.finditer(pattern, text, re.DOTALL)

    line_num = 0
    for match in matches:
        timestamp = match.group(1)  # Optional timestamp
        speaker = match.group(2).strip()
        content = match.group(3).strip()

        segments.append(
            TranscriptSegment(
                speaker=speaker, text=content, timestamp=timestamp, start_line=line_num
            )
        )
        line_num += 1

    return segments


def segment_by_time(text: str, window_minutes: int = 5) -> List[Dict]:
    """
    Segment transcript into time-based windows.

    Args:
        text: Transcript text with timestamps
        window_minutes: Size of time window in minutes

    Returns:
        List of dictionaries with time windows and content
    """
    segments = segment_by_speaker(text)

    if not segments or not any(s.timestamp for s in segments):
        # No timestamps, return single segment
        return [{"window": "full", "content": text}]

    time_windows = []
    current_window = []
    window_start = None

    for segment in segments:
        if segment.timestamp:
            try:
                # Parse timestamp (supports multiple formats)
                timestamp = _parse_timestamp(segment.timestamp)

                if window_start is None:
                    window_start = timestamp

                minutes_diff = (timestamp - window_start).total_seconds() / 60

                if minutes_diff >= window_minutes:
                    # Save current window
                    if current_window:
                        time_windows.append(
                            {
                                "window_start": window_start.isoformat(),
                                "segments": current_window,
                            }
                        )
                    current_window = [segment.to_dict()]
                    window_start = timestamp
                else:
                    current_window.append(segment.to_dict())
            except ValueError:
                # Invalid timestamp, add to current window
                current_window.append(segment.to_dict())
        else:
            current_window.append(segment.to_dict())

    # Add final window
    if current_window:
        time_windows.append(
            {
                "window_start": window_start.isoformat() if window_start else "unknown",
                "segments": current_window,
            }
        )

    return time_windows


def parse_teams_format(teams_data: Dict) -> str:
    """
    Parse Microsoft Teams export format into plain text transcript.

    Args:
        teams_data: Teams meeting export dictionary

    Returns:
        Formatted transcript text
    """
    if "messages" not in teams_data:
        raise ValueError("Invalid Teams format: missing 'messages' field")

    transcript_parts = []

    for message in teams_data["messages"]:
        speaker = message.get("speaker", "Unknown")
        text = message.get("text", "")
        timestamp = message.get("timestamp", "")

        if timestamp:
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%I:%M %p")
            except ValueError:
                formatted_time = timestamp

            transcript_parts.append(f"[{formatted_time}] {speaker}: {text}")
        else:
            transcript_parts.append(f"{speaker}: {text}")

    return "\n\n".join(transcript_parts)


def _parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string into datetime object.

    Args:
        timestamp_str: Timestamp string

    Returns:
        datetime object

    Raises:
        ValueError: If timestamp cannot be parsed
    """
    # Try multiple formats
    formats = [
        "%I:%M %p",  # 10:15 AM
        "%H:%M",  # 14:30
        "%I:%M:%S %p",  # 10:15:30 AM
        "%H:%M:%S",  # 14:30:45
        "%Y-%m-%dT%H:%M:%S",  # ISO format
    ]

    for fmt in formats:
        try:
            # For time-only formats, use today's date
            if "%" not in fmt or "Y" not in fmt:
                today = datetime.now().date()
                time_obj = datetime.strptime(timestamp_str, fmt).time()
                return datetime.combine(today, time_obj)
            else:
                return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
