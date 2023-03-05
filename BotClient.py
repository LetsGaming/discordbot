import json

import discord
import CommandHandler


class BotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.command_handler = None
        self.config = self.load_config()
        
    def load_config(self):
        with open("Configs/config.json") as file:
            config = json.load(file)
            self.token = config["token"]

    async def on_ready(self):
        self.command_handler = CommandHandler.Commands(self)
        await self.command_handler.register_commands()
    
    async def on_guild_join(self, guild):
        # Create channels
        category = await guild.create_category("Tickets")
        await category.create_text_channel("create-ticket")
        await category.create_text_channel("get-ticket")
    
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name = "Member")
        await member.add_roles(role)
        
_client = BotClient()
_client.run(_client.token)