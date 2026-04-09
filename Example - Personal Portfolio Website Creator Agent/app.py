from pathlib import Path

from ui import build_ui
from config import APP_HOST, APP_PORT

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name=APP_HOST,
        server_port=APP_PORT,
        share=True,
        allowed_paths=[str(Path(__file__).resolve().parent / "outputs")],
    )