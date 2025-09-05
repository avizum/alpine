"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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

import json
from typing import ClassVar, Final, TYPE_CHECKING

import discord
from discord import ChannelType, SelectOption, ui
from discord.ext import commands
from discord.ui.select import BaseSelect

import utils
from core.context import ConfirmView
from utils import LayoutView as LView

from .converters import GetCommand

if TYPE_CHECKING:
    from core import Bot, Context
    from utils import Database, GuildData, JoinLeaveData, LoggingData, VerificationData

    from .cog import Settings as SettingsCog


type Interaction = discord.Interaction[Bot]
type Containers = (
    HomeContainer | PrefixContainer | LoggingContainer | JoinLeaveContainer | VerificationContainer | CommandsContainer
)
type ContainerInstances = tuple[
    HomeContainer, PrefixContainer, LoggingContainer, JoinLeaveContainer, VerificationContainer, CommandsContainer
]


class HomeOrCloseAction(ui.ActionRow["SettingsView"]):
    @ui.button(label="Home", id=466301)
    async def home(self, itn: Interaction, _: ui.Button) -> None:
        assert self.view is not None

        await self.view.show_container(itn, container=0)

    @ui.button(label="Close", style=discord.ButtonStyle.red, id=466302)
    async def close(self, itn: Interaction, _: ui.Button) -> None:
        await itn.response.defer()
        try:
            await itn.delete_original_response()
        except discord.HTTPException:
            pass

        if self.view:
            self.view.stop()

    def update(self) -> None:
        assert self.view is not None

        self.clear_items()
        if self.view.container != self.view._containers[0]:
            self.add_item(self.home)
        self.add_item(self.close)


class SettingsContainer(ui.Container["SettingsView"]):
    no_update: ClassVar[bool] = False

    def __init__(self, data: GuildData, /, *, accent_color: discord.Color | int | None) -> None:
        self.data: GuildData = data
        super().__init__(accent_color=accent_color)

    def update(self) -> None: ...


class SettingsView(LView):
    def __init__(self, ctx: Context, cog: SettingsCog, data: GuildData) -> None:
        color = ctx.get_color()
        self.delete_message_after = True
        self._containers: tuple[SettingsContainer, ...] = (
            HomeContainer(data, accent_color=color),
            PrefixContainer(data, accent_color=color),
            LoggingContainer(data, accent_color=color),
            JoinLeaveContainer(data, accent_color=color),
            VerificationContainer(data, accent_color=color),
            CommandsContainer(data, accent_color=color),
        )

        self.container: SettingsContainer = self._containers[0]
        self.home_close: HomeOrCloseAction = HomeOrCloseAction(id=4663)
        self.container.add_item(self.home_close)

        self.ctx: Context = ctx
        self.cog: SettingsCog = cog
        self.database: Database = ctx.database
        self.data: GuildData = data
        self.message: discord.Message | None = None

        super().__init__(member=ctx.author, timeout=None)
        self.add_item(self.container)

    async def start(self, /, *, container: SettingsContainer | int | None = None):
        self.cog._settings[self.ctx.guild.id] = self
        self._prepare_container(container or self._containers[0])
        self.message = await self.ctx.send(view=self)

    def stop(self) -> None:
        self.cog._settings.pop(self.ctx.guild.id, None)
        return super().stop()

    def _prepare_container(self, container: SettingsContainer | int) -> None:
        if isinstance(container, int):
            container = self._containers[container]

        if self.container:
            self.remove_item(self.container)

        cont_home = container.find_item(4663)

        if cont_home is None:
            container.add_item(self.home_close)
        self.container = container
        self.add_item(container)
        self.home_close.update()

        if not container.no_update:
            self.container.update()

    async def show_container(self, itn: Interaction | None = None, /, *, container: SettingsContainer | int) -> None:
        self._prepare_container(container)

        if itn:
            await itn.response.edit_message(view=self)
            return

        if self.message:
            await self.message.edit(view=self)
            return

    def set_state(self, /, *, disabled: bool) -> None:
        for child in self.walk_children():
            if isinstance(child, (ui.Button, BaseSelect)) and child.id not in (466301, 466302):
                child.disabled = disabled


class SettingsSelect(ui.Select[SettingsView]):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Select a setting to configure...",
            options=[
                SelectOption(label="Prefixes", value="1", description="Change Alpine's command prefixes."),
                SelectOption(label="Logging", value="2", description="Configure logging for messages, members and more"),
                SelectOption(label="Joins and Leaves", value="3", description="Set up messages for member joins or leaves"),
                SelectOption(label="Member Verification", value="4", description="Settings for verifying new members."),
                SelectOption(label="Commands", value="5", description="Configure Alpine's commands for this server."),
            ],
        )

    async def callback(self, itn: Interaction):
        assert self.view is not None
        await self.view.show_container(itn, container=int(self.values[0]))


class HomeContainer(SettingsContainer):
    title = ui.TextDisplay("### Server Settings")
    description = ui.TextDisplay("Select a setting to edit from the dropdown.")
    separator = ui.Separator()
    settings_select = ui.ActionRow(SettingsSelect())


class PrefixAddButton(ui.Button[SettingsView]):
    async def callback(self, itn: Interaction):
        assert self.view is not None
        assert self.view.message is not None
        assert isinstance(self.view.container, PrefixContainer)

        prefixes = self.view.data.prefixes

        if len(prefixes) >= 10:
            await itn.response.send_message(
                "There can only be 10 command prefixes. Remove some before adding more.",
                ephemeral=True,
            )
            return

        modal = PrefixAddModal(self.view.container)
        await itn.response.send_modal(modal)
        await modal.wait()


class PrefixAddModal(ui.Modal, title="Add a prefix"):
    prefix = ui.TextInput(label="New Prefix", style=discord.TextStyle.short, min_length=1, max_length=20)

    def __init__(self, container: PrefixContainer) -> None:
        self.container: PrefixContainer = container
        super().__init__()

    async def on_submit(self, itn: Interaction) -> None:
        prefix = self.prefix.value
        if not prefix:
            await itn.response.send_message("Enter a prefix", ephemeral=True)
            return

        prefixes = self.container.data.prefixes

        if prefix in prefixes:
            await itn.response.send_message(f"`{prefix}` is already a prefix of this server.", ephemeral=True)
            return

        prefixes.append(prefix)
        await self.container.data.update(prefixes=prefixes)
        self.container.update()
        await itn.response.edit_message(view=self.container.view)
        return


class PrefixRemoveSelect(ui.Select[SettingsView]):
    def __init__(self) -> None:
        super().__init__(placeholder="Select a prefix to remove...")

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        assert isinstance(self.view.container, PrefixContainer)
        container: PrefixContainer = self.view.container

        for prefix in self.values:
            container.data.prefixes.remove(prefix)
        await container.data.update(prefixes=container.data.prefixes)

        container.update()
        await itn.response.edit_message(view=self.view)


class PrefixContainer(SettingsContainer):
    title = ui.TextDisplay("### Command Prefix Settings")
    description = ui.TextDisplay("Manage the server's command prefixes here.\nPrefixes do not apply to slash commands.")
    separator = ui.Separator()
    section = ui.Section(accessory=PrefixAddButton(label="Add Prefix", style=discord.ButtonStyle.green))
    select_action = ui.ActionRow()

    def __init__(self, data: GuildData, /, *, accent_color: discord.Color | None = None):
        super().__init__(data, accent_color=accent_color)
        self.select: PrefixRemoveSelect = PrefixRemoveSelect()
        self.select_action.add_item(self.select)

    def update(self) -> None:
        assert isinstance(self.section.accessory, PrefixAddButton)
        add_prefix = self.section.accessory

        prefixes = self.data.prefixes
        description = f"`{'` | `'.join(prefixes)}`"
        if not prefixes:
            description = "There are no custom prefixes. The default prefix is `a.`"
        elif len(prefixes) == 1:
            description = f"The prefix is `{prefixes[0]}`"

        self.section.clear_items()
        self.section.add_item("**Prefixes**")
        self.section.add_item(description)

        add_prefix.disabled = False
        self.select.disabled = False

        self.select.options = [discord.SelectOption(label=prefix) for prefix in self.data.prefixes] or [
            discord.SelectOption(label="Prefix")
        ]
        if not prefixes:
            self.select.disabled = True
        self.select.max_values = len(self.select.options)

        if len(prefixes) >= 10:
            add_prefix.disabled = True


class ConfirmNewSettingsMenu(ui.View):
    def __init__(self, /, *, menu: SettingsView, ctx: Context, cog: SettingsCog) -> None:
        super().__init__(timeout=(12 * 60 * 60))  # 12 hours obviously
        assert menu.message is not None
        self.menu: SettingsView = menu
        self.ctx: Context = ctx
        self.cog: SettingsCog = cog
        self.value: bool | None = None
        self.add_item(ui.Button(label="Jump to menu", url=menu.message.jump_url))

    @ui.button(label="Open new menu", style=discord.ButtonStyle.primary)
    async def close_menu(self, itn: Interaction, button: ui.Button) -> None:
        await itn.response.defer()
        menu = self.cog._settings.get(self.ctx.guild.id)

        if menu:
            menu.stop()
            if menu.message:
                try:
                    await menu.message.delete()
                except discord.HTTPException:
                    pass
        view = SettingsView(self.menu.ctx, self.cog, self.menu.data)
        await view.start()

        try:
            await itn.delete_original_response()
        except discord.HTTPException:
            pass


LOGGING_OPTIONS: Final[list[tuple[str, ...]]] = [
    ("Message Delete", "message_delete", "Log when a message is deleted."),
    ("Message Edit", "message_edit", "Log when a message is edited."),
    ("Member Join", "member_join", "Log when a member joins the server."),
    ("Member Kick", "member_leave", "Log when a member is kicked the servers"),
    ("Member Ban", "member_ban", "Log when a member is banned from the server."),
    ("Channel Edit", "channel_edit", "Log when a channel is edited."),
    ("Channel Delete", "channel_delete", "Log when a channel is deleted."),
    ("Server Edit", "guild_edit", "Log when the server is edited."),
]


LOGGING_DEFAULTS: Final[dict[str, bool]] = {
    "message_delete": False,
    "message_edit": False,
    "member_join": False,
    "member_leave": False,
    "member_ban": False,
    "channel_edit": False,
    "channel_delete": False,
    "guild_edit": False,
}


class LoggingChannelSelect(ui.ChannelSelect[SettingsView]):
    def __init__(self, container: LoggingContainer) -> None:
        self.container: LoggingContainer = container
        if container.data.logging and container.data.logging.channel_id:
            defaults = [discord.Object(container.data.logging.channel_id)]
        else:
            defaults = []
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Select a channel to send logs to...",
            default_values=defaults,
        )

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        await itn.response.defer(ephemeral=True, thinking=True)
        logging = self.container.data.logging
        if not logging:
            logging = await self.container.data.insert_logging()

        channel = self.values[0].resolve()
        if not channel or not isinstance(channel, discord.TextChannel):
            await itn.followup.send("Could not find channel for some reason.", ephemeral=True)
            return

        webhook: discord.Webhook | None = logging.webhook
        ctx: Context = self.view.ctx

        if webhook and logging.channel_id == channel.id:
            await itn.followup.send(f"Logging channel is already set to {channel.mention}.", ephemeral=True)
            return

        if not channel.permissions_for(ctx.me).manage_webhooks:
            await itn.followup.send(f"I do not have permissions to create webhooks in {channel.mention}.", ephemeral=True)
            return

        avatar = await ctx.me.display_avatar.read()
        reason = f"{itn.user}: set logging channel"

        try:
            assert webhook is not None
            await webhook.edit(name="Alpine Logs", avatar=avatar, reason=reason, channel=channel)
        except (discord.HTTPException, AssertionError):
            webhook = await channel.create_webhook(name="Alpine Logs", avatar=avatar, reason=reason)

        await logging.update(webhook=webhook.url, channel_id=channel.id)
        await itn.followup.send(f"Sucessfully set logging channel to {channel.mention}")


class LoggingTypesSelect(ui.Select[SettingsView]):
    def __init__(self, container: LoggingContainer) -> None:
        self.container: LoggingContainer = container
        options = [
            discord.SelectOption(label=label, value=value, description=description)
            for label, value, description in LOGGING_OPTIONS
        ]
        super().__init__(placeholder="Select what to log...", options=options, min_values=0, max_values=len(options))

    def update(self) -> None:
        logging = self.container.data.logging

        if not logging:
            return

        for option in self.options:
            default = bool(logging._data.get(option.value))
            option.default = default

    async def callback(self, itn: Interaction):
        logging = self.container.data.logging
        if not logging:
            logging = await self.container.data.insert_logging()

        values = self.values

        changed = LOGGING_DEFAULTS.copy()
        changed.update(dict.fromkeys(values, True))
        await logging.update(**changed)  # type: ignore
        self.update()
        await itn.response.send_message("Successfully updated log list.", ephemeral=True)


class LoggingToggleButton(ui.Button[SettingsView]):
    async def callback(self, itn: Interaction):
        assert self.view is not None
        assert isinstance(self.view.container, LoggingContainer)

        logging: LoggingData | None = self.view.container.logging
        if not logging:
            logging = await self.view.container.data.insert_logging()

        state = logging.enabled
        await logging.update(enabled=not state)
        self.view.container.update()
        await itn.response.edit_message(view=self.view)


class LoggingContainer(SettingsContainer):
    title = ui.Section("### Logging Settings", accessory=LoggingToggleButton())
    description = ui.TextDisplay("This feature allows you to log actions that happen in your server.")
    desc_separator = ui.Separator()
    channel_text = ui.TextDisplay("**Logging Channel**")
    channel = ui.ActionRow()
    channel_separator = ui.Separator()
    options_text = ui.TextDisplay("**Logging Options**")
    options = ui.ActionRow()

    def __init__(self, data: GuildData, /, *, accent_color: discord.Color | None = None) -> None:
        self.logging: LoggingData | None = data.logging
        super().__init__(data, accent_color=accent_color)
        self.channel.add_item(LoggingChannelSelect(self))
        self.logging_select = LoggingTypesSelect(self)
        self.options.add_item(self.logging_select)

    def update(self) -> None:
        assert self.view is not None
        assert isinstance(self.title.accessory, LoggingToggleButton)

        logging_toggle = self.title.accessory

        self.view.set_state(disabled=False)
        logging_toggle.style = discord.ButtonStyle.red
        logging_toggle.label = "Disable Feature"

        if not self.logging or not self.logging.enabled:
            self.view.set_state(disabled=True)
            logging_toggle.style = discord.ButtonStyle.green
            logging_toggle.label = "Enable Feature"

        logging_toggle.disabled = False
        self.logging_select.update()


class JLMessageModal(ui.Modal):
    def __init__(self, container: JoinLeaveContainer, join: bool = True):
        assert container.data.join_leave is not None

        self.container: JoinLeaveContainer = container
        join_leave: JoinLeaveData | None = container.data.join_leave
        self.output: str

        title = "Set Join Message"
        label = "Join Message"
        placeholder = "{member.mention} joined {server}! Now at {server.count} members!"
        default = join_leave.join_message

        if not join:
            title = "Set Leave Message"
            label = "Leave Message"
            placeholder = "Aww, {member.mention} left {server}... Now at {server.count} members."
            default = join_leave.leave_message

        super().__init__(title=title)

        self.label = ui.Label(
            text=label,
            description="Enter a message. You can leave this blank to disable this.",
            component=ui.TextInput(
                style=discord.TextStyle.long,
                placeholder=placeholder,
                default=default,
                required=False,
            ),
        )

        self.add_item(self.label)

    async def on_submit(self, itn: Interaction) -> None:
        assert isinstance(self.label.component, ui.TextInput)
        self.output = self.label.component.value
        await itn.response.defer()


class JLChannelSelect(ui.ChannelSelect[SettingsView]):
    def __init__(self, container: JoinLeaveContainer) -> None:
        self.data: GuildData = container.data
        default = (
            [discord.Object(self.data.join_leave.channel_id)]
            if self.data.join_leave and self.data.join_leave.channel_id
            else []
        )
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Select a channel to send messages to...",
            default_values=default,
        )

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None

        join_leave = self.data.join_leave

        if not join_leave:
            join_leave = await self.data.insert_join_leave()

        channel = self.values[0].resolve()
        if not channel:
            await itn.response.send_message("The channel you selected is not available for some reason.")
            return

        if not channel.permissions_for(self.view.ctx.me) >= discord.Permissions(send_messages=True, embed_links=True):
            await itn.response.send_message(
                f"I need the `Send Messages` and `Embed Links` permissions in {channel.mention}.", ephemeral=True
            )
            return

        if channel.id == join_leave.channel_id:
            await itn.response.send_message(f"Channel is already set to {channel.mention}.", ephemeral=True)
            return

        await join_leave.update(channel_id=channel.id)
        await itn.response.send_message(f"Set channel to {channel.mention}.", ephemeral=True)
        return


class JLEditButton(ui.Button[SettingsView]):
    def __init__(self, *, join: bool = False):
        self.join: bool = join
        _id = 28601 if join else 28602

        super().__init__(style=discord.ButtonStyle.blurple, label="Edit", id=_id)

    def convert_message(self, message: str) -> str:
        try:
            load = json.loads(message)
            embeds_key = load.get("embeds")
            if embeds_key:
                load = embeds_key[0]
            if not any(key in load for key in ["title", "description", "fields", "author", "footer", "image", "thumbnail"]):
                raise ValueError(
                    "The embed code you entered is invalid. It needs to include one of the following:\n"
                    "A title, description, fields, author, footer, image, or thumbnail."
                )
        except json.JSONDecodeError:
            return message
        else:
            return json.dumps(load)

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        assert self.view.message is not None
        assert isinstance(self.view.container, JoinLeaveContainer)

        modal = JLMessageModal(self.view.container, join=self.join)
        await itn.response.send_modal(modal)
        await modal.wait()

        assert self.view.container.data.join_leave is not None
        join_leave: JoinLeaveData = self.view.container.data.join_leave

        if self.join:
            join_message: str | None = join_leave.join_message

            if modal.output and modal.output != join_message:
                try:
                    join_message = self.convert_message(modal.output)
                except ValueError as exc:
                    await itn.followup.send(str(exc), ephemeral=True)
                    return
            elif not modal.output:
                join_message = None
                await itn.followup.send("Disabled join message.", ephemeral=True)

            await join_leave.update(join_message=join_message)

        else:
            leave_message: str | None = join_leave.leave_message

            if modal.output and modal.output != leave_message:
                try:
                    leave_message = self.convert_message(modal.output)
                except ValueError as exc:
                    await itn.followup.send(str(exc), ephemeral=True)
                    return

            elif not modal.output:
                leave_message = None
                await itn.followup.send("Disabled leave message.", ephemeral=True)

            await join_leave.update(leave_message=leave_message)

        self.view.container.update()
        await self.view.message.edit(view=self.view)


class JLToggleButton(ui.Button[SettingsView]):
    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        assert isinstance(self.view.container, JoinLeaveContainer)

        join_leave: JoinLeaveData | None = self.view.container.data.join_leave

        if not join_leave:
            join_leave = await self.view.container.data.insert_join_leave()

        state = join_leave.enabled

        await join_leave.update(enabled=not state)
        self.view.container.update()
        await itn.response.edit_message(view=self.view)


class JLTestButton(ui.Button[SettingsView]):
    def __init__(self, /, *, join: bool) -> None:
        self.join: bool = join
        super().__init__(label=f"Test {"Join" if join else "Leave"} Message")

    async def callback(self, itn: Interaction) -> None:
        assert self.view is not None
        assert isinstance(self.view.container, JoinLeaveContainer)

        rate = self.view.container.cooldown.update_rate_limit(self)
        if rate:
            await itn.response.send_message(f"Slow down. Try again in {rate:.2f}s.", ephemeral=True)
            return
        dispatch = "test_member_join" if self.join else "test_member_remove"
        self.view.ctx.bot.dispatch(dispatch, itn.user)
        await itn.response.send_message("Sent test message.", ephemeral=True)


class JoinLeaveContainer(SettingsContainer):

    title = ui.Section(
        "### Join and Leave Message Settings",
        "This feature allows you to say hello or goodbye to members in your server.",
        accessory=JLToggleButton(),
    )
    separator = ui.Separator()
    join_message = ui.Section(accessory=JLEditButton(join=True))
    leave_message = ui.Section(accessory=JLEditButton(join=False))
    channel = ui.TextDisplay("**Message Destination Channel**")
    channel_select = ui.ActionRow()
    large_sepatator = ui.Separator(spacing=discord.SeparatorSpacing.large)
    test_action = ui.ActionRow()

    def __init__(self, data: GuildData, /, *, accent_color: discord.Color | None = None) -> None:
        self.join_leave: JoinLeaveData | None = data.join_leave
        self.test_join_message: JLTestButton = JLTestButton(join=True)
        self.test_leave_message: JLTestButton = JLTestButton(join=False)
        super().__init__(data, accent_color=accent_color)
        self.add_items()
        self.cooldown: commands.CooldownMapping = commands.CooldownMapping.from_cooldown(1, 15, lambda btn: btn.custom_id)

    def add_items(self) -> None:
        self.channel_select.add_item(JLChannelSelect(self))
        self.test_action.add_item(self.test_join_message)
        self.test_action.add_item(self.test_leave_message)

    def _update_preview_section(
        self,
        action: str,
        feature_disabled: bool,
        section: ui.Section,
        message: str | None,
        button: JLTestButton,
    ) -> None:
        assert self.view is not None
        assert isinstance(self.title.accessory, JLToggleButton)
        assert isinstance(section.accessory, JLEditButton)

        section.clear_items()
        section.add_item(f"**{action} Message**")
        if message and not feature_disabled:
            preview = utils.preview_message(message, self.view.ctx)
            if isinstance(preview, discord.Embed):
                preview = "*Embed*\n-# Press the test button to see preview."
            section.accessory.label = "Edit"
            section.accessory.style = discord.ButtonStyle.blurple
            section.add_item(f">>> {preview}")
            button.disabled = False
        else:
            section.accessory.label = f"Add {action} Message"
            section.accessory.style = discord.ButtonStyle.green
            section.add_item("-# *Feature is disabled*" if feature_disabled else "> *No message set*")
            button.disabled = True

    def update(self):
        assert self.view is not None
        assert isinstance(self.title.accessory, JLToggleButton)
        assert isinstance(self.join_message.accessory, JLEditButton)
        assert isinstance(self.leave_message.accessory, JLEditButton)

        self.view.set_state(disabled=False)
        self.title.accessory.style = discord.ButtonStyle.red
        self.title.accessory.label = "Disable Feature"
        self.test_join_message.disabled = False
        self.test_leave_message.disabled = False

        feature_disabled: bool = not self.join_leave or not self.join_leave.enabled
        if feature_disabled:
            self.view.set_state(disabled=True)
            self.title.accessory.style = discord.ButtonStyle.green
            self.title.accessory.label = "Enable Feature"
            self.title.accessory.disabled = False

        join_message = self.join_leave.join_message if self.join_leave else None
        leave_message = self.join_leave.leave_message if self.join_leave else None

        self._update_preview_section("Join", feature_disabled, self.join_message, join_message, self.test_join_message)
        self._update_preview_section("Leave", feature_disabled, self.leave_message, leave_message, self.test_leave_message)

    @test_action.button(label="Help")
    async def help_button(self, itn: discord.Interaction, _: ui.Button):
        container = ui.Container(
            ui.TextDisplay(
                "### Join and Leave Message Help\n"
                "You can customize the join or leave messages however you like. "
                "Use the variables below to personalize your message. "
                "These variables also work when creating an embed using an "
                "[embed builder](https://message.style/app/editor). Just input the JSON code.\n"
                "- -# Note: When using embeds, you can only send one embed. If you input multiple embeds, "
                "the first embed will be saved, and the rest will be discarded."
            ),
            ui.TextDisplay(
                "**Member Variables**\n"
                "- `mention`: Shows a member's mention. Using this will ping a member.\n"
                "  - -# **Example**: {member.mention}, please introduce yourself.\n"
                "- `name`: Shows the member's username.\n"
                "  - -# **Example**: {member.name} is here.\n"
                "- `display_name`: Shows the member's display name.\n"
                "  - -# **Example**: {member.display_name} joined the server.\n"
                "- `nick_name` or `nick`: Shows the member's nick name or display name.\n"
                "  - -# **Example**: {member.name} AKA {member.nick_name} left.\n"
                "- `avatar` or `image` or `pfp` or `icon`: Returns a URL of the member's avatar.\n"
                "  - -# **Example**: Here is {member}'s  profile picture: {member.avatar}\n"
                "- `display_avatar` or `display_image` or `display_pfp` or `display_icon`: "
                "Returns a URL of the member's server avatar.\n"
                "  - -# **Example**: Here is {member}'s  server profile picture: {member.display_avatar}\n"
                "- `id`: Shows the member's user id.\n"
                "  - -# **Example**: A new member with ID {member.id} joined."
            ),
            ui.TextDisplay(
                "**Server Variables**\n"
                "Guild is an alias for server.\n"
                "- `name`: Shows the server's name.\n"
                "  - -# **Example**: {server.name} just gained a new member.\n"
                "- `member_count` or `count`: Shows the server's member count.\n"
                "  - -# **Example**: Someone left, there are now {server.member_count} people here.\n"
                "- `icon` or `image` or `picture`: Shows the server's icon if there is one.\n"
                "  - -# **Example**: {server.icon} This is an icon."
            ),
        )
        view = ui.LayoutView()
        view.add_item(container)
        await itn.response.send_message(view=view, ephemeral=True)


class VerificationToggle(ui.Button[SettingsView]):
    async def callback(self, itn: Interaction):
        assert self.view is not None
        assert isinstance(self.view.container, VerificationContainer)

        verification: VerificationData | None = self.view.container.verification
        if not verification:
            verification = await self.view.container.data.insert_verification()

        state = verification.high
        await verification.update(high=not state)
        self.view.container.update()
        await itn.response.edit_message(view=self.view)


class VerificationContainer(SettingsContainer):
    section = ui.Section(
        "### Member Verification Settings",
        (
            "This feature puts new members through a verification process to prevent raids early. "
            "This is recommended for servers that experience raids on a regular basis."
        ),
        accessory=VerificationToggle(),
    )
    desc_sepatator = ui.Separator()
    verification_channel = ui.TextDisplay("**Verification Channel**")
    channel_action = ui.ActionRow()
    channel_description = ui.TextDisplay("-# This channel will be used to send and receive verification messages.")
    channel_separator = ui.Separator()
    verification_role = ui.TextDisplay("**Verification Role**")
    role_action = ui.ActionRow()
    role_description = ui.TextDisplay("-# Once the verification process is complete, a member will be assigned this role.")

    def __init__(self, data: GuildData, /, *, accent_color: discord.Color | int | None) -> None:
        super().__init__(data, accent_color=accent_color)
        self.verification: VerificationData | None = data.verification

    def update(self) -> None:
        assert self.view is not None
        assert isinstance(self.section.accessory, VerificationToggle)

        toggle = self.section.accessory
        verification = self.verification

        self.view.set_state(disabled=True)
        toggle.style = discord.ButtonStyle.green
        toggle.label = "Enable Feature"

        if verification:
            self.channel_select.default_values = [discord.Object(verification.channel_id)]
            self.role_select.default_values = [discord.Object(id=verification.role_id)]

        if not verification or verification.high:
            self.view.set_state(disabled=False)
            toggle.style = discord.ButtonStyle.red
            toggle.label = "Disable Feature"

        toggle.disabled = False

    @channel_action.select(
        cls=ui.ChannelSelect[SettingsView],
        channel_types=[ChannelType.text],
        placeholder="Select a channel...",
        min_values=0,
        max_values=1,
    )
    async def channel_select(self, itn: Interaction, select: ui.ChannelSelect[SettingsView]):
        assert self.view is not None
        assert self.view.message is not None

        if self.verification is None:
            self.verification = await self.data.insert_verification()

        if not select.values:
            await self.verification.update(role_id=0)
            self.update()
            await itn.response.edit_message(view=self.view)
            return

        resolved = select.values[0].resolve()
        if not resolved:
            await itn.response.send_message("Could not find that channel. Please try again.", ephemeral=True)
            return
        if resolved.id == self.verification.channel_id:
            await itn.response.send_message(f"The verification channel is already set to {resolved.mention}", ephemeral=True)
            return
        perms = resolved.permissions_for(resolved.guild.default_role)
        least = discord.Permissions(view_channel=True, send_messages=True)
        if not perms >= least:
            await itn.response.send_message(
                f"To use {resolved.mention} as a verification channel, make sure `@everyone` "
                "has the `View Channel` and `Send Messages` permissions.\n"
                f"-# NOTE: Edit the permissions in {resolved.mention}, not the server settings",
                ephemeral=True,
            )
            return

        await self.verification.update(channel_id=resolved.id)
        self.update()
        await itn.response.send_message(f"Set verification channel to {resolved.mention}.", ephemeral=True)

    @role_action.select(cls=ui.RoleSelect[SettingsView], placeholder="Select a role...", min_values=0, max_values=1)
    async def role_select(self, itn: Interaction, select: ui.RoleSelect[SettingsView]):
        assert self.view is not None
        assert self.view.message is not None

        if self.verification is None:
            self.verification = await self.data.insert_verification()

        if not select.values:
            await self.verification.update(role_id=0)
            self.update()
            await itn.response.edit_message(view=self.view)
            return

        role = select.values[0]

        if role.id == self.verification.role_id:
            await itn.response.send_message(f"The verification role is already set to {role.mention}.", ephemeral=True)
            return
        if role.managed:
            await itn.response.send_message("This role is managed. Select another role.", ephemeral=True)
            return
        if role == self.view.ctx.me.top_role:
            await itn.response.send_message(
                f"I can not give members {role.mention} because it is my highest role. Please select another role.",
                ephemeral=True,
            )
            return
        if role > self.view.ctx.me.top_role:
            await itn.response.send_message(
                "I can only give members roles that are lower in hierarchy to my top role. "
                f"Please select another role, or move {role.mention} to a position lower than my top role.",
                ephemeral=True,
            )
            return
        perms = role.permissions
        if (
            perms.kick_members
            or perms.ban_members
            or perms.manage_channels
            or perms.manage_guild
            or perms.manage_messages
            or perms.manage_roles
            or perms.manage_webhooks
            or perms.manage_expressions
            or perms.manage_threads
            or perms.moderate_members
        ):
            view = ConfirmView(member=itn.user, timeout=300)
            view.yes.label = "Yes, give new members elevated permissions."
            view.yes.style = discord.ButtonStyle.red
            view.no.label = "No, nevermind."
            view.no.style = discord.ButtonStyle.gray
            await itn.response.send_message(
                f"This role ({role.mention}) has elevated permissions. Are you sure you want to give new members this role?",
                view=view,
                ephemeral=True,
            )
            message = await itn.original_response()
            await view.wait()
            if view.value is None:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass
                return
            if view.value is True:
                await self.verification.update(role_id=role.id)
                await message.edit(content=f"Set verification role to {role.mention}.", view=None)
            if view.value is False:
                await message.edit(content="Okay, no role was set. You can select another role.", view=None)

        else:
            await self.verification.update(role_id=role.id)
            await itn.response.send_message(content=f"Set verification role to {role.mention}.", ephemeral=True)

        self.update()
        await self.view.message.edit(view=self.view, allowed_mentions=itn.client.allowed_mentions)
        return


class AddDisabledCommandModal(ui.Modal, title="Add a Command"):
    command = ui.TextInput(label="Command", placeholder="Type a command name...")

    def __init__(self, view: SettingsView) -> None:
        self.view: SettingsView = view
        super().__init__()

    async def on_submit(self, itn: Interaction) -> None:
        ctx = self.view.ctx
        try:
            converted = await GetCommand.convert(ctx, self.command.value)
        except commands.BadArgument as exc:
            await itn.response.send_message(str(exc), ephemeral=True)
            return

        name = converted.full_parent_name or converted.qualified_name

        disabled = self.view.data.disabled_commands
        if name in disabled:
            await itn.response.send_message("This command is already disabled.", ephemeral=True)
            return
        disabled.append(name)
        await self.view.data.update(disabled_commands=disabled)
        self.view.container.update()
        await itn.response.edit_message(view=self.view)


class AddDisabledCommandButton(ui.Button[SettingsView]):
    async def callback(self, itn: Interaction):
        assert self.view is not None
        assert self.view.message is not None

        modal = AddDisabledCommandModal(self.view)
        await itn.response.send_modal(modal)
        await modal.wait()


class CommandsContainer(SettingsContainer):
    title = ui.TextDisplay("### Command Settings")
    description = ui.TextDisplay("Enable or disable commands or whole channels here.")
    desc_separator = ui.Separator()
    commands = ui.Section(
        ui.TextDisplay("**Disabled Commands**", id=263),
        accessory=AddDisabledCommandButton(label="Add Command", style=discord.ButtonStyle.green),
    )
    commands_select_action = ui.ActionRow()
    commands_separator = ui.Separator()
    channels = ui.TextDisplay("**Disabled Channels**")
    channels_select_action = ui.ActionRow()

    def update(self) -> None:
        assert self.view is not None
        disabled_commands = self.data.disabled_commands
        dummy = discord.SelectOption(label="Command")
        self.command_select.options = []
        if not disabled_commands:
            self.command_select.options = [dummy]
            self.command_select.disabled = True
            self.command_select.max_values = 1
        else:
            self.command_select.disabled = False
            options = [discord.SelectOption(label=command) for command in disabled_commands]
            self.command_select.options = options
            self.command_select.max_values = len(options)

        self.channel_select.default_values = [discord.Object(channel) for channel in self.data.disabled_channels]
        self.view.ctx.guild.text_channels
        self.channel_select.max_values = (
            len(self.view.ctx.guild.channels) - 1
        )  # Need at least one channel for the bot to work in.

        fmt_disabled = f"> {", ".join(disabled_commands)}" if disabled_commands else "There are no commands disabled."
        title = self.commands.find_item(263)
        assert title is not None
        self.commands.clear_items()
        self.commands.add_item(title)
        self.commands.add_item(fmt_disabled)

    @commands_select_action.select(cls=ui.Select[SettingsView], placeholder="Select commands to enable...", min_values=0)
    async def command_select(self, itn: Interaction, select: ui.Select):
        disabled_commands = self.data.disabled_commands
        for command in select.values:
            disabled_commands.remove(command)
        await self.data.update(disabled_commands=disabled_commands)
        self.update()
        await itn.response.edit_message(view=self.view)

    @channels_select_action.select(
        cls=ui.ChannelSelect[SettingsView],
        placeholder="Select channels to disable...",
        channel_types=[
            ChannelType.text,
            ChannelType.voice,
            ChannelType.news,
            ChannelType.stage_voice,
            ChannelType.news_thread,
            ChannelType.public_thread,
            ChannelType.private_thread,
            ChannelType.forum,
            ChannelType.media,
        ],
        min_values=0,
    )
    async def channel_select(self, itn: Interaction, select: ui.ChannelSelect):
        selected = [channel.id for channel in select.values]
        await self.data.update(disabled_channels=selected)
        await itn.response.edit_message(view=self.view)
