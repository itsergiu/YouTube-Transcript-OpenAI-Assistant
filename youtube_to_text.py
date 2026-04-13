from __future__ import annotations

import argparse
from pathlib import Path

from llama_ytb import LlamaContext


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a YouTube transcript using the repo's shared transcript logic."
    )
    parser.add_argument("video", help="YouTube URL to transcribe")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path. Defaults to stdout only.",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    context = LlamaContext(args.video)
    context.extract_ytb()

    if not context.ytb_content_valid:
        parser.exit(2, f"Failed to fetch transcript: {context.extract_error}\n")

    transcript = context.ytb_content or ""

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(transcript + "\n", encoding="utf-8")

    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
