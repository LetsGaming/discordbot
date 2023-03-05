
import discord
from discord import app_commands

from Commands.ModerationCommands import Moderation
from Commands.QuoteCommands import Quote
from Commands.RedditCommand import Reddit
from Commands.TicketCommands import TicketSystem
from Commands.WeatherCommand import Weather
from Commands.WebsiteCommand import WebsiteUtils
from Commands.ConvertCommands import Conversion

class Commands():
    def __init__(self, client: discord.Client):
        self.tree = app_commands.CommandTree(client=client) #Creates a new CommandTree to work with discods slash-commands
        self.moderationCommands = Moderation()
        self.redditCommand = Reddit()
        self.weatherCommand = Weather()
        self.quoteCommands = Quote(client=client)
        self.websiteCommand = WebsiteUtils()
        self.conversionCommand = Conversion()
        self.ticketSystem = TicketSystem(tree=self.tree, client=client)
        self.synced = False #Sets the synced bool to false
        
    async def register_commands(self):
        self.tree.command(name="reddit", description="Sends a random post from the given subreddit.")(self.redditCommand.reddit) #Adds a new Command to the tree with the name and a short description, also adds the def that gets called when the command is triggered
        self.tree.command(name="clear", description="Deletes the given amount of messages.")(self.moderationCommands.clear_messages)
        self.tree.command(name="weather", description="Gets information about the weather in the given city.")(self.weatherCommand.getWeather)
        self.tree.command(name="quote", description="Lets you save a quote from a user.")(self.quoteCommands.create_quote)
        self.tree.command(name="getquote", description="Returns a random saved quote from this server.")(self.quoteCommands.get_quote)
        self.tree.command(name="about", description="Tries to find the about us page of a given business and returns it's information")(self.websiteCommand.get_business_info)
        self.tree.command(name="conversion", description="Gets the conversion rate of Currency X to Currency Y")(self.conversionCommand.get_convertion_rate)
        self.tree.command(name="currencies", description="Returns a list of all the valid currency-codes")(self.conversionCommand.get_currencies)
        await self.ticketSystem.register_commands()

        if not self.synced: #Checks if the commands aren't already synced
            await self.tree.sync() #Syncs the commands with discords server
            self.synced = True #Sets the synced varaible to true