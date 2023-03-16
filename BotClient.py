from datetime import datetime
import json

import discord
import CommandHandler
from Commands.BirthdayCommands import BirthdayUtils
from Commands.BirthdayCommands import Birthday

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
        self.birthdayUtils = BirthdayUtils()
        await self.command_handler.register_commands()
    
    async def on_guild_join(self, guild):
        # Create channels
        ticket_category = await guild.create_category("Tickets")
        await ticket_category.create_text_channel("create-ticket")
        await ticket_category.create_text_channel("get-ticket")

        birthday_category = await guild.create_category("Birthdays")
        await birthday_category.create_text_channel("celebrate-birthday")
        add_birthday_channel = await birthday_category.create_text_channel("add-birthday")
        await add_birthday_channel.send("Add your birthday by sending it in this form: DD.MM.YYYY")
    
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name = "Member")
        await member.add_roles(role)

    async def on_message(self, message):
        if message.channel.name == "add-birthday":
            msg_content = message.content
            date_obj = datetime.strptime(msg_content, '%d.%m.%Y')
            birthday_date = date_obj.strftime('%Y-%m.%d')
            birthday = Birthday(guild=message.channel.guild, channel=message.channel, user=message.author, date=birthday_date)
            await self.birthdayUtils.add_birthday(birthday=birthday)

        
_client = BotClient()
_client.run(_client.token)