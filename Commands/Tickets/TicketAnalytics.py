from collections import Counter
import datetime
import json
from threading import Timer
import discord
import mysql.connector

class TicketStatistics:
    def __init__(self):
        self.config = self.load_config()
        self.connection = mysql.connector.connect(
            host= self.config["host"],
            user= self.config["username"],
            password= self.config["password"],
            database="pythonbot"
        )
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
    def __restart_connection(self):
        if not self.connection.is_connected:
            self.connection.reconnect(attempts=5)
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)
        
    async def get_ticket_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("Gathering data...")
        cursor = self.connection.cursor()

        guild_id = interaction.guild.id
        cursor.execute("Select * from tickets where guild_id = %s", (guild_id,))

        tickets = cursor.fetchall()
        
        team_counts = Counter([ticket[3] for ticket in tickets])
        most_common_team_id, team_count = team_counts.most_common(1)[0]
        cursor.execute("Select name from teams where id = %s", (most_common_team_id,))
        result = cursor.fetchone()
        most_common_team = result[0]

        member_counts = Counter([ticket[4] for ticket in tickets])
        most_common_member_id, member_count = member_counts.most_common(1)[0]
        cursor.execute("Select discord_id from members where id = %s", (most_common_member_id,))
        result = cursor.fetchone()
        most_common_member = result[0]

        ticket_authors = [ticket[5] for ticket in tickets]
        most_common_author, author_tickets_count = Counter(ticket_authors).most_common(1)[0]

        resolved_tickets = len([ticket for ticket in tickets if ticket[10]])
        unresolved_tickets = len([ticket for ticket in tickets if not ticket[10]])

        cursor.execute("SELECT * FROM tickets WHERE resolve_date > deadline;")
        result=cursor.fetchall()
        tickets_within_deadline = len(result)

        stat_dict = {
            'top_author': most_common_author,
            'author_count': author_tickets_count,
            'top_team': most_common_team,
            'team_count': team_count,
            'top_member': most_common_member,
            'member_count': member_count,
            'resolved_tickets': resolved_tickets,
            'unresolved_tickets': unresolved_tickets,
            'tickets_in_deadline': tickets_within_deadline
        }
        await self.send_stat_embed(dict=stat_dict, interaction=interaction)

    async def send_stat_embed(self, dict: dict, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Stats")
        embed.add_field(name="Most Tickets created by:", value=dict['top_author'])
        embed.add_field(name="Team with most Tickets:", value=dict['top_team'])
        embed.add_field(name="Member with most Tickets:", value=dict['top_member'])
        embed.add_field(name="Amount of resolved Tickets:", value=dict['resolved_tickets'])
        embed.add_field(name="Amount of unresolved Tickets:", value=dict['unresolved_tickets'])
        embed.add_field(name="Amount within deadline:", value=dict['tickets_in_deadline'])

        await interaction.channel.send(embed=embed)