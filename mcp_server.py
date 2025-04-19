import os
import json
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from playwright.async_api import async_playwright

# Load LinkedIn credentials from .env
load_dotenv()
USERNAME = os.getenv("LINKEDIN_USERNAME")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
# Allow overriding headless mode for debugging
HEADLESS_MODE = os.getenv("HEADLESS", "true").lower() == "true"

# Initialize the FastMCP server instance
mcp = FastMCP()

@mcp.tool()
async def login_linkedin(ctx: Context, username: str, password: str) -> dict:
    """Log in to LinkedIn using Playwright and return storage state."""
    async with async_playwright() as pw:
        ctx.info(f"Launching browser (headless={HEADLESS_MODE})...")
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        ctx.info("Logging in to LinkedIn...")
        page = await browser.new_page()
        ctx.info("Navigating to login page...")
        await page.goto("https://www.linkedin.com/login")
        ctx.info("Filling credentials...")
        await page.fill("input#username", username)
        await page.fill("input#password", password)
        ctx.info("Submitting login form...")
        await page.click("button[type=submit]")
        # Navigate to feed to confirm login succeeded
        ctx.info("Redirecting to feed for login verification...")
        await page.goto("https://www.linkedin.com/feed/")
        ctx.info("Waiting for feed posts to load...")
        try:
            await page.wait_for_selector("div.feed-shared-update-v2", timeout=30000)
            ctx.info("Feed posts found. Login confirmed.")
        except Exception:
            ctx.info("Feed posts did not load in time; assuming login succeeded.")
        state = await browser.contexts[0].storage_state()
        await browser.close()
    return {"storage_state": state}

@mcp.tool()
async def browse_linkedin_feed(ctx: Context, count: int, storage_state: dict) -> list[dict]:
    """Browse the LinkedIn feed and return the specified number of posts."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        ctx.info("Browsing LinkedIn feed...")
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/feed/")
        await page.wait_for_selector("div.feed-shared-update-v2")
        locator = page.locator("div.feed-shared-update-v2")
        posts = []
        for i in range(count):
            element = locator.nth(i)
            await element.wait_for()
            text = await element.inner_text()
            posts.append({"index": i, "text": text.strip()})
        await browser.close()
    return posts

@mcp.tool()
async def view_linkedin_profile(ctx: Context, profile_url: str, storage_state: dict) -> dict:
    """View a LinkedIn profile and return name and headline."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        await page.goto(profile_url)
        await page.wait_for_selector("h1", timeout=30000)
        data = await page.evaluate('''() => {
            const nameEl = document.querySelector('h1');
            const headlineEl = document.querySelector('.text-body-medium');
            return {
                name: nameEl ? nameEl.innerText.trim() : '',
                headline: headlineEl ? headlineEl.innerText.trim() : ''
            };
        }''')
        await browser.close()
    return data

@mcp.tool()
async def send_linkedin_invite(ctx: Context, profile_url: str, storage_state: dict) -> dict:
    """Send a connection invite to a LinkedIn profile."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        await page.goto(profile_url)
        ctx.info(f"Visiting {profile_url} to send invite...")
        # Click the Connect button if available
        btn = page.locator("button:has-text('Connect')").first
        if await btn.count() > 0:
            await btn.click()
            # Confirm send invite in the dialog
            await page.locator("button:has-text('Send now')").click()
            ctx.info("Invite sent.")
        else:
            ctx.info("Connect button not found.")
        await browser.close()
    return {"success": True}

@mcp.tool()
async def like_linkedin_post(ctx: Context, post_url: str, storage_state: dict) -> dict:
    """Like a specific LinkedIn post by URL."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        await page.goto(post_url)
        ctx.info(f"Visiting post {post_url} to like...")
        like_btn = page.locator("button[aria-label*='Like']").first
        if await like_btn.count() > 0:
            await like_btn.click()
            ctx.info("Post liked.")
        else:
            ctx.info("Like button not found.")
        await browser.close()
    return {"success": True}

@mcp.tool()
async def comment_linkedin_post(ctx: Context, post_url: str, comment: str, storage_state: dict) -> dict:
    """Post a comment on a LinkedIn post."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS_MODE)
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        await page.goto(post_url)
        ctx.info(f"Visiting post {post_url} to comment...")
        # Click the Comment button
        comment_btn = page.locator("button:has-text('Comment')").first
        if await comment_btn.count() > 0:
            await comment_btn.click()
            textarea = page.locator("textarea[aria-label='Add a comment']").first
            await textarea.fill(comment)
            await page.locator("button:has-text('Post')").click()
            ctx.info("Comment posted.")
        else:
            ctx.info("Comment button not found.")
        await browser.close()
    return {"success": True}

# Expose the FastMCP server instance
data = mcp 