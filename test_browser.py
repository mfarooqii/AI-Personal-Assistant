#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/home/farooqi/Documents/Repo/AI-Personal-Assistant/backend')

from app.browser.engine import BrowserEngine
from app.browser.agent import BrowserAgent

async def test():
    engine = BrowserEngine()
    agent = BrowserAgent(engine)
    
    print("🔷 Launching browser...")
    await engine.launch()
    
    print("🔷 Planning task...")
    plan = await agent.plan_task("Go to gmail.com login page")
    print(f"Plan: {plan}")
    
    print("🔷 Executing task...")
    event_count = 0
    async for event in agent.execute("Go to gmail.com login page", plan):
        event_count += 1
        print(f"  [{event.type}] {event.message}")
        if event.url:
            print(f"  URL: {event.url}")
        if event_count > 20:
            print("  (stopping after 20 events)")
            break
    
    print("✅ Done")
    await engine.close()

asyncio.run(test())
