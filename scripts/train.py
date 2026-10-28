from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.model import train
import json
if __name__ == "__main__":
    print(json.dumps(train(), indent=2, ensure_ascii=False))
