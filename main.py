import discord
from discord.ext import commands
import asyncio
import logging
import os
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class AdvancedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.logger = logging.getLogger('AdvancedBot')
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        self.logger.info("Starting bot setup...")
        
        # Load all cogs/modules
        await self.load_extensions()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
        
        self.logger.info("Bot setup completed!")
    
    async def load_extensions(self):
        """Load all module files"""
        modules = [
            'cogs.moderation',
            'cogs.utility',
            'cogs.fun',
            'cogs.music',
            'cogs.economy',
            'cogs.admin'
        ]
        
        for module in modules:
            try:
                await self.load_extension(module)
                self.logger.info(f"Loaded {module}")
            except Exception as e:
                self.logger.error(f"Failed to load {module}: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        embed = discord.Embed(
            title="🤖 Bot Online",
            description=f"**{self.user.name}** is now online and ready!",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Servers", value=len(self.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.latency * 1000)}ms", inline=True)
        embed.set_thumbnail(url=self.user.avatar.url if self.user.avatar else None)
        
        self.logger.info(f"Bot is ready! Logged in as {self.user.name}")
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers"
            )
        )
    
    async def on_guild_join(self, guild):
        """Called when bot joins a guild"""
        embed = discord.Embed(
            title="🎉 Joined New Server!",
            description=f"Thanks for adding me to **{guild.name}**!",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Member Count", value=guild.member_count, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Try to find a general channel to send welcome message
        channel = None
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break
        
        if channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
        
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """Global error handler for prefix commands"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        embed = discord.Embed(
            title="❌ Command Error",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "I don't have the required permissions to execute this command."
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Missing required argument: `{error.param.name}`"
        elif isinstance(error, commands.BadArgument):
            embed.description = "Invalid argument provided."
        else:
            embed.description = "An unexpected error occurred."
            self.logger.error(f"Unexpected error in command {ctx.command}: {error}")
            self.logger.error(traceback.format_exc())
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass
    
    async def on_app_command_error(self, interaction, error):
        """Global error handler for slash commands"""
        embed = discord.Embed(
            title="❌ Command Error",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        
        if isinstance(error, discord.app_commands.MissingPermissions):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed.description = "I don't have the required permissions to execute this command."
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            embed.description = f"Command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        else:
            embed.description = "An unexpected error occurred."
            self.logger.error(f"Unexpected error in slash command: {error}")
            self.logger.error(traceback.format_exc())
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler for events"""
        self.logger.error(f"Error in event {event}: {traceback.format_exc()}")

# Utility functions for embeds
def create_embed(title=None, description=None, color=0x2f3136, author=None, thumbnail=None, image=None, footer=None, timestamp=None):
    """Create a standardized embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp or datetime.utcnow()
    )
    
    if author:
        embed.set_author(name=author.get('name'), icon_url=author.get('icon_url'), url=author.get('url'))
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if footer:
        embed.set_footer(text=footer.get('text'), icon_url=footer.get('icon_url'))
    
    return embed

def success_embed(title, description=None):
    """Create a success embed"""
    return create_embed(title=f"✅ {title}", description=description, color=0x00ff00)

def error_embed(title, description=None):
    """Create an error embed"""
    return create_embed(title=f"❌ {title}", description=description, color=0xff0000)

def warning_embed(title, description=None):
    """Create a warning embed"""
    return create_embed(title=f"⚠️ {title}", description=description, color=0xffaa00)

def info_embed(title, description=None):
    """Create an info embed"""
    return create_embed(title=f"ℹ️ {title}", description=description, color=0x0099ff)

# Run the bot
async def main():
    bot = AdvancedBot()
    
    # Load token from environment variable or config
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set!")
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
