"""
[Alpine Bot]
Copyright (C) 2021 - 2023 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import discord
from discord import ui
from discord.ui.select import BaseSelect

import utils
from core.context import ConfirmResult, ConfirmView
from utils import View as AView

if TYPE_CHECKING:
    from discord import Interaction

    from core import Context
    from utils import Database, GuildData, JoinLeaveData, LoggingData, VerificationData


class View(AView):
    embed: discord.Embed
    message: discord.Message

    @discord.ui.button(label="Go Home", row=4)
    async def home(self, itn: Interaction, _: ui.Button) -> None:
        view: SettingsView | None = getattr(self, "view", None)
        if view and isinstance(view, SettingsView):
            return await itn.response.edit_message(embed=view.embed, view=view)
        await itn.response.send_message("Can't go home for some reason.", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, row=4)
    async def close(self, itn: Interaction, _: ui.Button) -> None:
        await itn.response.defer()
        with contextlib.suppress(discord.HTTPException):
            await itn.delete_original_response()

    async def on_timeout(self) -> None:
        with contextlib.suppress(discord.HTTPException):
            await self.message.delete()

    def _set_state(self, state: bool) -> None:
        for item in self.children:
            if isinstance(item, (ui.Button, BaseSelect)):
                item.disabled = state
            if isinstance(item, ui.Button) and item.label in ("Go Home", "Close"):
                item.disabled = False


SettingsOptions: list[tuple[str, ...]] = [
    ("Prefixes", "Configure server prefixes"),
    ("Logging", "Configure logging"),
    ("Joins and Leaves", "Set member join/leave messages"),
    ("Member Verification", "Configure member verification"),
]


class SettingsSelect(ui.Select["SettingsView"]):
    def __init__(self, view: SettingsView) -> None:
        self.original_view: SettingsView = view
        self.current_view: View | None = None
        super().__init__(
            placeholder="Select a setting to configure...",
            options=[discord.SelectOption(label=label, description=description) for label, description in SettingsOptions],
        )

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        assert self.original_view is not None

        selected = self.values[0]
        if self.current_view:
            self.current_view.stop()
        view = self.original_view.get_view(selected)
        if view == self.current_view:
            return await itn.response.defer()
        self.current_view = view
        if not view:
            return await itn.response.send_message("Unknown error occurred. Try again.", ephemeral=True)
        await itn.response.edit_message(view=view, embed=view.embed)


class SettingsView(View):
    @property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title="Server Settings",
            description="Use the menu below to select a setting to edit.",
            color=self.ctx.get_color(),
        )

    def __init__(self, ctx: Context, database: Database, settings: GuildData) -> None:
        self.ctx: Context = ctx
        self.database: Database = database
        self.settings: GuildData = settings
        self.message: discord.Message | None = None
        super().__init__(member=ctx.author, timeout=120)
        self.remove_item(self.home)
        self.select = SettingsSelect(self)
        self.add_item(self.select)

    async def start(self, *, view: View | None = None):
        if view:
            self.select.current_view = view
            message = await self.ctx.send(embed=view.embed, view=view)
            view.message = message
            self.message = message
            return
        self.message = await self.ctx.send(embed=self.embed, view=self)

    def get_view(self, name: str) -> View | None:
        match name.lower():
            case "prefixes":
                return PrefixView(self.ctx, self)
            case "logging":
                return LoggingView(self.ctx, self)
            case "joins and leaves":
                return JoinsAndLeavesView(self.ctx, self)
            case "member verification":
                return MemberVerificationView(self.ctx, self)
            case "commands":
                return None  # CommandsView()


class PrefixAddModal(ui.Modal, title="Add a prefix"):
    prefix = ui.TextInput(label="New Prefix", style=discord.TextStyle.short, min_length=1, max_length=20)

    def __init__(self, view: PrefixView) -> None:
        self.view = view
        super().__init__(timeout=None)

    async def on_submit(self, itn: Interaction) -> None:
        prefix = self.prefix.value
        if not prefix:
            return await itn.response.send_message("Enter a prefix.", ephemeral=True)
        guild_prefixes = self.view.settings.prefixes

        if prefix in guild_prefixes:
            return await itn.response.send_message(f"`{prefix}` is already a prefix of this server.", ephemeral=True)

        guild_prefixes.append(prefix)
        await self.view.settings.update(prefixes=guild_prefixes)
        return await itn.response.send_message(f"Added {prefix} to the list of prefixes.", ephemeral=True)


class PrefixRemoveSelect(ui.Select["PrefixView"]):
    def __init__(self, settings: GuildData) -> None:
        self.settings: GuildData = settings
        options = [discord.SelectOption(label=prefix) for prefix in self.settings.prefixes]
        super().__init__(options=options, max_values=len(options))

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None

        for prefix in self.values:
            self.settings.prefixes.remove(prefix)
        await self.settings.update(prefixes=self.settings.prefixes)
        await itn.response.send_message(
            f"Removed {len(self.values)} prefixes:\n`{'` | `'.join(self.values)}`", ephemeral=True
        )


class PrefixView(View):
    @property
    def embed(self) -> discord.Embed:
        prefixes = self.settings.prefixes
        description = f"The prefixes are:\n`{'` | `'.join(prefixes)}`"
        if not prefixes:
            description = "There are no custom prefixes."
        elif len(prefixes) == 1:
            description = f"The prefix is `{prefixes[0]}`."
        return discord.Embed(
            title="Prefixes",
            description=f"{description}\n\nUse the buttons below to add or remove prefixes.",
            color=self.ctx.get_color(),
        )

    def __init__(self, ctx: Context, settings_view: SettingsView) -> None:
        self.view: SettingsView = settings_view
        self.message: discord.Message | None = settings_view.message
        self.settings: GuildData = settings_view.settings
        self.ctx: Context = ctx
        super().__init__(member=ctx.author)
        self._update()

    def _update(self):
        self.add_prefix.disabled = False
        self.remove_prefix.disabled = False

        if not self.settings.prefixes:
            self.remove_prefix.disabled = True
        if len(self.settings.prefixes) >= 35:
            self.add_prefix.disabled = True

    @ui.button(label="Add prefix", style=discord.ButtonStyle.green)
    async def add_prefix(self, itn: Interaction, _: ui.Button) -> None:
        assert self.message is not None

        if len(self.settings.prefixes) >= 35:
            return await itn.response.send_message(
                "This server has too many prefixes. Remove some first before adding more.", ephemeral=True
            )
        else:
            modal = PrefixAddModal(self)
            await itn.response.send_modal(modal)
            await modal.wait()
            self._update()
            await self.message.edit(embed=self.embed, view=self)

    @ui.button(label="Remove prefix", style=discord.ButtonStyle.red)
    async def remove_prefix(self, itn: Interaction, _: ui.Button) -> None:
        assert self.message is not None

        if not self.settings.prefixes:
            return await itn.response.send_message("There are no prefixes to remove.", ephemeral=True)
        view = AView(member=self.ctx.author)
        select = PrefixRemoveSelect(self.settings)
        view.add_item(select)
        await itn.response.send_message("Select prefixes to remove.", view=view, ephemeral=True)
        msg = await itn.original_response()
        await view.wait()
        view.stop()
        await msg.delete()
        self._update()
        await self.message.edit(embed=self.embed, view=self)


LoggingOptions: list[tuple[str, ...]] = [
    ("Message Delete", "message_delete", "Log when a message is deleted."),
    ("Message Edit", "message_edit", "Log when a message is edited."),
    ("Member Join", "member_join", "Log when a member joins the server."),
    ("Member Kick", "member_leave", "Log when a member is kicked the servers"),
    ("Member Ban", "member_ban", "Log when a member is banned from the server."),
    ("Channel Edit", "channel_edit", "Log when a channel is edited."),
    ("Channel Delete", "channel_delete", "Log when a channel is deleted."),
    ("Server Edit", "guild_edit", "Log when the server is edited."),
]

LoggingDefaults: dict[str, bool] = {
    "message_delete": False,
    "message_edit": False,
    "member_join": False,
    "member_leave": False,
    "member_ban": False,
    "channel_edit": False,
    "channel_delete": False,
    "guild_edit": False,
}


class LoggingSelect(ui.Select["LoggingView"]):
    def __init__(self, settings: GuildData) -> None:
        self.settings: GuildData = settings
        self.logging = settings.logging
        options = []
        if self.logging:
            for label, value, description in LoggingOptions:
                default = bool(self.logging._data.get(value))
                options.append(discord.SelectOption(label=label, value=value, description=description, default=default))
        super().__init__(placeholder="Select what to log...", min_values=0, max_values=len(options), options=options)

    def _update(self) -> None:
        if not self.logging:
            return
        for option in self.options:
            default = bool(self.logging._data.get(option.value))
            option.default = default

    async def callback(self, itn: Interaction) -> None:
        if not self.logging:
            self.logging = await self.settings.insert_logging()

        assert self.logging is not None

        values = self.values
        if not self.values:
            return await itn.response.send_message("Could not find values.", ephemeral=True)
        changed = LoggingDefaults.copy()
        changed.update({name: True for name in values})
        await self.logging.update(**changed)
        self._update()
        await itn.response.send_message("Sucessfully updated log list.", ephemeral=True)


class LoggingChannelSelect(ui.ChannelSelect["LoggingView"]):
    def __init__(self, ctx: Context, settings: GuildData) -> None:
        self.ctx: Context = ctx
        self.settings: GuildData = settings
        self.logging: LoggingData | None = settings.logging
        super().__init__(channel_types=[discord.ChannelType.text], placeholder="Select a channel to send logs to...")

    async def callback(self, itn: Interaction) -> None:
        await itn.response.defer(ephemeral=True, thinking=True)
        if not self.logging:
            self.logging = await self.settings.insert_logging()

        assert self.logging is not None

        channel = self.values[0].resolve()
        if not channel or not isinstance(channel, discord.TextChannel):
            return await itn.response.send_message("Could not find channel for some reason.", ephemeral=True)

        webhook = self.logging.webhook

        if webhook and webhook.channel_id == channel.id:
            return await itn.response.send_message(f"Logging channel is already set to {channel.mention}.", ephemeral=True)

        avatar = await self.ctx.bot.user.display_avatar.read()
        reason = f"{self.ctx.author}: set logging channel"

        if webhook:
            try:
                webhook = await webhook.fetch()
            except discord.HTTPException:
                webhook = None

        new_webhook: discord.Webhook | None
        if not webhook:
            new_webhook = await channel.create_webhook(name="Alpine Logs", avatar=avatar, reason=reason)
        else:
            new_webhook = await webhook.edit(name="Alpine Logs", avatar=avatar, reason=reason, channel=channel)

        await self.logging.update(webhook=new_webhook.url)
        await itn.followup.send(f"Successfully set logging channel to {channel.mention}")


class LoggingView(View):
    @property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title="Logging",
            description="This feature allows you to log actions that happen in your server.\n"
            "Use the buttons below to configure what you want to log, and what channel you want to send the logs to.",
            color=self.ctx.get_color(),
        )

    def __init__(self, ctx: Context, settings_view: SettingsView) -> None:
        self.ctx: Context = ctx
        self.view: SettingsView = settings_view
        self.message: discord.Message | None = settings_view.message
        self.settings: GuildData = settings_view.settings
        self.logging: LoggingData | None = settings_view.settings.logging
        super().__init__(member=ctx.author)
        self.add_item(LoggingChannelSelect(ctx, settings_view.settings))
        self.add_item(LoggingSelect(self.settings))
        self._update()

    def _update(self) -> None:
        logging = self.logging

        self._set_state(True)
        self.enable_disable.style = discord.ButtonStyle.green
        self.enable_disable.label = "Enable Logging"

        if not logging or logging.enabled:
            self._set_state(False)
            self.enable_disable.style = discord.ButtonStyle.red
            self.enable_disable.label = "Disable Logging"

        self.enable_disable.disabled = False

    @ui.button(label="Enable Logging", style=discord.ButtonStyle.green)
    async def enable_disable(self, itn: Interaction, _: ui.Button):
        if not self.settings.logging:
            self.logging = await self.settings.insert_logging()

        assert self.logging is not None

        state = self.logging.enabled
        await self.logging.update(enabled=not state)
        self._update()
        await itn.response.edit_message(view=self)


class JoinsAndLeavesMessageModal(ui.Modal):
    def __init__(self, view: JoinsAndLeavesView):
        self.view = view
        self.join_message: str | None = None
        self.leave_message: str | None = None
        title = "Edit join and leave messages"
        super().__init__(title=title)
        if not view.joins_and_leaves:
            return
        self.join_input = ui.TextInput(
            style=discord.TextStyle.long,
            label="Join message",
            placeholder="{member.mention} joined {server}! Now at {server.count} members!",
            default=view.joins_and_leaves.join_message,
            required=False,
        )
        self.leave_input = ui.TextInput(
            style=discord.TextStyle.long,
            label="Leave message",
            placeholder="Aww, {member.mention} left {server}... Now at {server.count} members.",
            default=view.joins_and_leaves.leave_message,
            required=False,
        )
        self.add_item(self.join_input)
        self.add_item(self.leave_input)

    async def on_submit(self, itn: Interaction) -> None:
        self.join_message = self.join_input.value
        self.leave_message = self.leave_input.value
        await itn.response.defer()


class JoinsAndLeavesChannelSelect(ui.ChannelSelect["JoinsAndLeavesView"]):
    def __init__(self, settings: GuildData) -> None:
        self.settings: GuildData = settings
        self.joins_and_leaves: JoinLeaveData | None = settings.join_leave
        super().__init__(channel_types=[discord.ChannelType.text], placeholder="Select a channel to send messages to...")

    async def callback(self, itn: Interaction) -> None:
        if not self.joins_and_leaves:
            self.joins_and_leaves = await self.settings.insert_join_leave()

        channel = self.values[0]
        join_leave = self.joins_and_leaves

        if channel.id == join_leave.channel_id:
            return await itn.response.send_message(f"Channel already set to {channel.mention}.", ephemeral=True)

        await join_leave.update(channel_id=channel.id)
        return await itn.response.send_message(f"Set channel to {channel.mention}.", ephemeral=True)


class JoinsAndLeavesView(View):
    @property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title="Joins and Leaves",
            description=(
                "This feature allows you to welcome or say goodbye to members in your server.\n\n"
                "Use the buttons below to configure join and leave messages."
            ),
            color=self.ctx.get_color(),
        )

    def __init__(self, ctx: Context, settings_view: SettingsView) -> None:
        self.ctx: Context = ctx
        self.view: SettingsView = settings_view
        self.message: discord.Message | None = settings_view.message
        self.settings: GuildData = settings_view.settings
        self.joins_and_leaves: JoinLeaveData | None = self.settings.join_leave
        super().__init__(member=ctx.author)
        self.channel_select: JoinsAndLeavesChannelSelect = JoinsAndLeavesChannelSelect(self.settings)
        self.add_item(self.channel_select)
        self._update()

    def _update(self) -> None:
        join_leave = self.joins_and_leaves

        self._set_state(False)
        self.enable_disable.style = discord.ButtonStyle.red
        self.enable_disable.label = "Disable Joins and Leaves"

        if not join_leave or join_leave and not join_leave.enabled:
            self._set_state(True)
            self.enable_disable.disabled = False
            self.enable_disable.style = discord.ButtonStyle.green
            self.enable_disable.label = "Enable Joins and Leaves"

    async def confirm(self, itn: Interaction, message: str) -> ConfirmResult:
        view = ConfirmView(member=self.ctx.author, timeout=300)
        view.yes.label = "Looks good!"
        view.no.label = "Try again."
        preview = await utils.preview_message(message, self.ctx)
        if isinstance(preview, discord.Embed):
            msg = await itn.followup.send(embed=preview, view=view, ephemeral=True, wait=True)
        else:
            msg = await itn.followup.send(preview, view=view, ephemeral=True, wait=True)
        await view.wait()
        return ConfirmResult(msg, view.value)

    @ui.button(label="Enable", style=discord.ButtonStyle.green)
    async def enable_disable(self, itn: Interaction, _: ui.Button) -> None:
        if not self.joins_and_leaves:
            self.joins_and_leaves = await self.settings.insert_join_leave()

        assert self.joins_and_leaves is not None
        state = self.joins_and_leaves.enabled
        await self.joins_and_leaves.update(enabled=not state)
        self._update()
        await itn.response.edit_message(view=self)

    @ui.button(label="Edit join and leave message")
    async def join_message(self, itn: Interaction, _: ui.Button) -> None:
        assert self.joins_and_leaves is not None
        assert self.message is not None

        modal = JoinsAndLeavesMessageModal(self)
        timeout = self.timeout
        self.timeout = None
        await itn.response.send_modal(modal)
        await modal.wait()
        self.timeout = timeout

        join_message: str | None = None
        leave_message: str | None = None
        if modal.join_message:
            join = await self.confirm(itn, modal.join_message)
            if join.result:
                join_message = modal.join_message
                await join.message.edit(content="Successfully set join message.", embed=None, view=None)
            else:
                await join.message.edit(content="Okay, join message was not set.", embed=None, view=None)
        else:
            await itn.followup.send("Disabled join message.", ephemeral=True)
        if modal.leave_message:
            leave = await self.confirm(itn, modal.leave_message)
            if leave.result:
                leave_message = modal.leave_message
                await leave.message.edit(content="Successfully set leave message.", embed=None, view=None)
            else:
                await leave.message.edit(content="Okay, leave message wasn't set.", embed=None, view=None)
        else:
            await itn.followup.send("Disabled leave message.", ephemeral=True)

        await self.joins_and_leaves.update(join_message=join_message, leave_message=leave_message)
        self._update()
        await self.message.edit(view=self)


class MemberVerificationChannelSelect(ui.ChannelSelect["MemberVerificationView"]):
    def __init__(self, settings: GuildData) -> None:
        self.settings: GuildData = settings
        self.verification = settings.verification
        super().__init__(
            channel_types=[discord.ChannelType.text], placeholder="Select a channel to use for member verification..."
        )

    async def callback(self, itn: Interaction) -> None:
        if not self.verification:
            self.verification = await self.settings.insert_verification()

        assert self.verification is not None

        channel = self.values[0]
        if channel.id == self.verification.channel_id:
            return await itn.response.send_message(
                f"Verification channel is already set to {channel.mention}.", ephemeral=True
            )

        await self.verification.update(channel_id=channel.id)
        return await itn.response.send_message(f"Verification channel set to {channel.mention}.", ephemeral=True)


class MemberVerificationRoleSelect(ui.RoleSelect["MemberVerificationView"]):
    def __init__(self, ctx: Context, settings: GuildData) -> None:
        self.ctx: Context = ctx
        self.settings: GuildData = settings
        self.verification = settings.verification
        super().__init__(placeholder="Select a role to use for member verification...")

    async def confirm(self, itn: Interaction) -> ConfirmResult:
        view = ConfirmView(member=self.ctx.author, timeout=300)
        view.yes.label = "I'm sure."
        view.yes.style = discord.ButtonStyle.red
        view.no.label = "No, nevermind."
        view.no.style = discord.ButtonStyle.gray
        msg = await itn.response.send_message(
            "This role has elevated permissions. Are you sure you want to give new members this role?",
            view=view,
            ephemeral=True,
        )
        msg = await itn.original_response()
        await view.wait()
        return ConfirmResult(msg, view.value)

    async def callback(self, itn: Interaction) -> None:
        if not self.verification:
            self.verification = await self.settings.insert_verification()

        assert self.verification is not None

        role = self.values[0]
        permissions = role.permissions
        if role.id == self.verification.role_id:
            return await itn.response.send_message(f"Verification role is already set to {role.mention}.", ephemeral=True)
        elif role >= self.ctx.me.top_role:
            return await itn.response.send_message(
                f"I can not give {role.mention} to members as it's higher than my role. Please select another role.",
                ephemeral=True,
            )
        elif (
            permissions.administrator
            or permissions.kick_members
            or permissions.ban_members
            or permissions.moderate_members
            or permissions.manage_guild
        ):
            confirm = await self.confirm(itn)
            if confirm.result:
                await self.verification.update(role_id=role.id)
                await confirm.message.edit(content=f"Okay, verification role set to {role.mention}", view=None)
                return
            await confirm.message.edit(
                content=f"Verification role was not set to {role.mention}. Please select another role.", view=None
            )
            return
        await self.verification.update(role_id=role.id)
        return await itn.response.send_message(f"Verification role set to {role.mention}.", ephemeral=True)


class MemberVerificationView(View):
    @property
    def embed(self) -> discord.Embed:
        return discord.Embed(
            title="Member Verification",
            description=(
                "This feature puts new members through a verification process to prevent raids early. "
                "This is recommended for servers that experience raids on a regular basis.\n\n"
                "Use the buttons below to configure verification."
            ),
            color=self.ctx.get_color(),
        )

    def __init__(self, ctx: Context, settings_view: SettingsView) -> None:
        self.ctx: Context = ctx
        self.view: SettingsView = settings_view
        self.message: discord.Message | None = settings_view.message
        self.settings: GuildData = settings_view.settings
        self.verification: VerificationData | None = settings_view.settings.verification
        super().__init__(member=ctx.author)
        self.channel_select = MemberVerificationChannelSelect(settings_view.settings)
        self.role_select = MemberVerificationRoleSelect(ctx, settings_view.settings)
        self.add_item(self.channel_select)
        self.add_item(self.role_select)
        self._update()

    def _update(self) -> None:
        verification = self.verification

        self._set_state(True)
        self.enable_disable.style = discord.ButtonStyle.green
        self.enable_disable.label = "Enable Member Verification"

        if not verification or verification.high:
            self._set_state(False)
            self.enable_disable.style = discord.ButtonStyle.red
            self.enable_disable.label = "Disable Member Verification"

        self.enable_disable.disabled = False

    @ui.button(label="Enable Member Verifiation", style=discord.ButtonStyle.green)
    async def enable_disable(self, itn: Interaction, _: ui.Button):
        if not self.settings.verification:
            self.verification = await self.settings.insert_verification()

        assert self.verification is not None

        state = self.verification.high
        await self.verification.update(high=not state)
        self._update()
        await itn.response.edit_message(view=self)
