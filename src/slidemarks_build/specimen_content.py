"""Content shared by the HTML, PowerPoint and Word specimens so all three
show the same glyphs in the same arrangements."""

LADDER_PT = [10, 12, 14, 18, 24, 36]
CATEGORY_TITLES = {"harvey": "Harvey balls", "arrows": "Arrows", "status": "Status", "trend": "Trend"}

SCORECARD_HEADER = ("Capability", "Option A", "Option B", "Option C", "Status", "Trend")
SCORECARD_ROWS = [
    ("Offline use", "harvey-100", "harvey-50", "harvey-0", "status-check", "trend-up"),
    ("Font embedding", "harvey-75", "harvey-75", "harvey-25", "status-check", "arrow-right"),
    ("Web support", "harvey-50", "harvey-100", "harvey-25", "status-cross", "trend-down"),
    ("Table alignment", "harvey-100", "harvey-25", "harvey-0", "dot-filled", "arrow-up"),
    ("Recolour as text", "harvey-25", "harvey-50", "harvey-75", "dot-empty", "arrow-down"),
]
