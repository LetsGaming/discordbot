import asyncio
import json
import re
from datetime import date, datetime
from typing import Optional

import discord
import mysql.connector
from discord import app_commands

class Ticket:
    def __init__(self, tree: app_commands.CommandTree, client: discord.Client):
        self.client = client
        self.tree = tree
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.lastResult = None
        
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

    async def create_ticket(self, interaction: discord.Interaction):
        message_amount = 0
        await interaction.response.defer()
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
        message_amount += 1     
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        project_id = project_choice_msg.content
        
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await interaction.followup.send("Invalid Project-ID. Please try again")
            message_amount += 1
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
        await interaction.channel.send(f"Please select a team:\n{team_options_text}")
        message_amount += 1     
        try:
            team_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        team_id = team_choice_msg.content
        
        valid_team_ids = [option.value for option in team_options]
        if team_id not in valid_team_ids:
            await interaction.followup.send("Invalid Tean-ID. Please try again")
            message_amount += 1
            return
        
        # Get the available members from the database
        cursor.execute("SELECT * FROM members WHERE team_id = %s", (team_id,))
        members = cursor.fetchall()
        member_options = []
        for member in members:
            user = await self.get_user(member[2])
            member_options.append(app_commands.Choice(name=user.name, value=str(member[0])))

        # Ask for the member
        member_options_text = ""
        for option in member_options:
            member_options_text += "**{}** - {}\n".format(option.value, option.name)
        await interaction.channel.send(f"Please select a a member:\n{member_options_text}")    
        message_amount += 1 
        try:
            member_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        member_id = member_choice_msg.content
        
        valid_member_ids = [option.value for option in member_options]
        if member_id not in valid_member_ids:
            await interaction.followup.send("Invalid Member-ID. Please try again")
            message_amount += 1
            return
        
        await interaction.followup.send("What would you like the title of the ticket to be?")
        message_amount += 1
        try:
            ticket_title_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        ticket_title = ticket_title_msg.content

        await interaction.followup.send("What would you like the reason/description for the ticket to be?")
        message_amount += 1
        try:
            ticket_description_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        ticket_description = ticket_description_msg.content

        await interaction.followup.send("What is the deadline for the ticket? ")
        message_amount += 1
        try:
            ticket_deadline_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket creation timed out.")
            message_amount += 1
            return
        ticket_deadline = ticket_deadline_msg.content
        date_obj = datetime.strptime(ticket_deadline, '%d.%m.%Y')
        ticket_deadline_date = date_obj.strftime('%Y-%m.%d')
        
        # Create the ticket in the database
        ticket_author = await self.get_user(user_id=interaction.user.id)
        cursor.execute("INSERT INTO tickets (id, guild_id, project_id, team_id, member_id, ticket_author, ticket_title, ticket_description, deadline, resolved, resolve_date) VALUES (null, %s, %s, %s, %s, %s, %s, %s, %s, 0, null)",
                         (interaction.guild.id, project_id, team_id, member_id, ticket_author, ticket_title, ticket_description, ticket_deadline_date))
        self.connection.commit()
        print(message_amount)
        await self.delete_command_messages(interaction = interaction, amount=message_amount)
        await interaction.channel.send("Ticket created successfully!")
           
    async def get_ticket(self, interaction: discord.Interaction, get_resolved: Optional[bool]=False):
        message_amount = 0
        await interaction.response.defer()
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
        await interaction.followup.send(f"For what project do you want to get your tickets?:\n{project_options_text}")    
        message_amount += 1 
        try:
            project_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
            message_amount += 1
        except asyncio.TimeoutError:
            await interaction.followup.send("Ticket getting timed out.")
            message_amount += 1
            return
        project_id = project_choice_msg.content
        valid_project_ids = [option.value for option in project_options]
        if project_id not in valid_project_ids:
            await interaction.followup.send("Invalid Project-ID. Please try again")
            message_amount += 1
            return
        
        discord_id = f"<@{interaction.user.id}>"
        cursor.execute("SELECT id, team_id FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        member_tuple = cursor.fetchone()
        member_id = member_tuple[0]
        team_id = member_tuple[1]

        query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s AND resolved = 0"
        if get_resolved:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s AND resolved = 1"
        cursor.execute(query, (project_id, team_id, member_id))
        tickets = cursor.fetchall()
        tickets_dict = {}
        for index, ticket in enumerate(tickets):
            print(ticket)
            ticket_id = ticket[0]
            ticket_author = ticket[5]
            ticket_title = ticket[6]
            ticket_description = ticket[7]
            ticket_deadline = ticket[8]
            ticket_resolved = ticket[9]
            ticket_resolved_date = ticket[10]
            tickets_dict[index] = {
                "ticket_id": ticket_id,
                "ticket_author": ticket_author,
                "ticket_title": ticket_title,
                "ticket_description": ticket_description,
                "ticket_deadline": ticket_deadline,
                "ticket_resolved": ticket_resolved,
                "ticket_resolved_date": ticket_resolved_date
            }
        await self.send_tickets_embeds(interaction, tickets_dict, message_amount)
        
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
        
        # Prompt for team name
        await interaction.followup.send("What would you like to name your first team?")
        try:
            team_name_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Project creation timed out.")
            return
        team_name = team_name_msg.content
        
        # Create the team and prompt for member addition
        team_id = self.create_team(interaction=interaction, name=team_name, description="", project_id=project_id)
        interaction.response.defer()
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
            
            # Prompt for member name and email
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
            self.add_member(interaction=interaction,discord_id=member_name, team_id=team_id, project_id=project_id) # Change the arguments to match your add_member function
        
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
            await interaction.channel.send(f"'{discord_id}' is not a valid form. Please use @username!")
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

    async def send_tickets_embeds(self, interaction:discord.Interaction, tickets_dict: dict, amount: int):
            await self.delete_command_messages(interaction=interaction, amount=amount)
            if len(tickets_dict) < 1:
                await interaction.channel.send("You do not have any (open) Tickets!")
            else:
                for ticket_index in tickets_dict:
                    ticket = tickets_dict[ticket_index]
                    embed = discord.Embed(title=ticket["ticket_title"], description=ticket["ticket_description"])
                    embed.set_author(name=f"From: {ticket['ticket_author']}")
                    embed.add_field(name="ID", value=ticket["ticket_id"])
                    embed.add_field(name="Deadline", value=ticket["ticket_deadline"].strftime('%d.%m.%Y'))
                    if ticket["ticket_resolved"]:
                        resolved = '✅'
                        footer_text = f"Resolved: {resolved} \nResolved on date: {ticket['ticket_resolved_date'].strftime('%d.%m.%Y')}"
                    else:
                        resolved = '❌'
                        footer_text = f"Resolved: {resolved}"
                    embed.set_footer(text = footer_text)
                    await interaction.channel.send(embed=embed)

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
        
    async def get_user(self, user_id):
        user_id = int(re.search(r'\d+', user_id).group())
        return await self.client.fetch_user(user_id)
    
    async def delete_command_messages(self, interaction: discord.Interaction, amount: int):
        await interaction.channel.purge(limit=amount, bulk=True)