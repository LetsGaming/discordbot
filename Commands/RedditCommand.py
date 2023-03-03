import discord
from discord import app_commands
from memelib.api import DankMemeClient


class Reddit:
    def __init__(self):
        self.memeClient = DankMemeClient() #Creates a new Memeclient to get random posts out of a subreddit

    async def reddit(self, interaction: discord.Interaction, subreddit: str):
        await interaction.response.defer()
        try:
            await interaction.followup.send(f"Searching for a Reddit-post in [r/{subreddit}]...")
            postDict = await self.memeClient.async_meme(subreddit=subreddit)
            selftext = postDict['selftext']
            if "comment" in postDict["post_url"] and selftext != "":
                await interaction.channel.send(embed=self.buildCommentEmbed(dictionary=postDict))
            elif (postDict["img_url"].endswith(".jpg") or postDict["img_url"].endswith(".png") or postDict["img_url"].endswith(".gif")):
                await interaction.channel.send(embed=self.buildContentEmbed(postDict))
            else:
                await interaction.channel.send(postDict["post_url"])

        except Exception as ex:
            print(ex)
            await interaction.channel.send(ex)

    def buildCommentEmbed(self, dictionary: dict):
        embed = discord.Embed(
                title=dictionary["title"],
                url=dictionary["post_url"],
                description=f"{dictionary['author']} \n\n {dictionary['selftext']}",
            )
        embed.set_footer(text=f"{dictionary['upvotes']} 👍 | {dictionary['comments']} 💬")
        return embed
    
    def buildContentEmbed(self, dictionary: dict):
        embed = discord.Embed(
            title=dictionary["title"],
            url=dictionary["post_url"],
            description=f"{dictionary['author']} \nCan't see the image? [Click Here.]({dictionary['img_url']})",
        )
        embed.set_image(url=dictionary["img_url"])
        embed.set_footer(text=f"{dictionary['upvotes']} 👍 | {dictionary['comments']} 💬")
        return embed