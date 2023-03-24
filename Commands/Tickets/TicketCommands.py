import asyncio
import json
from datetime import date, datetime
from typing import Optional
from threading import Timer

import discord
import mysql.connector

class TicketCommands:
    def __init__(self, client, utils ):
        self.client = client
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start() 

        self.utils = utils

    def __restart_connection(self):
        self.connection.connect()
        self.ping_timer = Timer(28500, self.__restart_connection) 
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
        project_id = await self.utils.ask_for_project(channel=channel, interaction_user= interaction_user, guild=guild, cursor=cursor)

        team_id = await self.utils.ask_for_team(project_id=project_id, channel=channel,interaction_user=interaction_user, cursor=cursor)
        
        member_id = await self.utils.ask_for_member(team_id=team_id, cursor=cursor, guild=guild, channel=channel, interaction_user=interaction_user)
        
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
        today_date = date.today().isoformat()
        query = """
            INSERT INTO tickets (
                guild_id, project_id, team_id, member_id, ticket_author,
                ticket_author_icon, ticket_title, ticket_description, deadline,
                resolved, creation_date, assigned_team_id,
                assigned_member_id
            )
            VALUES (
                %(guild_id)s, %(project_id)s, %(team_id)s, %(member_id)s,
                %(ticket_author)s, %(ticket_author_icon)s, %(ticket_title)s,
                %(ticket_description)s, %(deadline)s, 0, %(creation_date)s,
            )
        """

        params = {
            "guild_id": guild.id,
            "project_id": project_id,
            "team_id": team_id,
            "member_id": member_id,
            "ticket_author": ticket_author.nick,
            "ticket_author_icon": ticket_author.avatar.url,
            "ticket_title": ticket_title,
            "ticket_description": ticket_description,
            "deadline": ticket_deadline_date,
            "creation_date": today_date,
        }

        cursor.execute(query, params)
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
        project_id = await self.utils.ask_for_project(channel=channel, interaction_user= interaction_user, guild=guild, cursor=cursor)
        
        discord_id = f"<@{interaction_user.id}>"
        cursor.execute("SELECT id, team_id FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        member_tuple = cursor.fetchone()
        member_id = member_tuple[0]
        team_id = member_tuple[1]
        
        if get_all:
            resolved_query = "" # empty string means all tickets will be retrieved
        elif get_resolved:
            resolved_query = "AND resolved = 1"
        else:
            resolved_query = "AND resolved = 0"
            
        query = f"SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s) AND (member_id = %s OR assigned_member_id = %s)) {resolved_query}"
        cursor.execute(query, (project_id, team_id, team_id, member_id, member_id))
        tickets = cursor.fetchall()
        
        await channel.send("Getting your tickets...")
        await self.utils.send_tickets_embeds(channel=channel, interaction_user=interaction_user, tickets_dict = await self.utils.create_ticket_dict(tickets=tickets, guild = guild))

    async def get_tickets_by_team(self, interaction: discord.Interaction, get_all: Optional[bool]=False, get_resolved: Optional[bool]=False):
        await interaction.response.defer()
        
        channel = await self.utils.create_sub_channel(interaction=interaction)
        await interaction.followup.send(f"Your interaction continues in <#{channel.id}>", ephemeral=True)
        await channel.send(f"Welcome {interaction.user.mention}! This is your ticket channel.")
        await self.utils.delete_command_messages(channel=interaction.channel,amount=2)
        
        guild = interaction.guild
        interaction_user = interaction.user
        
        cursor = self.connection.cursor()
        project_id = await self.utils.ask_for_project(channel=channel, interaction_user= interaction_user, guild=guild, cursor=cursor)
        
        #Check if user is leader
        discord_id = f"<@{interaction.user.id}>"
        cursor.execute("SELECT team_id, leader FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        result = cursor.fetchone()
        members_team_id = result[0]
        leader = result[1]
        
        if not leader:
            await channel.send("You're not the leader of your team!")
            return
        
        query = "SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s) AND resolved = 0)"
        if get_resolved:
            query = "SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s) AND resolved = 1)"
        if get_all:
            query = "SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s))"
        cursor.execute(query, (project_id, members_team_id, members_team_id))
        tickets = cursor.fetchall()

        await channel.send("Getting the tickets...")
        await self.utils.send_tickets_embeds(channel=channel, interaction_user=interaction_user, tickets_dict= await self.utils.create_ticket_dict(tickets=tickets, guild = guild))

    async def get_tickets_past_week(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        channel = await self.utils.create_sub_channel(interaction=interaction)
        await interaction.followup.send(f"Your interaction continues in <#{channel.id}>", ephemeral=True)
        await channel.send(f"Welcome {interaction.user.mention}! This is your ticket channel.")
        await self.utils.delete_command_messages(channel=interaction.channel,amount=2)
        
        guild = interaction.guild
        interaction_user = interaction.user
        
        cursor = self.connection.cursor()
        project_id = await self.utils.ask_for_project(channel=channel, interaction_user= interaction_user, guild=guild, cursor=cursor)
        
        #Check if user is leader
        discord_id = f"<@{interaction.user.id}>"
        cursor.execute("SELECT team_id, id, leader FROM members WHERE discord_id = %s AND project_id = %s", (discord_id, project_id))
        result = cursor.fetchone()
        members_team_id = result[0]
        member_id = result[1]
        leader = result[2]
        
        query = "SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s) AND (member_id = %s OR assigned_member_id = %s)) and creation_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 WEEK) AND NOW()"
        values = (project_id, members_team_id, members_team_id ,member_id, member_id)
        if leader:
            query = "SELECT * FROM tickets WHERE project_id = %s AND ((team_id = %s OR assigned_team_id = %s) and creation_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 WEEK) AND NOW()"
            values = (project_id, members_team_id, members_team_id)

        cursor.execute(query, values)
        tickets = cursor.fetchall()

        await channel.send("Getting the tickets...")
        await self.utils.send_tickets_embeds(channel=channel, interaction_user=interaction_user, tickets_dict= await self.utils.create_ticket_dict(tickets=tickets, guild = guild))
        
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
        
    async def assign_ticket_to(self, interaction: discord.Interaction, ticket_id: int):
        await interaction.response.defer()
        await interaction.followup.send("Assigning ticket to another user...")
        cursor = self.connection.cursor()
        cursor.execute("SELECT project_id FROM tickets WHERE id = %s", (ticket_id,))
        project_id = cursor.fetchone()[0]

        team_id = await self.utils.ask_for_team(project_id=project_id, cursor=cursor, channel=interaction.channel, interaction_user=interaction.user)
        
        member_id = await self.utils.ask_for_member(team_id=team_id, cursor=cursor, guild=interaction.guild, channel=interaction.channel, interaction_user=interaction.user)
        
        cursor.execute("UPDATE tickets SET assigned_team_id = %s, assigned_member_id = %s WHERE id = %s", (team_id, member_id, ticket_id))
        await interaction.channel.send("New assignment successful")

class Ticket:
    def __init__(self, id, team_member_id, guild_id, created_at=None):
        self.id = id
        self.team_member_id = team_member_id
        self.guild_id = guild_id
        self.created_at = created_at or datetime.utcnow()