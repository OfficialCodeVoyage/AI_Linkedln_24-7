import os
import pytest
import openai
from commenter import moderate, generate_comment

# Test moderate function

def test_moderate_pass(monkeypatch):
    # Mock moderation to not flag
    monkeypatch.setenv("MODERATION", "on")
    def fake_moderation(input):
        return {"results": [{"flagged": False}]}
    monkeypatch.setattr(openai.Moderation, "create", fake_moderation)
    assert moderate("some safe content") is True


def test_moderate_fail(monkeypatch):
    # Mock moderation to flag
    monkeypatch.setenv("MODERATION", "on")
    def fake_moderation(input):
        return {"results": [{"flagged": True}]}
    monkeypatch.setattr(openai.Moderation, "create", fake_moderation)
    assert moderate("some bad content") is False

# Test generate_comment function

def test_generate_comment_success(monkeypatch):
    post_text = "This is a sample LinkedIn post."
    # Mock moderation on input
    def fake_mod(input):
        return {"results": [{"flagged": False}]}
    monkeypatch.setattr(openai.Moderation, "create", fake_mod)
    # Mock chat completion
    class FakeMsg:
        def __init__(self, content):
            self.message = type("m", (), {"content": content})
    def fake_chat_completion(model, messages, temperature, max_tokens):
        return type("r", (), {"choices": [FakeMsg("Great post!")]})
    monkeypatch.setattr(openai.ChatCompletion, "create", fake_chat_completion)
    # Should not error and return mocked comment
    comment = generate_comment(post_text)
    assert comment == "Great post!"


def test_generate_comment_flagged_input(monkeypatch):
    post_text = "flagged content"
    # Mock input moderation to fail
    def fake_mod(input):
        return {"results": [{"flagged": True}]}
    monkeypatch.setenv("MODERATION", "on")
    monkeypatch.setattr(openai.Moderation, "create", fake_mod)
    with pytest.raises(ValueError):
        generate_comment(post_text) 