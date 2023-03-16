import asyncio
from datetime import datetime
import json
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
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.check_birthdays())

    def __restart_connection(self):
        if not self.connection.is_connected:
            self.connection.connect()
        self.ping_timer = Timer(1000, self.__restart_connection) 
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
        cursor.execute("SELECT id, date FROM birthdays WHERE discord_id = %s", (discord_id,))
        result = cursor.fetchone()

        if result is not None:
            date = result[1]
            await channel.send(f"{discord_id} Your Birthday is already added! It's: {date} !")
        else:
            cursor.execute("INSERT INTO birthdays (id, guild_id, discord_id, date) VALUES (null, %s, %s, %s)",
                         (guild.id, discord_id, date))
            self.connection.commit()
            await channel.send(f"{discord_id} Your birthday got added successfully!")

    async def get_birthday(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        cursor = self.connection.cursor()
        if username.startswith("<"):
            cursor.execute("Select date from birthdays where discord_id = %s", (username,))
            result = cursor.fetchone()
            if result is not None:
                await interaction.followup.send(f"{interaction.user.mention} their birthday is: {result[0]} !")
            else:
                await interaction.followup.send(f"{interaction.user.mention} it seems like they haven't added their birthday yet.")
        else:
            await interaction.channel.send("Invalid form please use @username !")
    
    async def check_birthdays(self):
        while True:
            # Get today's date
            today = datetime.today().strftime('%m-%d')
            
            # Query the database for birthdays that match today's date
            cursor = self.connection.cursor()
            cursor.execute("SELECT discord_id FROM birthdays WHERE DATE_FORMAT(date, '%m-%d') = %s", (today,))
            results = cursor.fetchall()
            
            # Send a birthday message to each user whose birthday it is
            for result in results:
                user = await self.client.fetch_user(result[0])
            if user:
                # Get the celebrate birthday channel for the user's guild
                guild = user.guild
                celebrate_channel = discord.utils.get(guild.text_channels, name='celebrate-birthday')
                if celebrate_channel:
                    await celebrate_channel.send(f"Happy birthday, {user.mention}!")

            # Wait until tomorrow to check again
            await asyncio.sleep(86400)
            
class Birthday:
    def __init__(self, guild, channel, user, date):
        self.guild = guild
        self.channel = channel
        self.user = user
        self.date = date