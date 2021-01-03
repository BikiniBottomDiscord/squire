import discord
import random

from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def membercount(self, ctx):
        await ctx.send(ctx.guild.member_count)

    @commands.command()
    async def joinpos(self, ctx, member: discord.Member = None):
        member = member if member else ctx.author
        order = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        join_pos = order.index(member) + 1
        await ctx.send(join_pos)

    @commands.command()
    async def test(self, ctx):
        if random.randint(0, 1):
            await ctx.guild.me.edit(nick="Ol' Reliable")
            await ctx.send("Whoosh whoosh, on HostPls! <:bluejellyfish:479723952265232396> v1.1.0")
        else:
            await ctx.guild.me.edit(nick="Jellyfish")
            await ctx.send("Buzz Buzz, on HostPls! <:jellyfish:479723952890052608> v1.1.0")
        await ctx.guild.me.edit(nick=None)


def setup(bot):
    bot.add_cog(Misc(bot))
