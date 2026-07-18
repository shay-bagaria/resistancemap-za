"""Put the app directory on sys.path so `from engine import pk` resolves."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
