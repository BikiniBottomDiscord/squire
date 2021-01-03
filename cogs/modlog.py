
import discord
import json
import asyncio
import logging

from discord.ext import commands

from utils.db import Database


logger = logging.getLogger('cogs.modlog')


# class Infractions:
#     def __init__(self):
#         self.next_id = 1
#         self.by_infraction_id = {}
#         self.by_user_id = {}
#
#     def add_infraction(self, moderator_id, user_id, infraction_type, reason, message_id):
#         logger.debug(f"adding infraction {(self.next_id, moderator_id, user_id, infraction_type, reason, message_id)}")
#         infraction = {'moderator_id': moderator_id, 'user_id': user_id, 'infraction_id': self.next_id, 'infraction_type': infraction_type, 'reason': reason, 'message_id': message_id}
#         self.by_infraction_id[self.next_id] = infraction
#         if user_id in self.by_user_id.keys():
#             self.by_user_id[user_id][self.next_id] = infraction_type
#         else:
#             self.by_user_id[user_id] = {self.next_id: infraction_type}
#         self.next_id += 1
#
#     def get_infraction(self, infraction_id):
#         logger.debug(f"getting infraction {infraction_id}")
#         return self.by_infraction_id[infraction_id]
#
#     def edit_infraction(self, infraction_id, reason):
#         logger.debug(f"editing infraction {infraction_id} {reason}")
#         infraction = self.by_infraction_id[infraction_id]
#         # todo: edit in by_user without scanning
#         infraction['reason'] = reason
#
#     def get_infractions(self, user_id):
#         logger.debug(f"getting infractions for {user_id}")
#         return self.by_user_id[user_id]
#
#     def dump(self):
#         logger.debug("DUMPING INFRACTION DATA")
#         logger.debug(self.by_user_id)
#         logger.debug(self.by_infraction_id)
#         with open('data/infractions.json', 'w') as f:
#             json.dump([self.by_user_id, self.by_infraction_id], f)
#
#     def load(self):
#         logger.debug(f"LOADING INFRACTION DATA")
#         with open('data/infractions.json', 'r') as f:
#             self.by_user_id, by_infraction_id = json.load(f)
#         self.by_infraction_id = {}
#         for key, value in by_infraction_id.items():
#             self.by_infraction_id[int(key)] = value
#         self.next_id = len(self.by_infraction_id) + 1
#         logger.debug(self.by_user_id)
#         logger.debug(self.by_infraction_id)


class Modlog(commands.Cog):
    """Mod action log, utilizes audit logs."""

    def __init__(self, bot):
        self.bot = bot
        self.infractions = Database()
        self.logging_channel = 713467871040241744
        self.guild = 384811165949231104
        self.muted_role = 541810707386335234
        self.last_audit_id = 0

    async def log_kick(self, moderator, member, reason):
        content = f"<:howmanytimes:502338448951083020> **MEMBER KICKED (#{self.infractions.next_id})**\n**User:** {member} (`{member.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, member.id, 'kick', reason, message.id)

    async def log_ban(self, moderator, member, reason):
        content = f"<:ban:654576835224535080> **MEMBER BANNED (#{self.infractions.next_id})**\n**User:** {member} (`{member.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, member.id, 'ban', reason, message.id)

    async def log_forceban(self, moderator, user, reason):
        content = f"<:ban:654576835224535080> **USER FORCEBANNED (#{self.infractions.next_id})**\n**User:** {user} (`{user.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, user.id, 'forceban', reason, message.id)

    async def log_unban(self, moderator, user, reason):
        content = f"<:thankful:589318185183084554> **USER UNBANNED (#{self.infractions.next_id})**\n**User:** {user} (`{user.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, user.id, 'unban', reason, message.id)

    async def log_mute(self, moderator, member, reason):
        content = f"<:thenerve:783956406990405682> **MEMBER MUTED (#{self.infractions.next_id})**\n**User:** {member} (`{member.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, member.id, 'mute', reason, message.id)

    async def log_unmute(self, moderator, member, reason):
        content = f"<:patpog:718369341816700958> **MEMBER UNMUTED (#{self.infractions.next_id})**\n**User:** {member} (`{member.id}`)\n**Moderator:** {moderator}\n**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        self.infractions.add_infraction(moderator.id, member.id, 'unmute', reason, message.id)


    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if guild.id != self.guild:
            return

        logger.debug("ban detected")

        moderator = None
        reason = None

        await asyncio.sleep(2)

        async for entry in guild.audit_logs(limit=5):
            if entry.action == discord.AuditLogAction.ban and entry.target == user:
                logger.debug("audit log entry found")
                moderator = entry.user
                reason = entry.reason
                break

        if isinstance(user, discord.User):  # forceban
            logger.debug("it's a forceban")
            await self.log_forceban(moderator, user, reason)
        else:  # regular ban
            logger.debug("it's a regular ban")
            await self.log_ban(moderator, user, reason)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        if guild.id != self.guild:
            return

        logger.debug("possible kick detected")
        moderator = None
        reason = None

        await asyncio.sleep(2)

        async for entry in guild.audit_logs(limit=5):
            if entry.action == discord.AuditLogAction.kick and entry.target == member:
                logger.debug("audit log entry found, it's a kick. logging")
                moderator = entry.user
                reason = entry.reason
                break
            elif entry.action == discord.AuditLogAction.ban and entry.target == member:
                logger.debug("audit log entry found, it's a ban. ignoring")
                return

        if not moderator:
            logger.debug("no audit log entry found. member left the server.")
        else:
            await self.log_kick(moderator, member, reason)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = before.guild
        if guild.id != self.guild:
            return

        member = before
        moderator = None
        reason = None

        bad_noodle = guild.get_role(541810707386335234)

        await asyncio.sleep(2)

        if bad_noodle in before.roles and bad_noodle not in after.roles:  # unmute
            logger.debug("detected unmute")
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.member_role_update and bad_noodle in entry.before.roles and bad_noodle not in entry.after.roles:
                    if entry.id == self.last_audit_id:
                        return
                    self.last_audit_id = entry.id
                    logger.debug("unmute audit log entry found")
                    moderator = entry.user
                    reason = entry.reason
                    break
            await self.log_unmute(moderator, member, reason)

        elif bad_noodle in after.roles and bad_noodle not in before.roles:  # mute
            logger.debug("detected mute")
            async for entry in guild.audit_logs(limit=5):
                if entry.action == discord.AuditLogAction.member_role_update and bad_noodle in entry.after.roles and bad_noodle not in entry.before.roles:
                    if entry.id == self.last_audit_id:
                        return
                    self.last_audit_id = entry.id
                    logger.debug("mute audit log entry found")
                    moderator = entry.user
                    reason = entry.reason
                    break
            await self.log_mute(moderator, member, reason)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if guild.id != self.guild:
            return

        logger.debug("unban detected")
        moderator = None
        reason = None

        await asyncio.sleep(2)

        async for entry in guild.audit_logs(limit=5):
            if entry.action == discord.AuditLogAction.unban and entry.target == user:
                logger.debug("audit log entry found")
                moderator = entry.user
                reason = entry.reason
                break

        await self.log_unban(moderator, user, reason)


    @commands.group(aliases=['infraction', 'inf', 'i'], invoke_without_command=True)
    async def infractions(self, ctx):
        pass

    @infractions.command()
    async def listall(self, ctx):
        infractions = self.infractions
        await ctx.send("BY_USER_ID```json\n" + json.dumps(infractions.by_user_id, indent=4) + "\n```BY_INFRACTION_ID```json\n" + json.dumps(infractions.by_infraction_id, indent=4) + "\n```")

    @infractions.command()
    async def list(self, ctx, user: discord.Member):
        infractions = self.infractions.get_infractions(user.id)
        await ctx.send("```json\n" + json.dumps(infractions, indent=4) + "\n```")

    @infractions.command()
    async def info(self, ctx, infraction_id: int):
        infraction = self.infractions.get_infraction(infraction_id)
        await ctx.send("```json\n" + json.dumps(infraction, indent=4) + "\n```")

    @infractions.command()
    async def edit(self, ctx, infraction_id: int, *, new_reason):
        infraction = self.infractions.get_infraction(infraction_id)
        message = await self.bot.get_channel(self.logging_channel).fetch_message(infraction['message_id'])
        content = '\n'.join(message.content.split('\n')[:-1])
        content += f"\n**Reason:** {new_reason} (edited by {ctx.author})"
        await message.edit(content=content)
        await ctx.send(message.jump_url)


def setup(bot):
    bot.add_cog(Modlog(bot))

