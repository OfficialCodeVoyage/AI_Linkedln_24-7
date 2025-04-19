import os
import json
import asyncio
import random
import datetime
import sqlite3
from dotenv import load_dotenv
import yaml
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from commenter import generate_comment

# Load environment
load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
FAST_TEST = os.getenv("FAST_TEST", "false").lower() == "true"
MOCK_LINKEDIN = os.getenv("MOCK_LINKEDIN", "false").lower() == "true"
CONFIG_PATH = os.getenv("ACTIVITY_CONFIG", "config/daily.yml")
DB_URL = os.getenv("DB_URL", "sqlite:///state.db").split("sqlite:///")[-1]

def setup_db(db_path):
    """Initializes SQLite DB and returns connection."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, date TEXT, type TEXT, success INTEGER)")
    conn.commit()
    return conn

# Load config
with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)
schedule_blocks = cfg["schedule_blocks"]
delay_min = cfg["delay_seconds"]["min"]
delay_max = cfg["delay_seconds"]["max"]
# Store daily_caps globally *after* loading
global_daily_caps = cfg["daily_caps"]

# Parse time blocks
blocks = []
for b in schedule_blocks:
    h1, m1 = map(int, b["start"].split(':'))
    h2, m2 = map(int, b["end"].split(':'))
    blocks.append((datetime.time(h1, m1), datetime.time(h2, m2)))

# Helpers

def within_active_block():
    now = datetime.datetime.now().time()
    return any(start <= now <= end for start, end in blocks)


def count_actions(conn: sqlite3.Connection, action_type: str) -> int:
    """Counts actions of a specific type for today."""
    today = datetime.date.today().isoformat()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM actions WHERE date=? AND type=?", (today, action_type))
    return cursor.fetchone()[0]


def caps_remaining(
    conn: sqlite3.Connection, action_type: str, caps: dict | None = None, fast_test_mode: bool | None = None
) -> bool:
    """Checks if the daily cap for an action type has capacity.
       Uses global_daily_caps by default, or provided caps dict.
       Respects FAST_TEST env var unless fast_test_mode is explicitly provided.
    """
    if fast_test_mode if fast_test_mode is not None else FAST_TEST:
        return True
    # Use provided caps if available, otherwise global
    active_caps = caps if caps is not None else global_daily_caps
    current_count = count_actions(conn, action_type)
    return current_count < active_caps.get(action_type, 0)


def log_action(conn: sqlite3.Connection, action_type: str, success: bool):
    """Logs an action to the database."""
    today = datetime.date.today().isoformat()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO actions(date, type, success) VALUES(?,?,?)", (today, action_type, 1 if success else 0))
    conn.commit()

# Task stubs
async def handle_invite(client, storage_state):
    if MOCK_LINKEDIN:
        print("MOCK: invite sent")
        return True
    try:
        # TODO: implement real invite via mcp tool
        await client.call_tool("view_linkedin_profile", {"profile_url": f"https://www.linkedin.com/in/{USERNAME.split('@')[0]}/", "storage_state": storage_state})
        print("Invited connection")
        return True
    except Exception as e:
        print("Invite error", e)
        return False

async def handle_like(client, storage_state):
    if MOCK_LINKEDIN:
        print("MOCK: post liked")
        return True
    try:
        # TODO: implement real like via mcp tool
        await client.call_tool("browse_linkedin_feed", {"count": 1, "storage_state": storage_state})
        print("Liked a post")
        return True
    except Exception as e:
        print("Like error", e)
        return False

async def handle_comment(client, storage_state):
    if MOCK_LINKEDIN:
        print("MOCK: comment posted")
        return True
    try:
        # Fetch a single post to comment on
        feed_res = await client.call_tool("browse_linkedin_feed", {"count": 1, "storage_state": storage_state})
        feed = json.loads(feed_res[0].text)
        post_text = feed[0]["text"] if feed else ''
        # Generate a comment
        comment = generate_comment(post_text)
        # Post the comment via MCP tool
        # Here we assume the post URL matches user's feed URL
        post_url = f"https://www.linkedin.com/feed/"
        await client.call_tool("comment_linkedin_post", {"post_url": post_url, "comment": comment, "storage_state": storage_state})
        print(f"Commented: {comment}")
        return True
    except Exception as e:
        print("Comment error", e)
        return False

async def main():
    # Setup MCP client
    cmd = ["fastmcp", "run", "mcp_server.py"]
    program, *args = cmd
    transport = StdioTransport(command=program, args=args)
    async with Client(transport) as client:
        # Perform login and show all MCP server logs
        login_res = await client.call_tool("login_linkedin", {"username": USERNAME, "password": PASSWORD})
        print("=== LOGIN TOOL LOGS ===")
        for event in login_res:
            print(event.text)
        # Extract storage state from the last message
        login_json = json.loads(login_res[-1].text)
        storage = login_json.get("storage_state")
        print(f"Logged in successfully at {datetime.datetime.now().isoformat()}")

        db_conn = setup_db(DB_URL)
        # Debug: print schedule blocks and daily caps
        print(f"Schedule blocks: {schedule_blocks}")
        print(f"Daily caps: {global_daily_caps}")

        # Scheduler loop
        while True:
            # No schedule: run tasks immediately
            candidates = []  # Check caps using global config & env FAST_TEST
            if caps_remaining(db_conn, "invites"): candidates.append(handle_invite)
            if caps_remaining(db_conn, "likes"): candidates.append(handle_like)
            if caps_remaining(db_conn, "comments"): candidates.append(handle_comment)
            if candidates:
                task = random.choice(candidates)
                action_type = task.__name__.replace('handle_','')
                # Debug: fixed 1-second delay for task execution
                delay = 1
                print(f"[{datetime.datetime.now().isoformat()}] Selected task: {action_type}, will run in {delay}s")
                await asyncio.sleep(delay)
                print(f"[{datetime.datetime.now().isoformat()}] Running task: {action_type}")
                try:
                    success = await task(client, storage)
                    print(f"[{datetime.datetime.now().isoformat()}] Finished task: {action_type}, success={success}")
                except Exception as e:
                    success = False
                    print(f"[{datetime.datetime.now().isoformat()}] Error running task {action_type}:", e)
                log_action(db_conn, action_type, success)
                continue
            # Delay between loop iterations
            await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main()) 