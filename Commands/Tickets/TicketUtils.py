import asyncio
import re
import discord

class TicketUtils:
    def __init__(self, client: discord.Client):
        self.client = client

    async def send_tickets_embeds(self, channel: discord.TextChannel, interaction_user, tickets_dict: dict):
            check = '✅'
            if len(tickets_dict) < 1:
                await channel.send("You do not have any (open) Tickets!")
            else:
                for ticket_index in tickets_dict:
                    ticket = tickets_dict[ticket_index]
                    embed = discord.Embed(title=ticket["ticket_title"], description=ticket["ticket_description"])
                    embed.set_author(name=f"From: {ticket['ticket_author']}\n For: {ticket['ticket_for']}")
                    embed.set_thumbnail(url=ticket["author_icon"])
                    embed.add_field(name="ID", value=ticket["ticket_id"])
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