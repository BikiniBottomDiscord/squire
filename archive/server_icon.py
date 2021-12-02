import os
import random
import traceback
import discord

from discord.ext import commands, tasks


GUILD = 384811165949231104
IMG_DIR = './data/server-icons'
PLAN_Z = 507429352720433152


def find_file(i):
    images = os.listdir(IMG_DIR)
    for img_name in images:
        if img_name.startswith(str(i)):
            return f'{IMG_DIR}/{img_name}'
    return


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
        # self.check_if_new_week.start()

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, commands.CheckFailure):
            await ctx.send(f"```py\n{error.__class__.__name__}: {error}\n```")

    async def rotate_server_icon(self):
        try:
            guild = self.bot.get_guild(GUILD)
            img = random.choice(os.listdir(IMG_DIR))
            img_path = f"{IMG_DIR}/{img}"
            with open(img_path, 'rb') as fp:
                icon = fp.read()
            await guild.edit(icon=icon)
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
        images = os.listdir(IMG_DIR)
        count = len(images)
        await ctx.send(f"Found `{count}` total images: ```py\n{images}\n```")

    @icons.command()
    async def rotate(self, ctx):
        """Rotate to the next server icon."""
        await self.rotate_server_icon()

    @icons.command()
    async def upload(self, ctx):
        """Add a new image to the icon folder."""
        attachment = ctx.message.attachments[0]
        filename = f"{IMG_DIR}/{attachment.filename}"
        await attachment.save(filename)
        await ctx.send(f"Saved as `{filename}`.")


def setup(bot):
    bot.add_cog(ServerIcon(bot))
