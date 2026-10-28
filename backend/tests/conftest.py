import sys
from pathlib import Path

# Make the src layout importable regardless of the directory pytest is invoked from.
SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
