import asyncio
import json
from datetime import date, datetime
from typing import Optional
from threading import Timer

import discord
import mysql.connector
from discord import app_commands

from Commands.Tickets.TicketUtils import TicketUtils
from Commands.Tickets.TicketAnalytics import TicketStatistics

class TicketSystem:
    def __init__(self, tree: app_commands.CommandTree, client: discord.Client):
        self.tree = tree
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

        self.utils = TicketUtils(client)
        self.analytics = TicketStatistics()    


    def __restart_connection(self):
        if not self.connection.is_connected:
            self.connection.connect()
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)

    async def register_commands(self):
        self.tree.command(name="create_ticket", description="Creates a ticket for a project/team/member")(self.create_ticket)
        self.tree.command(name="get_tickets", description="Gets your open tickets for a project (Note: Set get_resolved = True, to get all tickets)")(self.get_ticket)
        self.tree.command(name="resolve_ticket", description="Lets you resolve one of your tickets")(self.resolve_ticket)
        self.tree.command(name="create_project", description="Create a new Project with Teams/Members")(self.create_project)
        self.tree.command(name="add_team", description="Adds a team to a project")(self.add_team_to_project)
        self.tree.command(name="add_member", description="Adds a member to a team")(self.add_member_to_team)
        self.tree.command(name="ticket_stats", description="Returns a embed with the Ticket-Statistics of this guild")(self.analytics.get_ticket_stats)

    async def create_ticket(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = await self.utils.create_sub_channel(interaction=interaction)
        await interaction.followup.send(f"Your interaction continues in <#{channel.id}>", ephemeral=True)
        await channel.send(f"Welcome {interaction.user.mention}! This is your ticket channel.")
        await self.utils.delete_command_messages(channel=interaction.channel,amount=2)
        
        guild = interaction.guild
        interaction_user = interaction.user
        
        # Get the available projects from the database
        cursor = self.connection.cursor()
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
            await channel.send("Ticket creation timed out.")
            await self.utils.delete_sub_channel(channel=channel)
            return
        project_id = project_choice_msg.content
        
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await channel.send("Invalid Project-ID. Please try again")
            await self.utils.delete_sub_channel(channel=channel)
            return

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
            await self.utils.delete_sub_channel(channel=channel)
            return
        team_id = team_choice_msg.content
        
        valid_team_ids = [option.value for option in team_options]
        if team_id not in valid_team_ids:
            await channel.send("Invalid Tean-ID. Please try again")
            await self.utils.delete_sub_channel(channel=channel)
            return
        
        # Get the available members from the database
        cursor.execute("SELECT * FROM members WHERE team_id = %s", (team_id,))
        members = cursor.fetchall()
        member_options = []
        for member in members:
            discord_member = await self.utils.get_member(guild=guild, userId=member[2])
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
            await self.utils.delete_sub_channel(channel=channel)
            return
        member_id = member_choice_msg.content
        
        valid_member_ids = [option.value for option in member_options]
        if member_id not in valid_member_ids:
            await channel.send("Invalid Member-ID. Please try again")
            await self.utils.delete_sub_channel(channel=channel)
            return
        
        await channel.send("What would you like the title of the ticket to be?")
        try:
            ticket_title_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=100)
        except asyncio.TimeoutError:
            await channel.send("Ticket creation timed out.")
            await self.utils.delete_sub_channel(channel=channel)
            return
        ticket_title = ticket_title_msg.content

        await channel.send("What would you like the reason/description for the ticket to be?")
        try:
            ticket_description_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=180)
        except asyncio.TimeoutError:
            await channel.send("Ticket creation timed out.")
            await self.utils.delete_sub_channel(channel=channel)
            return
        ticket_description = ticket_description_msg.content

        await channel.send("What is the deadline for the ticket? ")
        try:
            ticket_deadline_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=60)
        except asyncio.TimeoutError:
            await channel.send("Ticket creation timed out.")
            await self.utils.delete_sub_channel(channel=channel)
            return
        ticket_deadline = ticket_deadline_msg.content
        date_obj = datetime.strptime(ticket_deadline, '%d.%m.%Y')
        ticket_deadline_date = date_obj.strftime('%Y-%m.%d')
        
        # Create the ticket in the database
        ticket_author = interaction_user
        cursor.execute("INSERT INTO tickets (id, guild_id, project_id, team_id, member_id, ticket_author, ticket_author_icon, ticket_title, ticket_description, deadline, resolved, resolve_date) VALUES (null,%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, null)",
                         (guild.id, project_id, team_id, member_id, ticket_author.nick, ticket_author.avatar.url, ticket_title, ticket_description, ticket_deadline_date))
        self.connection.commit()
        ticket_id = cursor.lastrowid
        await channel.send("Ticket created successfully!")
        await self.utils.delete_sub_channel(channel=channel)
        
        ticket = Ticket(id=ticket_id, team_member_id=member_id, guild_id=guild.id)
        await self.on_ticket_create(ticket=ticket)
    
    async def on_ticket_create(self, ticket):
        cursor = self.connection.cursor()
        cursor.execute("SELECT discord_id FROM members WHERE id = %s", (ticket.team_member_id,))
        member_tuple = cursor.fetchone()
        discord_id = member_tuple[0]
        # Get the user who created the ticket
        user = await self.utils.get_user(user_id=discord_id)
        
        # Send a notification to the user
        guild = await self.client.fetch_guild(ticket.guild_id)
        message = f"Hello {user.name}, you have a new Ticket: #{ticket.id} in the server {guild.name} go check it out!"
        channel = await user.create_dm()
        await channel.send(content=message)
           
    async def get_ticket(self, interaction: discord.Interaction, get_all: Optional[bool]=False, get_resolved: Optional[bool]=False):
        await interaction.response.defer()
        
        channel = await self.utils.create_sub_channel(interaction=interaction)
        await interaction.followup.send(f"Your interaction continues in <#{channel.id}>", ephemeral=True)
        await channel.send(f"Welcome {interaction.user.mention}! This is your ticket channel.")
        await self.utils.delete_command_messages(channel=interaction.channel,amount=2)
        
        guild = interaction.guild
        interaction_user = interaction.user
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects WHERE guild_id = %s", (guild.id,))
        projects = cursor.fetchall()
        project_options = []
        for project in projects:
            project_options.append(app_commands.Choice(name=project[2], value=str(project[0])))

        # Ask for the project
        project_options_text = ""
        for option in project_options:
            project_options_text += "**{}** - {}\n".format(option.value, option.name)
        await channel.send(f"For what project do you want to get your tickets?:\n{project_options_text}")
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction_user, timeout=60)
        except asyncio.TimeoutError:
            await channel.send("Ticket getting timed out.")
            await self.utils.delete_sub_channel(channel=channel)
            return
        project_id = project_choice_msg.content
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await channel.send("Invalid Project-ID. Please try again")
            await self.utils.delete_sub_channel(channel=channel)
            return
        
        discord_id = f"<@{interaction_user.id}>"
        cursor.execute("SELECT id, team_id FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        member_tuple = cursor.fetchone()
        member_id = member_tuple[0]
        team_id = member_tuple[1]

        query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s AND resolved = 0"
        if get_resolved:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s AND resolved = 1"
        if get_all:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s"
        cursor.execute(query, (project_id, team_id, member_id))
        tickets = cursor.fetchall()
        tickets_dict = {}
        for index, ticket in enumerate(tickets):
            ticket_id = ticket[0]
            ticket_author = ticket[5]
            author_icon = ticket[6]
            ticket_title = ticket[7]
            ticket_description = ticket[8]
            ticket_deadline = ticket[9]
            ticket_resolved = ticket[10]
            ticket_resolved_date = ticket[11]
            tickets_dict[index] = {
                "ticket_id": ticket_id,
                "author_icon": author_icon,
                "ticket_author": ticket_author,
                "ticket_title": ticket_title,
                "ticket_description": ticket_description,
                "ticket_deadline": ticket_deadline,
                "ticket_resolved": ticket_resolved,
                "ticket_resolved_date": ticket_resolved_date
            }
        await channel.send("Getting your tickets...")
        await self.utils.send_tickets_embeds(channel=channel, interaction_user=interaction_user, tickets_dict=tickets_dict)
        
    async def resolve_ticket(self, interaction: discord.Interaction, ticket_id: int):
        await interaction.response.defer()
        cursor = self.connection.cursor()

        cursor.execute("SELECT member_id FROM tickets WHERE id = %s", (ticket_id,))
        member_id = cursor.fetchone()[0]

        cursor.execute("SELECT discord_id FROM members WHERE id = %s", (member_id,))
        discord_id = cursor.fetchone()[0]
        
        resolver_id = f"<@{interaction.user.id}>"
        if discord_id == resolver_id:
            resolve_date = date.today().isoformat()
            cursor.execute("UPDATE tickets SET resolved = 1, resolve_date = %s WHERE tickets.id = %s", (resolve_date, ticket_id))
            self.connection.commit()
            await interaction.followup.send(f"Your Ticket with ID: {ticket_id} got resolved!")
        else:
            await interaction.followup.send(f"This Ticket does not belong to you, you can't resolve it!")
            return
         
    async def create_project(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Check if user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.channel.send("Please contact the server owner if you wish to create a new project!")
            return

        # Prompt for project name
        await interaction.followup.send("What would you like to name your project?")
        try:
            project_name_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Project creation timed out.")
            return
        project_name = project_name_msg.content
        
        # Insert the project into the database
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO projects (id, guild_id, name) VALUES (null, %s, %s)", (interaction.guild.id, project_name))
        self.connection.commit()
        project_id = cursor.lastrowid
        
        # Prompt for team amounts
        await interaction.followup.send("How many teams do you want to add?")
        try:
            team_amount_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Project creation timed out.")
            return
        team_amount = team_amount_msg.content

        for x in range(team_amount):
        # Prompt for team name
            await interaction.followup.send(f"What would you like to name your {x+1}. team?")
            try:
                team_name_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            except asyncio.TimeoutError:
                await interaction.followup.send("Project creation timed out.")
                return
            team_name = team_name_msg.content
            
            # Create the team and prompt for member addition
            team_id = self.create_team(interaction=interaction, name=team_name, description="", project_id=project_id)
            while True:
                await interaction.followup.send("Would you like to add a member to the team? (y/n)")
                try:
                    add_member_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
                except asyncio.TimeoutError:
                    await interaction.followup.send("Member addition timed out.")
                    return
                add_member = add_member_msg.content.lower()
                if add_member == "n":
                    break
                elif add_member != "y":
                    await interaction.followup.send("Invalid input. Please enter 'y' or 'n'.")
                    continue
                
                # Prompt for member name
                await interaction.followup.send("What is the name of the member you would like to add?")
                try:
                    member_name_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
                except asyncio.TimeoutError:
                    await interaction.followup.send("Member addition timed out.")
                    return
                member_name = member_name_msg.content
                if not member_name.startswith("<"):
                    await interaction.followup.send(f"'{member_name}' is not a valid form. Please use @username!")
                    continue
                # Add the member to the team
                self.add_member(interaction=interaction,discord_id=member_name, team_id=team_id, project_id=project_id)
        
        await interaction.channel.send(f"Project '{project_name}' successfully created.")

    async def add_team_to_project(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Check if user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.channel.send("Please contact the server owner if you wish to add a new team to a project!")
            return

        # Get the available projects from the database
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects WHERE guild_id = %s", (interaction.guild.id,))
        projects = cursor.fetchall()
        project_options = []
        for project in projects:
            project_options.append(app_commands.Choice(name=project[2], value=str(project[0])))

        # Ask for the project
        project_options_text = ""
        for option in project_options:
            project_options_text += "**{}** - {}\n".format(option.value, option.name)
        await interaction.followup.send(f"Please select a project:\n{project_options_text}")     
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            return
        project_id = project_choice_msg.content
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await interaction.followup.send("Invalid Project-ID. Please try again")
            return
        
        await interaction.followup.send(f"What do you want to name the team?")     
        try:
            team_name_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            return
        team_name = team_name_msg.content
        self.create_team(interaction=interaction, name=team_name, description="", project_id=project_id)
        await interaction.channel.send(f"Team {team_name} successfully created!")
    
    async def add_member_to_team(self, interaction: discord.Interaction, discord_id: str, team_name: str):
        await interaction.response.defer()
        # Check if user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.channel.send("Please contact the server owner if you wish to create a new project!")
            return
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM projects WHERE guild_id = %s", (interaction.guild.id,))
        projects = cursor.fetchall()
        project_options = []
        for project in projects:
            project_options.append(app_commands.Choice(name=project[2], value=str(project[0])))

        # Ask for the project
        project_options_text = ""
        for option in project_options:
            project_options_text += "**{}** - {}\n".format(option.value, option.name)
        await interaction.followup.send(f"Please select a project:\n{project_options_text}")     
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Member addition timed out.")
            return
        project_id = project_choice_msg.content
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await interaction.followup.send("Invalid Project-ID. Please try again")
            return
        
        # Extract the member's name and ID from the tag
        if not discord_id.startswith("<"):
            await interaction.channel.send(f"'{discord_id}' is not a valid form. Please use @username !")
            return

        # Add the member to the team
        team_id = self.get_team_id(team_name, project_id)
        if not team_id:
            await interaction.channel.send(f"Team '{team_name}' not found in project '{project_id}'.")
            return

        query = "INSERT INTO members (id, guild_id, discord_id, team_id, project_id) VALUES (null, %s, %s, %s, %s);"
        values = (interaction.guild.id, discord_id, team_id, project_id)
        cursor.execute(query, values)
        self.connection.commit()

        await interaction.channel.send(f"Added member '{discord_id}' to team '{team_name}' in project '{project_id}'.")

    def add_member(self, interaction: discord.Interaction, discord_id, team_id, project_id):
            cursor = self.connection.cursor()
            cursor.execute(("INSERT INTO members (id, guild_id, discord_id, team_id, project_id) VALUES (null, %s, %s, %s, %s)"), (interaction.guild.id, discord_id, team_id, project_id))
            self.connection.commit()

    def create_team(self, interaction: discord.Interaction, name: str, description: str, project_id: int) -> int:
        cursor = self.connection.cursor()
        query = "INSERT INTO teams (id, guild_id, name, description, project_id) VALUES (null, %s, %s, %s, %s);"
        values = (interaction.guild.id, name, description, project_id)
        cursor.execute(query, values)
        self.connection.commit()
        team_id = cursor.lastrowid
        return team_id
    
    def get_team_id(self, team_name: str, project_id: str) -> Optional[int]:
        cursor = self.connection.cursor()
        query = "SELECT teams.id FROM teams INNER JOIN projects ON teams.project_id = projects.id WHERE teams.name = %s AND projects.id = %s;"
        values = (team_name, project_id)
        cursor.execute(query, values)
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return None
        
class Ticket:
    def __init__(self, id, team_member_id, guild_id, created_at=None):
        self.id = id
        self.team_member_id = team_member_id
        self.guild_id = guild_id
        self.created_at = created_at or datetime.utcnow()