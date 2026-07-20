"""Put the repo root on sys.path so `from resistancemap...` imports resolve."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
