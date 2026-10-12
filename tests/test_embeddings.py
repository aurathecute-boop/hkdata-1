import pytest

from hkdata import embeddings


@pytest.fixture
def clean_env(monkeypatch):
    for key in ("HKDATA_EMBED_PROVIDER", "HKDATA_EMBED_MODEL",
                "HKDATA_EMBED_URL", "HKDATA_EMBED_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_default_resolves_to_ollama(clean_env):
    e = embeddings.resolve_embedder()
    assert e.name == "ollama"
    assert e.model == embeddings.DEFAULT_MODEL
    # Ollama fingerprint is the bare model name (backward compatible).
    assert e.fingerprint == embeddings.DEFAULT_MODEL
    # EmbeddingGemma uses asymmetric task prompts on both sides.
    assert e.query_instruction == embeddings.GEMMA_QUERY_INSTRUCTION
    assert e.document_instruction == embeddings.GEMMA_DOCUMENT_INSTRUCTION


def test_ollama_prompts_by_model_family(clean_env):
    gemma = embeddings.resolve_embedder("ollama", "embeddinggemma-2:740m")
    assert gemma.query_instruction == embeddings.GEMMA_QUERY_INSTRUCTION
    assert gemma.document_instruction == embeddings.GEMMA_DOCUMENT_INSTRUCTION

    # A Qwen model keeps its query-only prefix (no document prefix).
    qwen = embeddings.resolve_embedder("ollama", "qwen3-embedding:0.6b")
    assert qwen.query_instruction == embeddings.QWEN_QUERY_INSTRUCTION
    assert qwen.document_instruction == ""

    # Unknown Ollama models take plain text, matching Ollama's own behaviour.
    other = embeddings.resolve_embedder("ollama", "nomic-embed-text")
    assert other.query_instruction == "" and other.document_instruction == ""


def test_openai_resolution(clean_env):
    e = embeddings.resolve_embedder(
        "openai", "text-embedding-3-small",
        "https://example.com/v1/embeddings", "sk-test")
    assert e.name == "openai"
    assert e.fingerprint == "openai:text-embedding-3-small"
    # OpenAI-compatible models take plain queries (no qwen3 instruction prefix).
    assert e.query_instruction == ""


def test_openai_compatible_alias(clean_env):
    e = embeddings.resolve_embedder("openai-compatible")
    assert e.name == "openai"


def test_env_vars_select_provider(clean_env, monkeypatch):
    monkeypatch.setenv("HKDATA_EMBED_PROVIDER", "openai")
    monkeypatch.setenv("HKDATA_EMBED_MODEL", "text-embedding-3-large")
    e = embeddings.resolve_embedder()
    assert e.name == "openai"
    assert e.model == "text-embedding-3-large"


def test_unknown_provider_raises(clean_env):
    with pytest.raises(ValueError):
        embeddings.resolve_embedder("no-such-backend")


def test_embed_query_applies_instruction():
    seen = []

    class Fake(embeddings.Embedder):
        name = "fake"
        query_instruction = "PREFIX "

        def embed(self, texts):
            seen.append(texts[0])
            return [[0.0]]

    Fake().embed_query("hello")
    assert seen == ["PREFIX hello"]


def test_embed_documents_applies_document_instruction():
    seen = []

    class Fake(embeddings.Embedder):
        name = "fake"
        document_instruction = "DOC "

        def embed(self, texts):
            seen.extend(texts)
            return [[0.0]] * len(texts)

    Fake().embed_documents(["a", "b"])
    assert seen == ["DOC a", "DOC b"]


def test_embed_documents_without_instruction_is_raw():
    seen = []

    class Fake(embeddings.Embedder):
        name = "fake"

        def embed(self, texts):
            seen.extend(texts)
            return [[0.0]] * len(texts)

    Fake().embed_documents(["a"])
    assert seen == ["a"]


def test_register_custom_embedder(clean_env):
    class Custom(embeddings.Embedder):
        name = "custom-vendor"

        def __init__(self, model=None, url=None, api_key=""):
            self.model = model or "custom-model"

        def embed(self, texts):
            return [[1.0]] * len(texts)

    embeddings.register_embedder("custom-vendor", Custom)
    e = embeddings.resolve_embedder("custom-vendor")
    assert e.name == "custom-vendor"
    assert e.fingerprint == "custom-vendor:custom-model"
    assert e.embed(["a", "b"]) == [[1.0], [1.0]]


def test_dotted_path_provider(tmp_path, clean_env, monkeypatch):
    mod = tmp_path / "myembed.py"
    mod.write_text(
        "from hkdata.embeddings import Embedder\n"
        "class Mine(Embedder):\n"
        "    name = 'mine'\n"
        "    query_instruction = ''\n"
        "    def __init__(self, model=None, url=None, api_key=''):\n"
        "        self.model = model or 'mine-model'\n"
        "    def embed(self, texts):\n"
        "        return [[2.0]] * len(texts)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    e = embeddings.resolve_embedder("myembed:Mine")
    assert e.name == "mine"
    assert e.fingerprint == "mine:mine-model"
    assert e.embed(["a", "b"]) == [[2.0], [2.0]]