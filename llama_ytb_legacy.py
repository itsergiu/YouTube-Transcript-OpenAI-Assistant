import os
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
from urllib.parse import parse_qs, urlparse

import logging
import sys

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logging.basicConfig(stream=sys.stdout, level=logging.CRITICAL)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# There are five standard levels for logging in Python, listed here in increasing order of severity:
# DEBUG: Detailed information, typically of interest only when diagnosing problems.
# INFO: Confirmation that things are working as expected.
# WARNING: An indication that something unexpected happened or indicative of some problem in the near future (e.g., 'disk space low'). The software is still working as expected.
# ERROR: Due to a more serious problem, the software has not been able to perform some function.
# CRITICAL: A very serious error, indicating that the program itself may be unable to continue running.


class LlamaContext:
    def __init__(self, ytb_link, path=None, ):
        self.path = path if path is not None else ""

        persist_sub_dir = "storage"
        self.persist_dir = os.path.join(self.path, persist_sub_dir)
        if not os.path.exists(self.persist_dir):
            os.makedirs(self.persist_dir)
        data_sub_dir = "data"
        self.data_dir = os.path.join(self.path, data_sub_dir)

        self.ytb_link = ytb_link

        self.cost_model_ada = "ada"  # https://openai.com/pricing
        self.cost_model_davinci = "davinci"  # https://openai.com/pricing
        self.price_ada_1k_tokens = 0.0004
        self.price_davinci_1k_tokens = 0.03

        self.documents = None
        self.ytb_content = None
        self.ytb_content_valid = False
        self.index = None
        # self.index_size = 0
        self.query_engine = None
        self.sleep = None
        self.response_cls = None
        self.response = None
        self.total_tokens = None
        self.total_cost_ada = None
        self.total_cost_davinci = None
        self.extract_error = None

        Settings.llm = OpenAI(model="gpt-4o-mini")
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

    def _get_video_id(self):
        parsed_url = urlparse(self.ytb_link)
        hostname = parsed_url.hostname or ""

        if hostname in {"youtu.be", "www.youtu.be"}:
            return parsed_url.path.lstrip("/")

        if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            if parsed_url.path == "/watch":
                return parse_qs(parsed_url.query).get("v", [None])[0]
            if parsed_url.path.startswith("/shorts/"):
                return parsed_url.path.split("/shorts/", 1)[1].split("/", 1)[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/embed/", 1)[1].split("/", 1)[0]

        return None

    def extract_ytb(self):
        video_id = self._get_video_id()
        if not video_id:
            self.ytb_content = "Invalid YouTube link."
            self.ytb_content_valid = False
            self.extract_error = "Could not parse a YouTube video ID from the link."
            return

        try:
            transcript = self._fetch_transcript(video_id)
            transcript_text = self._transcript_to_text(transcript)

            if transcript_text:
                self.documents = [Document(text=transcript_text)]
                self.ytb_content = transcript_text
                self.ytb_content_valid = True
                self.extract_error = None
            else:
                self.documents = None
                self.ytb_content = "Transcript is empty."
                self.ytb_content_valid = False
                self.extract_error = "The transcript API returned no text."
        except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as exc:
            self.documents = None
            self.ytb_content = "Can't extract text from link!"
            self.ytb_content_valid = False
            self.extract_error = str(exc)
        except Exception as exc:
            self.documents = None
            self.ytb_content = "Can't extract text from link!"
            self.ytb_content_valid = False
            self.extract_error = str(exc)

    def _fetch_transcript(self, video_id):
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            return YouTubeTranscriptApi.get_transcript(video_id)

        api = YouTubeTranscriptApi()

        if hasattr(api, "fetch"):
            return api.fetch(video_id)

        if hasattr(api, "get_transcript"):
            return api.get_transcript(video_id)

        raise AttributeError("Unsupported youtube_transcript_api version.")

    def _transcript_to_text(self, transcript):
        if transcript is None:
            return ""

        if isinstance(transcript, list):
            return " ".join(item.get("text", "") for item in transcript).strip()

        if hasattr(transcript, "snippets"):
            return " ".join(getattr(item, "text", "") for item in transcript.snippets).strip()

        return str(transcript).strip()

    def create_vector_store(self):
        if self.documents is not None:
            self.index = VectorStoreIndex.from_documents(self.documents)

    def load_documents_from_source(self):
        source_dir = os.path.join(self.path, "source")
        if not os.path.isdir(source_dir):
            return False

        source_files = sorted(
            file_name for file_name in os.listdir(source_dir)
            if file_name.lower().endswith(".txt")
        )
        if not source_files:
            return False

        source_path = os.path.join(source_dir, source_files[0])
        with open(source_path, "r", encoding="utf-8") as source_file:
            transcript_text = source_file.read().strip()

        if not transcript_text:
            return False

        self.documents = [Document(text=transcript_text)]
        self.ytb_content = transcript_text
        self.ytb_content_valid = True
        return True

    def save_index(self):
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        print(f"Index saved in path {self.persist_dir}.")

    def load_index(self):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            self.index = load_index_from_storage(storage_context)
        except Exception:
            self.index = None

        if self.index is None and self.load_documents_from_source():
            self.create_vector_store()
            if self.index is not None:
                self.save_index()

    def start_query_engine(self):
        self.query_engine = self.index.as_query_engine()
        print("Query_engine started.")

    def post_question(self, question, sleep=None):
        if sleep is None:
            self.sleep = 0  # trial 20s
        self.response_cls = self.query_engine.query(question)
        self.response = self.response_cls.response

    def estimate_tokens(self, text):
        words = text.split()

        num_words = int(len(words))
        tokens = int((num_words / 0.75))
        tokens_1k = tokens / 1000
        cost_ada = tokens_1k * self.price_ada_1k_tokens
        cost_davinci = tokens_1k * self.price_davinci_1k_tokens
        return tokens, cost_ada, cost_davinci

    def estimate_cost(self):
        total_tokens = 0
        total_cost_ada = 0
        total_cost_davinci = 0
        costs_rounding = 8
        if self.ytb_content_valid:
            for doc in self.documents:
                if hasattr(doc, "get_text"):
                    text = doc.get_text()
                elif hasattr(doc, "get_content"):
                    text = doc.get_content()
                else:
                    text = getattr(doc, "text", "")
                tokens, cost_ada, cost_davinci = self.estimate_tokens(text)
                total_tokens += tokens

                total_cost_ada += cost_ada
                total_cost_ada = round(total_cost_ada, costs_rounding)

                total_cost_davinci += cost_davinci
                total_cost_davinci = round(total_cost_davinci, costs_rounding)

        self.total_tokens = total_tokens
        self.total_cost_ada = total_cost_ada
        self.total_cost_davinci = total_cost_davinci
