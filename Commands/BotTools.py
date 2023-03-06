import discord
import json
class Tools:
    def __init__(self, client: discord.Client):
        self.config = self.load_config()
        self.client = client
    
    async def relaod(self, interaction: discord.Interaction):
        await interaction.channel.send("Restarting...")
        self.client.close()
        self.client.run(self.token)
        
    def load_config(self):
        with open("Configs/config.json") as file:
            config = json.load(file)
            self.token = config["token"]