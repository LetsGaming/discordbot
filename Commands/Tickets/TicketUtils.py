import asyncio
import json
import re
import discord
from discord import app_commands

import mysql.connector
class TicketUtils:
    def __init__(self, client: discord.Client):
        self.client = client
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM members")
        self.member_cache = cursor.fetchall()
        cursor.close()
        self.connection.close()

    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)
        
    async def send_tickets_embeds(self, channel: discord.TextChannel, interaction_user, tickets_dict: dict):
            check = '✅'
            if len(tickets_dict) < 1:
                await channel.send("There aren't any (open) Tickets!")
            else:
                for ticket_index in tickets_dict:
                    ticket = tickets_dict[ticket_index]
                    embed = discord.Embed(title=ticket["ticket_title"], description=ticket["ticket_description"])
                    embed.set_author(name=f"From: {ticket['ticket_author']}\nFor: {ticket['ticket_for']}\nAssigned-to: {ticket['assigned_to_member']}")
                    embed.set_thumbnail(url=ticket["author_icon"])
                    embed.add_field(name="ID", value=ticket["ticket_id"])
                    if ticket["ticket_creation_date"]:
                        creation_date = ticket["ticket_creation_date"].strftime('%d.%m.%Y')
                    else:
                        creation_date = "Null"
                    embed.add_field(name="Creation-Date", value=creation_date)
                    embed.add_field(name="Deadline", value=ticket["ticket_deadline"].strftime('%d.%m.%Y'))
                    if ticket["ticket_resolved"]:
                        resolved = check
                        footer_text = f"Resolved: {resolved} \nResolved on date: {ticket['ticket_resolved_date'].strftime('%d.%m.%Y')}"
                    else:
                        resolved = '❌'
                        footer_text = f"Resolved: {resolved}"
                    embed.set_footer(text=footer_text)
                    await channel.send(embed=embed)
            message = await channel.send(f"React with {check} if you're done getting your tickets for {channel.mention}!")
            await message.add_reaction(check)

            def reaction_check(reaction, user):
                return user == interaction_user and str(reaction.emoji) == check

            try:
                reaction, user = await self.client.wait_for('reaction_add', check=reaction_check, timeout=600) # Wait for reaction or 10 minutes
                if str(reaction.emoji) == check:
                    await channel.send("Tickets received, deleting this channel...")
                    await self.delete_sub_channel(channel=channel)
            except asyncio.TimeoutError:
                await channel.send("10 minutes have passed. Deleting this channel...")
                await self.delete_sub_channel(channel=channel)
    
    async def delete_command_messages(self, channel: discord.TextChannel, amount: int):
        await asyncio.sleep(2)
        await channel.purge(limit=amount, bulk=True)
        
    async def create_sub_channel(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = interaction.channel.category
        if interaction.channel.name == "get-ticket":
            channel_name = f"{interaction.user.nick}-Tickets"
        elif interaction.channel.name == "create-ticket":
            channel_name = f"Ticket_Creation-{interaction.user.nick}"
        else:
            channel_name = "Unknown"
        member_role = discord.utils.get(interaction.guild.roles, name = "Member")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
        }
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        return channel

    async def delete_sub_channel(self, channel: discord.TextChannel):
            await asyncio.sleep(2)
            await channel.delete()

    async def delete_channel_on_timeout(self, channel: discord.TextChannel, timeout: int, task: asyncio.Task):
        try:
            await asyncio.wait_for(asyncio.sleep(timeout), timeout=timeout)
        except asyncio.TimeoutError:
            if not task.cancelled():
                await channel.delete()
                print(f"Channel {channel.name} has been deleted due to inactivity.")

    async def get_member(self, guild: discord.Guild, userId):
        user_id = int(re.search(r'\d+', userId).group())
        return await guild.fetch_member(user_id)
    
    async def get_user(self, user_id):
        user_id = int(re.search(r'\d+', user_id).group())
        return await self.client.fetch_user(user_id)
    
    async def ask_for_project(self, cursor, guild, channel, interaction_user):
        cursor.execute("SELECT * FROM projects WHERE guild_id = %s", (guild.id,))
        projects = cursor.fetchall()
        project_options = []
        for project in projects:
            project_options.append(app_commands.Choice(name=project[2], value=str(project[0])))

        # Ask for the project
        project_options_text = ""
        for option in project_options:
            project_options_text += "**{}** - {}\n".format(option.value, option.name)
        await channel.send(f"Please select a project:\n{project_options_text}")
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=60)
        except asyncio.TimeoutError:
            await channel.send("Ticket getting timed out.")
            await self.delete_sub_channel(channel=channel)
            return
        project_id = project_choice_msg.content
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await channel.send("Invalid Project-ID. Please try again")
            await self.delete_sub_channel(channel=channel)
            return
        else:
            return project_id
        
    async def ask_for_team(self, project_id, cursor, channel, interaction_user):
        # Get the available teams from the database
        cursor.execute("SELECT * FROM teams WHERE project_id = %s", (project_id,))
        teams = cursor.fetchall()
        team_options = []
        for team in teams:
            team_options.append(app_commands.Choice(name=team[2], value=str(team[0])))

        # Ask for the team
        team_options_text = ""
        for option in  team_options:
            team_options_text += "**{}** - {}\n".format(option.value, option.name)
        await channel.send(f"Please select a team:\n{team_options_text}")
        try:
            team_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=60)
        except asyncio.TimeoutError:
            await channel.send("Ticket creation timed out.")
            await self.delete_sub_channel(channel=channel)
            return
        team_id = team_choice_msg.content
        
        valid_team_ids = [option.value for option in team_options]
        if team_id not in valid_team_ids:
            await channel.send("Invalid Team-ID. Please try again")
            await self.delete_sub_channel(channel=channel)
            return
        else:
            return team_id
        
    async def ask_for_member(self, team_id, cursor, guild, channel, interaction_user):
        # Get the available members from the database
        cursor.execute("SELECT * FROM members WHERE team_id = %s", (team_id,))
        members = cursor.fetchall()
        member_options = []
        for member in members:
            discord_member = await self.get_member(guild=guild, userId=member[2])
            nick = discord_member.nick if discord_member.nick is not None else discord_member.name
            member_options.append(app_commands.Choice(name=nick, value=str(member[0])))

        # Ask for the member
        member_options_text = ""
        for option in member_options:
            member_options_text += "**{}** - {}\n".format(option.value, option.name)
        await channel.send(f"Please select a a member:\n{member_options_text}")
        try:
            member_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=60)
        except asyncio.TimeoutError:
            await channel.send("Ticket creation timed out.")
            await self.delete_sub_channel(channel=channel)
            return
        member_id = member_choice_msg.content
        
        valid_member_ids = [option.value for option in member_options]
        if member_id not in valid_member_ids:
            await channel.send("Invalid Member-ID. Please try again")
            await self.delete_sub_channel(channel=channel)
            return
        else:
            return member_id
        
    async def create_ticket_dict(self, tickets, guild):
        member_cache = {member[0]: await self.get_member(guild=guild, userId=member[2]) for member in self.member_cache if member[2]}
        tickets_dict = {}
        for index, ticket in enumerate(tickets):
            for_member = member_cache.get(ticket[4], {})
            if ticket[14] in member_cache:
                assigned_member = member_cache[ticket[14]]
                ticket_assigned_to = assigned_member.nick
            else:
                ticket_assigned_to = "None"
            tickets_dict[index] = {
                "ticket_id": ticket[0],
                "ticket_for": for_member.nick,
                "ticket_author": ticket[5],
                "ticket_title": ticket[7],
                "ticket_description": ticket[8],
                "ticket_deadline": ticket[9],
                "ticket_resolved": ticket[10],
                "ticket_resolved_date": ticket[11],
                "ticket_creation_date": ticket[12],
                "assigned_to_member": ticket_assigned_to
            }
        return tickets_dict