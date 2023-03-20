import asyncio
from datetime import datetime, time, timedelta
import json
import re
from threading import Timer
import discord
import mysql.connector

class BirthdayUtils:
    def __init__(self, client: discord.Client):
        self.client = client
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start() 
        
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.check_birthdays())

    def __restart_connection(self):
        self.connection.connect()
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start()
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)
        
    async def add_birthday(self, birthday):
        guild = birthday.guild
        channel = birthday.channel
        user = birthday.user
        date = birthday.date

        discord_id = f"<@{user.id}>"
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, date FROM birthdays WHERE discord_id = %s AND guild_id = %s", (discord_id, guild.id))
        result = cursor.fetchone()

        if result is not None:
            date = result[1]
            await channel.send(f"{discord_id} Your Birthday is already added! It's: {date.strftime('%d.%m.%Y')} !")
        else:
            cursor.execute("INSERT INTO birthdays (id, guild_id, discord_id, date) VALUES (null, %s, %s, %s)",
                         (guild.id, discord_id, date))
            self.connection.commit()
            await channel.send(f"{discord_id} Your birthday got added successfully!")
            await self.delete_command_messages(channel=channel, amount=2)

    async def get_birthday(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        cursor = self.connection.cursor()
        if username.startswith("<"):
            birthday_user = await self.get_user(user_id=username)
            cursor.execute("Select date from birthdays where discord_id = %s and guild_id = %s", (username, interaction.guild.id))
            result = cursor.fetchone()
            if result is not None:
                await interaction.followup.send(f"{interaction.user.mention} {birthday_user.name}'s birthday is: {result[0].strftime('%d.%m.%Y')} !")
            else:
                await interaction.followup.send(f"{interaction.user.mention} it seems like {birthday_user.name} hasn't added their birthday yet.")
        else:
            await interaction.channel.send("Invalid form please use @username !")
    
    async def check_birthdays(self):
        while True:
            # Get the current date and time
            now = datetime.now()

            # Check if it's 6 in the morning
            if now.hour == 6 and now.minute == 0:
                # Get today's date
                today = datetime.date.today()

                # Query the database for birthdays that match today's date
                cursor = self.connection.cursor()
                cursor.execute("SELECT discord_id, date, guild_id FROM birthdays WHERE DATE_FORMAT(date, '%m-%d') = %s", (today.strftime('%m-%d'),))
                results = cursor.fetchall()

                # Send a birthday message to each user whose birthday it is
                for result in results:
                    user = await self.get_user(result[0])
                    guild = await self.client.fetch_guild(result[3])
                    if user:
                        # Check if it's the user's birthday
                        birthday_date = result[1].date()
                        if birthday_date == today:
                            # Get the celebrate birthday channel for the user's guild
                            celebrate_channel = discord.utils.get(guild.text_channels, name='celebrate-birthday')
                            if celebrate_channel:
                                await celebrate_channel.send(f"Happy birthday, {user.mention}!")
            
            # Wait until the next day at 6 am to check again
            next_check = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
            sleep_seconds = (next_check - now).total_seconds()
            await asyncio.sleep(sleep_seconds)

    async def get_user(self, user_id):
        user_id = int(re.search(r'\d+', user_id).group())
        return await self.client.fetch_user(user_id)

    async def delete_command_messages(self, channel: discord.TextChannel, amount: int):
        await asyncio.sleep(2)
        await channel.purge(limit=amount, bulk=True)

class Birthday:
    def __init__(self, guild, channel, user, date):
        self.guild = guild
        self.channel = channel
        self.user = user
        self.date = date