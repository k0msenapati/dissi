from agno.agent import Agent
from agno.models.groq import Groq
from agno.playground import Playground, serve_playground_app
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.mcp import MCPTools
from asyncio import run
from dotenv import load_dotenv
from mcp import StdioServerParameters
from nest_asyncio import apply
from os import getenv

# Allow nested event loops
apply()

# Load environment variables from .env file
load_dotenv()

agent_storage_file: str = "tmp/agents.db"

INSTRUCTIONS = """
You are DiscordOps, a high-performance assistant with access to Discord tools and DuckDuckGo search. On user request, read or send messages in Discord (ask for channel ID if not provided) and search the web when needed. Respond clearly, concisely, and follow community guidelines.
"""

MODEL = Groq(id="llama-3.3-70b-versatile")

STORAGE = SqliteAgentStorage(
    table_name="discord_agent",
    db_file=agent_storage_file,
    auto_upgrade_schema=True,
)


async def run_server() -> None:
    discord_token = getenv("DISCORD_TOKEN") or getenv("DISCORD_BOT_TOKEN")
    if not discord_token:
        raise ValueError("DISCORD_TOKEN environment variable is required")

    server_params = StdioServerParameters(
        command="node",
        args=["mcp-discord\\build\\index.js"],
        env={"DISCORD_TOKEN": discord_token},
    )

    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            name="Discord Agent",
            tools=[mcp_tools, DuckDuckGoTools()],
            instructions=INSTRUCTIONS,
            model=MODEL,
            storage=STORAGE,
            add_history_to_messages=True,
            num_history_responses=3,
            add_datetime_to_instructions=True,
            markdown=True,
        )

        playground = Playground(agents=[agent])
        app = playground.get_app()

        serve_playground_app(app)


if __name__ == "__main__":
    run(run_server())
