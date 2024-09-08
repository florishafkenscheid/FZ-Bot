import discord
import asyncio

from discord import app_commands
from fz_api import FZClient
from fz_api import ServerStatus
from main import Main

class Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    fz_client = None

    def __init__(self, main: Main):
        self.main = main
        self.client = Bot.client
        self.client.event(self.on_ready)

    # Connect to factorio zone API
    async def fz_connect(self):
        self.fz_client = FZClient()
        asyncio.get_event_loop_policy().get_event_loop().create_task(self.fz_client.connect())
        await self.fz_client.wait_sync()

    async def on_ready(self):
        await self.fz_connect()
        await self.tree.sync()

    def register_commands(self):
        @self.tree.command(
            name="start",
            description="Start the Factorio server instance"
        )
        async def start(interaction: discord.Interaction):
            STATUS = await self.fz_client.get_instance_status()
            if STATUS == ServerStatus.RUNNING or STATUS == ServerStatus.STARTING:
                await interaction.response.send_message("The server is already running.")
            else:
                await interaction.response.send_message("This could take a while, please hold.")
                await self.fz_client.start_instance()
                await asyncio.sleep(15)
                await interaction.edit_original_response(content=f"Successfully started instance on IP: {self.fz_client.server_address}")


        @self.tree.command(
            name="status",
            description="Get the status of the Factorio server instance"
        )
        async def status(interaction: discord.Interaction):
            STATUS = await self.fz_client.get_instance_status()
            if STATUS == ServerStatus.RUNNING:
                await interaction.response.send_message(f"Current status: {STATUS} on IP: {self.fz_client.server_address}")
            else:
                await interaction.response.send_message(f"Current status: {STATUS}")

        @self.tree.command(
            name="stop",
            description="Stop the Factorio server instance"
        )
        async def stop(interaction: discord.Interaction):
            STATUS = await self.fz_client.get_instance_status()
            if STATUS == ServerStatus.RUNNING:
                await interaction.response.send_message("Stopping instance, please hold")
                await self.fz_client.stop_instance()
                await interaction.edit_original_response(content="Successfully stopped instance!")
            else:
                await interaction.response.send_message("The server is already stopped.")

    def run(self, token):
        self.register_commands()
        self.client.run(token)