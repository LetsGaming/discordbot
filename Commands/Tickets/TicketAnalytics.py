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
            self.connection.connect()
        self.ping_timer = Timer(1000, self.__restart_connection) 
        self.ping_timer.start() 
        
    def load_config(self):
        with open("Configs/sqlconfig.json") as file:
            return json.load(file)
        
    async def get_ticket_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cursor = self.connection.cursor()

        guild_id = interaction.guild.id
        cursor.execute("Select * from Tickets where guild_id = %s", (guild_id,))

        tickets = cursor.fetchall()
        
        ticket_authors = [ticket[5] for ticket in tickets]
        most_common_author, author_tickets_count = Counter(ticket_authors).most_common(1)[0]

        team_counts = Counter([ticket[0] for ticket in tickets])
        most_common_team_id, team_count = team_counts.most_common(1)[0]
        cursor.execute("Select name from teams where id = %s", (most_common_team_id,))
        result = cursor.fetchone()
        most_common_team = result[0]

        member_counts = Counter([ticket[1] for ticket in tickets])
        most_common_member_id, member_count = member_counts.most_common(1)[0]
        cursor.execute("Select discord_id from members where id = %s", (most_common_member_id,))
        result = cursor.fetchone()
        most_common_member = result[0]

        resolved_tickets = len([ticket for ticket in tickets if ticket[10]])
        unresolved_tickets = len([ticket for ticket in tickets if not ticket[10]])

        today = datetime.date.today()

        tickets_within_deadline = [ticket for ticket in tickets if not ticket[10] and ticket[9] >= today]

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
        self.send_stat_embed(dict=stat_dict, interaction=interaction)

    def send_stat_embed(self, dict: dict, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Stats")
        embed.add_field(name="Most Tickets created by:", value=dict['top_author'])
        embed.add_field(name="Team with most Tickets:", value=dict['top_team'])
        embed.add_field(name="Member with most Tickets:", value=dict['top_member'])
        embed.add_field(name="Amount of resolved Tickets:", value=dict['resolved_tickets'])
        embed.add_field(name="Amount of unresolved Tickets:", value=dict['unresolved_tickets'])
        embed.add_field(name="Amount within deadline:", value=dict['tickets_in_deadline'])

        interaction.channel.send(embed=embed)