import os
import json
import asyncio
from fastmcp import Client
from dotenv import load_dotenv
from fastmcp.client.transports import StdioTransport

# Load LinkedIn credentials from .env
load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")

async def main():
    # Launch the tool server subprocess via stdio
    cmd = ["fastmcp", "run", "linkedin_tools.py"]
    program, *args = cmd
    transport = StdioTransport(command=program, args=args)
    async with Client(transport) as client:
        # 1) Log in to LinkedIn
        print("Logging into LinkedIn...")
        login_res = await client.call_tool("login_linkedin", {
            "username": USERNAME,
            "password": PASSWORD
        })
        # Parse JSON from TextContent to access the returned dict
        login_json = json.loads(login_res[0].text)
        storage = login_json["storage_state"]
        print("Login successful. Storage state saved.")

        # 2) Browse your LinkedIn feed
        print("\nBrowsing feed...")
        feed_res = await client.call_tool("browse_linkedin_feed", {
            "count": 2,
            "storage_state": storage
        })
        # Parse feed JSON
        feed = json.loads(feed_res[0].text)
        print(json.dumps(feed, indent=2))

        # 3) View your LinkedIn profile
        print("\nViewing profile...")
        profile_res = await client.call_tool("view_linkedin_profile", {
            "profile_url": f"https://www.linkedin.com/in/{USERNAME.split('@')[0]}/",
            "storage_state": storage
        })
        # Parse profile JSON
        profile = json.loads(profile_res[0].text)
        print(json.dumps(profile, indent=2))

if __name__ == "__main__":
    asyncio.run(main())