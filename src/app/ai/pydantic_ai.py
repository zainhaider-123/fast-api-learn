import asyncio
from pydantic_ai import Agent
from .prompt.system import system_prompt

agent = Agent(  
  'anthropic:claude-sonnet-4-6',
  system_prompt=system_prompt
)

async def main(prompt: str):
    async with agent.run_stream_events(prompt) as events:
        async for event in events:
            print(event)
