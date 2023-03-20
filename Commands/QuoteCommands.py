import json
import re
from datetime import date
from typing import Optional
from threading import Timer

import discord
import mysql.connector


class Quote:
    def __init__(self, client: discord.Client):
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.client = client
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start() 

        self.lastResult = None
        
    def __restart_connection(self):
        self.connection.connect()
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start()
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)

    async def create_quote(self, interaction: discord.Interaction, username: str, text: str):
        await interaction.response.defer()
        cursor = self.connection.cursor()
        
        user = None
        if username.startswith("<"):
            user = await self.get_user(user_id=username)
        else:
            await interaction.channel.send("Invalid form please use @username !")
            
        quote_date = date.today().isoformat()
        avatar = user.avatar.url if user else "none"
        name = user.name if user else username
        val = (interaction.guild.id, quote_date, name, avatar, text)
        
        sql = "INSERT INTO quote (quote_id, guild_id, quote_date, username, user_avatar, quote_text) VALUES (null, %s, %s, %s, %s, %s)"
        cursor.execute(operation=sql, params=val)
        self.connection.commit()

        await interaction.followup.send(f"Quote from {username} is now saved in the database.")

    async def get_quote(self, interaction: discord.Interaction, embed: Optional[bool]=True):
        await interaction.response.defer()
        cursor = self.connection.cursor()
        sql = "SELECT quote_date, username, user_avatar, quote_text FROM quote WHERE guild_id = %s ORDER BY RAND() LIMIT 1"
        cursor.execute(operation=sql, params=(interaction.guild.id,))
        result = cursor.fetchone()
        if not result:
            return await interaction.followup.send("No quotes found for this guild.")
        
        if result != self.lastResult:
            date, username, avatar, text = result
            self.lastResult = result
        else:
            self.get_quote(embed=embed)

        if embed:
            await interaction.followup.send("Grabbing random quote...")
            await interaction.channel.send(embed=self.build_quote_embed(date=date, username=username, avatar=avatar, text=text))
        else:
            await interaction.followup.send(f"{date} - {username}: {text}")

    async def get_user(self, user_id):
        user_id = int(re.search(r'\d+', user_id).group())
        return await self.client.fetch_user(user_id)

    def build_quote_embed(self, date, username, avatar, text):
        embed = discord.Embed(
            title=f"Quote from {username}",
            description=text,
        )
        embed.set_footer(text=date)
        if avatar != "none":
            embed.set_thumbnail(url=avatar)
        return embed
