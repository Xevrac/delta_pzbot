import asyncio
import os
import subprocess
import discord
from discord import app_commands

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PZ_SCRIPT = os.path.join(BASE_DIR, "pz.py")
PZ_HOST = os.environ["PZ_HOST"]
PZ_PORT = os.environ["RCON_PORT"]
PZ_RCON_PASSWORD = os.environ["RCON_PASSWORD"]

RESTART_SCRIPT = os.path.join(BASE_DIR, "pzrestart.sh")

GUILD_ID = int(os.environ["GUILD_ID"])

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


COMMANDS = [
    {
        "name": "players",
        "description": "Show current Project Zomboid players",
        "type": "pz",
        "command": "players",
    },
    {
        "name": "restart",
        "description": "Restart the Project Zomboid server",
        "type": "script",
        "command": RESTART_SCRIPT,
    },
    {
        "name": "servermsg",
        "description": "Send a message to the Project Zomboid server",
        "type": "servermsg",
    },
]


def run_pz_command(pz_command: str) -> str:
    try:
        result = subprocess.run(
            [
                "python3",
                PZ_SCRIPT,
                PZ_HOST,
                PZ_PORT,
                PZ_RCON_PASSWORD,
                pz_command,
            ],
            capture_output=True,
            text=True,
            timeout=150,
        )
    except subprocess.TimeoutExpired:
        return "RCON command timed out."
    except Exception as exc:
        return f"Failed to run RCON command: {exc}"

    return format_result(result)


def run_script(script_path: str) -> str:
    try:
        result = subprocess.run(
            [
                "bash",
                script_path,
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        return "Restart script timed out."
    except Exception as exc:
        return f"Failed to run restart script: {exc}"

    return format_result(result)


def format_result(result: subprocess.CompletedProcess) -> str:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        return stderr or stdout or f"Command failed with exit code {result.returncode}"

    return stdout or "Command completed successfully."


def make_command_callback(command_config):
    async def callback(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        if command_config["type"] == "pz":
            output = await asyncio.to_thread(
                run_pz_command,
                command_config["command"],
            )
        elif command_config["type"] == "script":
            output = await asyncio.to_thread(
                run_script,
                command_config["command"],
            )
        else:
            output = f"Unknown command type: {command_config['type']}"

        await interaction.followup.send(f"```{output[:1900]}```")

    return callback


def make_servermsg_callback(command_config):
    async def callback(interaction: discord.Interaction, message: str):
        await interaction.response.defer(thinking=True)

        cleaned_message = message.strip().replace("\n", " ").replace("\r", " ")

        if not cleaned_message:
            await interaction.followup.send("Message cannot be empty.")
            return

        pz_command = f'servermsg "{cleaned_message}"'

        output = await asyncio.to_thread(
            run_pz_command,
            pz_command,
        )

        if output == "Message sent." or output == "Command completed successfully.":
            output = cleaned_message

        await interaction.followup.send(f"```{output[:1900]}```")

    return callback


for command_config in COMMANDS:
    if command_config["type"] == "servermsg":
        callback = make_servermsg_callback(command_config)
    else:
        callback = make_command_callback(command_config)

    tree.add_command(
        app_commands.Command(
            name=command_config["name"],
            description=command_config["description"],
            callback=callback,
        ),
        guild=discord.Object(id=GUILD_ID),
    )


@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)

    print(f"Logged in as {client.user}")
    print("Slash commands synced.")


client.run(DISCORD_TOKEN)