import argparse
import json

from hkdata import cli


class _FakeEmbedder:
    query_instruction = ""

    def embed(self, texts):
        return [[0.0] for _ in texts]


def test_info_returns_array_for_single_id(monkeypatch, capsys):
    monkeypatch.setattr(cli, "info_multiple",
                        lambda ids: [{"data": {"name": ids[0]}, "error": None}])
    rc = cli.cmd_info(argparse.Namespace(dataset_ids=["hk-x"]))
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert isinstance(payload, list)
    assert payload[0]["name"] == "hk-x"


def test_info_all_errors_exit_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(cli, "info_multiple",
                        lambda ids: [{"data": None, "error": "boom"} for _ in ids])
    rc = cli.cmd_info(argparse.Namespace(dataset_ids=["a", "b"]))
    captured = capsys.readouterr()
    assert rc == 1
    assert "boom" in captured.err


def test_programs_search_no_hits(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_require_chromadb", lambda: True)
    monkeypatch.setattr(cli, "_resolve_embedder", lambda a: _FakeEmbedder())
    monkeypatch.setattr(cli, "_warn_store_mismatch", lambda *a, **k: None)
    monkeypatch.setattr(cli.programs, "search", lambda *a, **k: [])
    rc = cli.cmd_programs_search(argparse.Namespace(
        keywords=["nothing"], top_n=5, json=False, source=False))
    assert rc == 0
    assert "No program matches" in capsys.readouterr().out


def test_programs_search_json_hit(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_require_chromadb", lambda: True)
    monkeypatch.setattr(cli, "_resolve_embedder", lambda a: _FakeEmbedder())
    monkeypatch.setattr(cli, "_warn_store_mismatch", lambda *a, **k: None)
    hit = {"score": 0.9, "id": "lcsd.facility:fitness_rooms",
           "signature": "fitness_rooms() -> list", "datasets": ["hk-x"],
           "department": "LCSD", "source": "def fitness_rooms(): ..."}
    monkeypatch.setattr(cli.programs, "search", lambda *a, **k: [hit])
    rc = cli.cmd_programs_search(argparse.Namespace(
        keywords=["gym"], top_n=5, json=True, source=False))
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload[0]["id"] == "lcsd.facility:fitness_rooms"
