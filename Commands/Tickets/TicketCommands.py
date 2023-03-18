import asyncio
import json
from datetime import date, datetime
from typing import Optional
from threading import Timer

import discord
import mysql.connector
from discord import app_commands

from Commands.Tickets.TicketUtils import TicketUtils

class TicketCommands:
    def __init__(self, client: discord.Client):
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

    def __restart_connection(self):
        if not self.connection.is_connected:
            self.connection.reconnect(attempts=5)
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)

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
        today = datetime.date.today()
        today_date = today.strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO tickets (id, guild_id, project_id, team_id, member_id, ticket_author, ticket_author_icon, ticket_title, ticket_description, deadline, resolved, resolve_date, creation_date) VALUES (null,%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, null, %s)",
                         (guild.id, project_id, team_id, member_id, ticket_author.nick, ticket_author.avatar.url, ticket_title, ticket_description, ticket_deadline_date, today_date))
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
                "ticket_for": interaction_user.nick,
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

    async def get_tickets_by_team(self, interaction: discord.Interaction, get_all: Optional[bool]=False, get_resolved: Optional[bool]=False):
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
        await channel.send(f"For what project do you want to get the tickets?:\n{project_options_text}")
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
        
        #Check if user is leader
        discord_id = f"<@{interaction.user.id}>"
        cursor.execute("SELECT team_id, leader FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        result = cursor.fetchone()
        members_team_id = result[0]
        leader = result[1]
        
        if not leader:
            await channel.send("You're not the leader of your team!")
            return
        
        query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND resolved = 0"
        if get_resolved:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND resolved = 1"
        if get_all:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s"
        cursor.execute(query, (project_id, members_team_id))
        tickets = cursor.fetchall()
        tickets_dict = {}
        for index, ticket in enumerate(tickets):
            cursor.execute("SELECT discord_id from members where id = %s", (ticket[4],))
            ticket_discord_id = cursor.fetchone()[0]
            ticket_for_user = await self.utils.get_member(guild=guild,userId=ticket_discord_id)
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
                "ticket_for": ticket_for_user.nick,
                "author_icon": author_icon,
                "ticket_author": ticket_author,
                "ticket_title": ticket_title,
                "ticket_description": ticket_description,
                "ticket_deadline": ticket_deadline,
                "ticket_resolved": ticket_resolved,
                "ticket_resolved_date": ticket_resolved_date
            }
        await channel.send("Getting the tickets...")
        await self.utils.send_tickets_embeds(channel=channel, interaction_user=interaction_user, tickets_dict=tickets_dict)

    async def get_tickets_past_week(self, interaction: discord.Interaction):
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
        await channel.send(f"For what project do you want to get the tickets?:\n{project_options_text}")
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
        
        #Check if user is leader
        discord_id = f"<@{interaction.user.id}>"
        cursor.execute("SELECT team_id, id, leader FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        result = cursor.fetchone()
        members_team_id = result[0]
        member_id = result[1]
        leader = result[2]
        
        query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s AND member_id = %s and creation_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 WEEK) AND NOW()"
        values = (project_id, members_team_id, member_id)
        if leader:
            query = "SELECT * FROM tickets WHERE project_id = %s AND team_id = %s and creation_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 WEEK) AND NOW()"
            values = (project_id, members_team_id)

        cursor.execute(query, values)
        tickets = cursor.fetchall()
        tickets_dict = {}
        for index, ticket in enumerate(tickets):
            cursor.execute("SELECT discord_id from members where id = %s", (ticket[4],))
            ticket_discord_id = cursor.fetchone()[0]
            ticket_for_user = await self.utils.get_member(guild=guild,userId=ticket_discord_id)
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
                "ticket_for": ticket_for_user.nick,
                "author_icon": author_icon,
                "ticket_author": ticket_author,
                "ticket_title": ticket_title,
                "ticket_description": ticket_description,
                "ticket_deadline": ticket_deadline,
                "ticket_resolved": ticket_resolved,
                "ticket_resolved_date": ticket_resolved_date
            }
        await channel.send("Getting the tickets...")
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
         
class Ticket:
    def __init__(self, id, team_member_id, guild_id, created_at=None):
        self.id = id
        self.team_member_id = team_member_id
        self.guild_id = guild_id
        self.created_at = created_at or datetime.utcnow()