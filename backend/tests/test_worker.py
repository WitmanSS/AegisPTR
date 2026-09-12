import json
import time

import pytest


from types import SimpleNamespace


def make_fake_finding():
    f = SimpleNamespace()
    f.id = "f-123"
    f.severity = "HIGH"
    f.confidence = 10
    f.risk_score = 0
    f.remediation = None
    return f


class FakeQuery:
    def __init__(self, obj):
        self._obj = obj

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._obj


class FakeDB:
    def __init__(self, obj):
        self._obj = obj
        self.committed = False

    def query(self, model):
        return FakeQuery(self._obj)

    def add(self, obj):
        # emulate SQLAlchemy attaching
        pass

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        return obj


class FakePubSub:
    def __init__(self, messages):
        self.messages = messages

    def subscribe(self, channel):
        self.channel = channel

    def listen(self):
        for m in self.messages:
            yield m


class FakeRedis:
    def __init__(self, pubsub_obj):
        self._pubsub = pubsub_obj
        self.published = []

    def pubsub(self, ignore_subscribe_messages=True):
        return self._pubsub

    def publish(self, channel, payload):
        self.published.append((channel, payload))


def test_enrich_finding_updates_fields(monkeypatch):
    # test enrich_finding directly
    from backend.workers.finding_worker import enrich_finding

    fake = make_fake_finding()
    db = FakeDB(fake)

    res = enrich_finding(db, fake.id)

    assert res.get("id") == fake.id
    assert res.get("risk_score") > 0
    assert db.committed is True


def test_worker_loop_one_message(monkeypatch):
    # Prepare fake redis pubsub message
    msg_payload = {"type": "finding.created", "data": "f-123"}
    msg = {"data": json.dumps(msg_payload)}

    pubsub = FakePubSub([msg])
    fake_redis = FakeRedis(pubsub)

    # monkeypatch Publisher._ensure_redis to return our fake redis
    from app.events import publisher as pubmod

    monkeypatch.setattr(pubmod.Publisher, "_ensure_redis", lambda self: fake_redis)

    # monkeypatch get_db_session used in worker
    fake_finding = make_fake_finding()
    db = FakeDB(fake_finding)
    import backend.workers.finding_worker as worker_mod

    monkeypatch.setattr(worker_mod, "get_db_session", lambda: db)

    # run worker (it will iterate over our single message then exit)
    worker_mod.run_worker()

    # after run, fake_redis should have one published finding.enriched
    published = fake_redis.published
    assert any(ch == "finding.enriched" for ch, _ in published)
