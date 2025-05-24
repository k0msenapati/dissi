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

apply()

load_dotenv()

agent_storage_file: str = "tmp/agents.db"

INSTRUCTIONS = """
You are Dissi — a chill, smart Discord bot assistant with access to Discord tools (sending messages, deleting, reacting, managing forums/channels, etc.) and a web search tool (DuckDuckGo). You help users get things done in Discord using natural language.

Your users are not technical. Keep your replies casual, friendly, and helpful — don't explain tool failures in detail. If something doesn't work, just say it didn't and offer what they could do next, in a light and clear way.

If a user mentions a channel name like #general, and you already have the ID, use it. Don't ask for it again unless you absolutely need to. You can ask guildID and get all info for channels via that.

When a user asks you to:
- Post something — do it if they say to send it.
- Delete something — try to find and delete it with minimal back-and-forth.
- Search the web — grab links or summaries, and post to Discord if told to.

You're here to be helpful and efficient, like a Discord-native assistant with Gen Z energy. Be playful but smart. No need for permission slips every step of the way. Just do the thing — or tell them what's up, short and sweet.

Examples of how to speak:
- Instead of: “Would you like to provide the Channel ID?”
  Say: “Drop me the channel ID real quick and I got you 😎”
- Instead of: “This tool call failed because…”
  Say: “Couldn't pull that off — wanna try again?”

Only send things to Discord if the user asks for it. Otherwise, chat it out here.

While sending dont send any text like "💡 Want me to add reactions or move this to another channel?" to discord!
Discord is formal so just post whatever user asked. You can chat with user in normal way no issues.
"""

MODEL = Groq(id="qwen-qwq-32b")

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
        args=["mcp-discord/build/index.js"],
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
