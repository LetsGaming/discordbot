import discord
import json
class Tools:
    def __init__(self, client: discord.Client):
        self.config = self.load_config()
        self.client = client
    
    async def restart(self, interaction: discord.Interaction):
        if interaction.user.id == 272402865874534400:
            await interaction.channel.send("Restarting...")
            self.client.close()
            self.client.run(self.token)
        else:
            await interaction.channel.send("You do not have the Bot-Permission for this Command!")
        
    def load_config(self):
        with open("Configs/config.json") as file:
            config = json.load(file)
            self.token = config["token"]