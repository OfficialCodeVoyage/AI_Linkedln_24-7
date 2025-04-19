import yaml

def test_config_structure():
    cfg = yaml.safe_load(open("config/daily.yml"))
    assert "daily_caps" in cfg
    assert isinstance(cfg["daily_caps"], dict)
    assert all(key in cfg["daily_caps"] for key in ("invites", "likes", "comments"))
    assert "schedule_blocks" in cfg
    assert isinstance(cfg["schedule_blocks"], list)
    assert "delay_seconds" in cfg
    assert isinstance(cfg["delay_seconds"], dict) 