
import discord
import json
import asyncio
import logging

from discord.ext import commands

from utils.db import Database


logger = logging.getLogger('cogs.modlog')


EMOJI_MUTE = "<hoopla:718369341162258482>"
EMOJI_KICK = "<howmanytimes:502338448951083020>"
EMOJI_BAN = "<:rage:642234025640984606>"
EMOJI_UNMUTE = "<:patpog:718369341816700958>"
EMOJI_UNBAN = "<:thankful:589318185183084554>"


class Modlog(commands.Cog):
    """Mod action log, utilizes audit logs."""

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.logging_channel = 713467871040241744
        self.guild = 384811165949231104
        self.muted_role = 541810707386335234
        self.last_audit_id = 0

    async def log_mute(self, moderator, member, reason):
        infraction_id = await self.db.new_infraction(moderator.id, member.id, 'mute', reason)
        content = f"{EMOJI_MUTE} **MEMBER MUTED (#{infraction_id})**\n" \
                  f"**User:** {member} (`{member.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

    async def log_kick(self, moderator, member, reason):
        infraction_id = await self.db.new_infraction(moderator.id, member.id, 'kick', reason)
        content = f"{EMOJI_KICK} **MEMBER KICKED (#{infraction_id})**\n" \
                  f"**User:** {member} (`{member.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

    async def log_ban(self, moderator, member, reason):
        infraction_id = await self.db.new_infraction(moderator.id, member.id, 'ban', reason)
        content = f"{EMOJI_BAN} **MEMBER BANNED (#{infraction_id})**\n" \
                  f"**User:** {member} (`{member.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

    async def log_forceban(self, moderator, user, reason):
        infraction_id = await self.db.new_infraction(moderator.id, user.id, 'ban', reason)
        content = f"{EMOJI_BAN} **USER FORCEBANNED (#{infraction_id})**\n" \
                  f"**User:** {user} (`{user.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

    async def log_unmute(self, moderator, member, reason):
        infraction_id = await self.db.new_infraction(moderator.id, member.id, 'unmute', reason)
        content = f"{EMOJI_UNMUTE} **MEMBER UNMUTED (#{infraction_id})**\n" \
                  f"**User:** {member} (`{member.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

    async def log_unban(self, moderator, user, reason):
        infraction_id = await self.db.new_infraction(moderator.id, user.id, 'unban', reason)
        content = f"{EMOJI_UNBAN} **USER UNBANNED (#{infraction_id})**\n" \
                  f"**User:** {user} (`{user.id}`)\n" \
                  f"**Moderator:** {moderator}\n" \
                  f"**Reason:** {reason}"
        message = await self.bot.get_channel(self.logging_channel).send(content)
        await self.db.set_message_id(infraction_id, message.id)

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
    async def list(self, ctx, user: discord.Member):
        infractions = self.infractions.get_history(user.id)
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

