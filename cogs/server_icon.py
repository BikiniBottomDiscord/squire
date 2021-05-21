import os
import random
import traceback

import discord

from discord.ext import commands, tasks


GUILD = 0
IMG_DIR = './data/server-icons'
PLAN_Z = 507429352720433152


def load_last_server_icon():
    with open('./data/last-server-icon.txt') as fp:
        return int(fp.read())


def set_last_server_icon(i):
    with open('./data/last-server-icon.txt', 'w') as fp:
        fp.write(str(i))


def find_file(i):
    images = os.listdir(IMG_DIR)
    for img_name in images:
        if img_name.startswith(str(i)):
            return f'{IMG_DIR}/{img_name}'
    return


def get_server_icon(current):
    return find_file(current + 1)


def shuffle_server_icons():
    names = list(range(len(os.listdir(IMG_DIR))))
    random.shuffle(names)

    for img_name in os.listdir(IMG_DIR):
        ext = img_name.split('.')[-1]
        os.rename(f'{IMG_DIR}/{img_name}', f'{IMG_DIR}/{names.pop()}.{ext}')


class ServerIcon(commands.Cog):
    """Automatic server icon rotation."""
    def __init__(self, bot):
        self.bot = bot
        self.last_server_icon = load_last_server_icon()
        # self.check_if_new_week.start()

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, commands.CheckFailure):
            await ctx.send(f"```py\n{error.__class__.__name__}: {error}\n```")

    async def rotate_server_icon(self):
        try:
            guild = self.bot.get_guild(GUILD)
            last = self.last_server_icon
            img_path = get_server_icon(last)
            with open(img_path) as fp:
                icon = fp.read()
            await guild.edit(icon=icon)
            self.last_server_icon += 1
            set_last_server_icon(self.last_server_icon)
            await self.log(f"Set server icon to `{img_path}`.")
        except Exception as e:
            error = ''.join(traceback.format_exception(e.__class__, e, e.__traceback__))
            await self.log(f"Error rotating server icon:```\n{error}\n```")

    async def log(self, msg):
        await self.bot.get_channel(PLAN_Z).send(msg)

    @tasks.loop(hours=1)
    async def check_if_new_week(self):
        # TODO
        pass

    @commands.group(invoke_without_command=True)
    async def icons(self, ctx):
        """Base command for controlling server icon."""
        current = find_file(self.last_server_icon)
        count = len(os.listdir(IMG_DIR))
        await ctx.send(f"Server icon is `{current}`. Found `{count} total images.`")

    @icons.command()
    async def shuffle(self, ctx):
        """Shuffle server icon names."""
        shuffle_server_icons()
        await ctx.send(f"Shuffled!```py\n{os.listdir(IMG_DIR)}```")

    @icons.command()
    async def rotate(self, ctx):
        """Rotate to the next server icon."""
        await self.rotate_server_icon()

    @icons.command()
    async def upload(self, ctx):
        """Add a new image to the icon folder."""
        count = len(os.listdir(IMG_DIR))
        attachment = ctx.message.attachments[0]
        ext = attachment.filename.split('.')[-1]
        filename = f"{IMG_DIR}/{count}.{ext}"
        await attachment.save(filename)
        await ctx.send(f"Saved as `{filename}`.")


def setup(bot):
    bot.add_cog(ServerIcon(bot))
