"""Utilities Module"""

import sys

class ProgressBar:
    """A clean, reusable terminal progress bar with centered percentage text."""
    def __init__(self, length: int = 50):
        self.length = length

    def update(self, percent: int, message: str = "") -> None:
        # Clamp percent between 0 and 100
        percent = max(0, min(100, percent))
        filled = int(self.length * (percent / 100))
        
        # Build the bar ('=' for filled, ' ' for empty)
        bar = ["=" if i < filled else " " for i in range(self.length)]
        
        # Overlay the centered percentage text
        pct_text = f" [{percent}%] "
        start_idx = (self.length - len(pct_text)) // 2
        
        for i, char in enumerate(pct_text):
            idx = start_idx + i
            if 0 <= idx < self.length:
                bar[idx] = char
                
        sys.stdout.write(f"\r[{''.join(bar)}] {message:<45}")
        sys.stdout.flush()
        
        if percent >= 100:
            sys.stdout.write("\n")