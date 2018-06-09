# coding=utf-8
"""Main bot file"""
import time
from collections import Counter
from pathlib import Path

import discord
from discord import DiscordException
from discord.ext import commands

from bot.utils.logging import setup_logger
from bot.utils.over import send


discord.abc.Messageable.send = send


class Bot(commands.AutoShardedBot):
    """Subclasses AutoShardedBot to give more flexibility with design"""

    def __init__(self, *args, **kwargs):
        self.config = kwargs.pop('config')
        self._start_time = time.time()
        self.app_info = None
        self.case_insensitive = True
        super().__init__(*args, **kwargs)
        shard = f"| Shard {self.shard_id}" if self.shard_id else ""
        self.activity = discord.Game(name=f"{self.command_prefix}help {shard}")
        self.commands_used = Counter()
        self.commands_used_in = Counter()

        discord_logger = setup_logger("discord")
        self.logger = setup_logger("Bot")
        self.command_logger = setup_logger("Commands")
        self.loggers = [discord_logger, self.logger, self.command_logger]

        _modules = [mod.stem for mod in Path("bot/cogs").glob("*.py")]
        self.load_extension(f"bot.cogs.core")
        self.load_extension(f"bot.cogs.errors")
        if 'bare' in kwargs.pop('argv'):  # load the bot bare-bones to diagnose issues
            return
        for module in _modules:
            try:
                if module in ['core', 'errors']:
                    pass
                self.load_extension(f"bot.cogs.{module}")
            except DiscordException as exc:
                self.logger.error(f"{type(exc).__name__} occurred when loading {module}: {exc}")

        # make sure to only print ready text once
        self._loaded = False

    async def on_ready(self):
        """Function called when bot is ready or resumed"""
        if self._loaded is False:
            end_time = time.time() - self._start_time
            self.app_info = await self.application_info()
            self.owner_id = self.app_info.owner.id
            self.logger.info(f"Loaded Bot:")
            self.logger.info(f"Logged in as {self.user}")
            self.logger.info(f"ID is {self.user.id}")
            self.logger.info(f"Owned by {self.app_info.owner}")
            self.description = f"Hello, this is the help menu for {self.user.name}!"
            self.logger.info(f"Bot started in {end_time} seconds")
            self._loaded = True
            return
        self.logger.info(f"Resumed bot session on shard {self.shard_id}!")

    async def close(self):
        """Function called when closing the bot"""
        await super().close()
        for logger in self.loggers:
            for handler in logger:
                logger.removeHandler(handler)
