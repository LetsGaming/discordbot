import asyncio
import json
from threading import Timer
from typing import Optional
import discord
from discord import app_commands
import mysql.connector

class TicketProjectCommands:
    def __init__(self):
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start()
        
    def __restart_connection(self):
        self.connection.connect()
        self.ping_timer = Timer(28500, self.__restart_connection) 
        self.ping_timer.start() 
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)

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

                await interaction.followup.send("Is this member a Teamleader? (y/n)")
                try:
                    leader_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
                except asyncio.TimeoutError:
                    await interaction.followup.send("Member addition timed out.")
                    return
                leader_choice = leader_choice_msg.content.lower()
                if leader_choice == "n":
                    leader = 0
                elif leader_choice == "y":
                    leader = 1
                elif leader_choice != "y":
                    await interaction.followup.send("Invalid input. Please enter 'y' or 'n'.")
                    continue

                # Add the member to the team
                self.add_member(interaction=interaction,discord_id=member_name, team_id=team_id, project_id=project_id, leader=leader)
        
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
    
    async def add_member_to_team(self, interaction: discord.Interaction, discord_id: str):
        await interaction.response.defer()

        # Extract the member's name and ID from the tag
        if not discord_id.startswith("<"):
            await interaction.channel.send(f"'{discord_id}' is not a valid form. Please use @username !")
            return

        # Check if user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.channel.send("Please contact the server owner if you wish to add someone to your team!")
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
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM teams WHERE guild_id = %s and project_id = %s", (interaction.guild.id, project_id,))
        teams = cursor.fetchall()
        team_options = []
        for team in teams:
            team_options.append(app_commands.Choice(name=team[2], value=str(team[0])))
        
        # Ask for the team
        team_options_text = ""
        for option in team_options:
            team_options_text += "**{}** - {}\n".format(option.value, option.name)
        await interaction.followup.send(f"Please select a team:\n{team_options_text}")     
        try:
            team_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Member addition timed out.")
            return
        team_id = team_choice_msg.content
        valid_team_ids = [option.value for option in team_options]
        if project_id not in valid_team_ids:
            await interaction.followup.send("Invalid Team-ID. Please try again")
            return

        leader_options = []
        for i in range(2):
            if i == 0:
                value_text = "False"
            else: 
                value_text = "True"
            leader_options.append(app_commands.Choice(name=i, value=value_text))

        leader_options_text = ""
        for option in leader_options:
            leader_options_text += "**{}** - {}\n".format(option.value, option.name)
        await interaction.followup.send(f"Please select if member is leader or not:\n{leader_options_text}")     
        try:
            leader_choice_msg = await self.client.wait_for('message', check=lambda m: m.author == interaction.user, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("Member addition timed out.")
            return
        leader_value = leader_choice_msg.content
        valid_leader_options = [option.value for option in leader_options]
        if leader_value not in valid_leader_options:
            await interaction.followup.send("Invalid Value. Please try again")
            return

        self.add_member(interaction=interaction, discord_id=discord_id, team_id=team_id, project_id=project_id, leader=leader_value)

        await interaction.channel.send(f"Added member {discord_id} to team ' {team_id} ' in project ' {project_id} '.")

    def add_member(self, interaction: discord.Interaction, discord_id, team_id, project_id, leader):
            cursor = self.connection.cursor()
            cursor.execute(("INSERT INTO members (id, guild_id, discord_id, team_id, project_id, leader) VALUES (null, %s, %s, %s, %s, %s)"), (interaction.guild.id, discord_id, team_id, project_id, leader))
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
        