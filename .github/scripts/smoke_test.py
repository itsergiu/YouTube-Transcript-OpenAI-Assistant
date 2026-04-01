import py_compile
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import utility_settings
from llama_ytb import LlamaContext


def assert_video_id(url: str, expected: str) -> None:
    context = LlamaContext(ytb_link=url, path="")
    actual = context._get_video_id()
    assert actual == expected, f"expected {expected}, got {actual}"


def main() -> None:
    py_compile.compile(str(REPO_ROOT / "app.py"), doraise=True)
    assert callable(utility_settings.openai_psw_check)

    context = LlamaContext(ytb_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ", path="")
    assert context.persist_dir.endswith("storage")
    assert context.ytb_content_valid is False

    assert_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ")
    assert_video_id("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ")
    assert_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ")


if __name__ == "__main__":
    main()
