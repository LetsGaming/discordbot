import json
from threading import Timer
import mysql.connector

class BirthdayUtils:
    def __init__(self):
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
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

class Birthday:
    def __init__(self, guild, channel, user, date):
        self.guild = guild
        self.channel = channel
        self.user = user
        self.date = date