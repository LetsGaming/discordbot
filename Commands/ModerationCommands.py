import asyncio

import discord


class Moderation:

    async def clear_messages(self, interaction: discord.Interaction, amount: int):
        interaction.response.defer()
        try:
            await interaction.followup.send(f"Deleting {amount} messages.")
            await asyncio.sleep(1) 
            deleted = await interaction.channel.purge(limit=amount+1, bulk=True)
            print(f"Deleted {len(deleted)} messages.")
        except discord.Forbidden as ex:
            await interaction.channel.send(ex)
