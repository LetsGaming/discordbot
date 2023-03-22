import discord
from discord import app_commands

from Commands.Tickets.TicketAnalytics import TicketStatistics
from Commands.Tickets.TicketCommands import TicketCommands
from Commands.Tickets.TicketProjectCommands import TicketProjectCommands
from Commands.Tickets.TicketUtils import TicketUtils

class TicketSystemHandler:
    def __init__(self, tree: app_commands.CommandTree, client: discord.Client):
        self.tree = tree
        self.client = client
        self.utils = TicketUtils(client)
        self.ticketCommands = TicketCommands(utils=self.utils)
        self.ticketProjectCommands = TicketProjectCommands(utils=self.utils)
        self.ticketStatistics = TicketStatistics()

    async def register_commands(self):
        self.tree.command(name="create_ticket", description="Creates a ticket for a project/team/member")(self.ticketCommands.create_ticket)
        self.tree.command(name="get_tickets", description="Retrieve your open project tickets. To get resolved tickets, set get_resolved = True.")(self.ticketCommands.get_ticket)
        self.tree.command(name="get_tickets_week", description="Retrieve your tickets created in past week. Leaders get all team tickets.")(self.ticketCommands.get_tickets_past_week)
        self.tree.command(name="get_tickets_team", description="Gets all tickets of your team, if you're the leader!")(self.ticketCommands.get_tickets_by_team)
        self.tree.command(name="resolve_ticket", description="Lets you resolve one of your tickets")(self.ticketCommands.resolve_ticket)
        #self.tree.command(name="assign_ticket_to", description="Lets you assign a Ticket to a another user")(self.ticketCommands.assign_ticket_to)
        self.tree.command(name="create_project", description="Create a new Project with Teams/Members")(self.ticketProjectCommands.create_project)
        self.tree.command(name="add_team", description="Adds a team to a project")(self.ticketProjectCommands.add_team_to_project)
        self.tree.command(name="add_member", description="Adds a member to a team")(self.ticketProjectCommands.add_member_to_team)
        self.tree.command(name="ticket_stats", description="Returns a embed with the Ticket-Statistics of this guild")(self.ticketStatistics.get_ticket_stats)   