"""
[Avimetry Bot]
Copyright (C) 2021 - 2022 avizum

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
import asyncio
import contextlib
import functools

import discord


class AvimetryView(discord.ui.View):
    def __init__(self, *, member: discord.Member, timeout: int = 180):
        self.member = member
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.member:
            embed = discord.Embed(
                description=f"This can only be used by {self.member}."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True


def disable_when_pressed(func):
    @functools.wraps(func)
    async def callback_wrapper(self, component, interaction):
        async with self.disable(interaction=interaction):
            await func(self, component, interaction)

    return callback_wrapper


# Inspired by (and uses code from) Mousey (https://github.com/LostLuma/Mousey/blob/stardust/packages/bot/src/ui.py)
class InteractiveView(AvimetryView):
    def __init__(self, ctx, timeout: int = 180):
        self.ctx = ctx
        self.message: discord.Message = None
        self._disabled = None
        super().__init__(member=ctx.author, timeout=timeout)

    async def start(self, content: str = None, **kwargs):
        await self.update(content, **kwargs)
        return await self.wait()

    async def on_timeout(self) -> None:
        if self._disabled or self.message is None:
            return
        self._disable_children()

        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            pass

    async def update(self, content: str = None, **kwargs):
        await self.update_children()
        content = content or await self.create_message()
        embed = isinstance(content, discord.Embed)
        if self.message:
            if embed:
                await self.message.edit(embed=content, view=self, **kwargs)
            else:
                await self.message.edit(content=content, view=self, **kwargs)
        elif embed:
            self.message = await self.ctx.send(embed=content, view=self, **kwargs)
        else:
            self.message = await self.ctx.send(content, view=self, **kwargs)

    async def update_children(self):
        pass

    async def create_message(self):
        pass

    def _disable_children(self):
        for child in self.children:
            if hasattr(child, 'disabled'):
                child.disabled = True

    @contextlib.asynccontextmanager
    async def disable(self, interaction=None):
        if self.message is None:
            raise RuntimeError('Missing message to edit.')

        items = [x for x in self.children if hasattr(x, 'disabled')]
        state = [x.disabled for x in items]  # type: ignore :blobpain:

        try:
            self._disabled = True

            for item in items:
                item.disabled = True  # type: ignore

            if interaction is None or interaction.response.is_done():
                await self.message.edit(view=self)
            else:
                await interaction.response.edit_message(view=self)

            yield
        finally:
            self._disabled = False

            for item, previous in zip(items, state):
                item.disabled = previous  # type: ignore

            if not self.is_finished():
                await self.update()

    async def _wait_for(self, message: str, view: discord.ui.View, interaction: discord.Interaction):
        msg = await interaction.followup.send(message, view=view)
        await view.wait()
        await msg.delete()

        if view.result is not None:
            return view.result
        else:
            raise asyncio.TimeoutError

    async def prompt(self, message: str, *, check=None, interaction: discord.Interaction):
        view = ExitableMenu(ctx=self.ctx, timeout=180)

        msg = await interaction.followup.send(message, view=view, wait=True)

        def check(m: discord.Message):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        cancel_task = self.ctx.bot.loop.create_task(view.wait())
        wait_for_task = self.ctx.bot.loop.create_task(self.ctx.bot.wait_for('message', check=check))

        try:
            cancel_task = view.wait()
            wait_for_task = self.ctx.bot.wait_for('message', check=check)

            done, pending = await asyncio.wait(
                {cancel_task, wait_for_task}, timeout=view.timeout, return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if not done or cancel_task in done:
                raise asyncio.TimeoutError
        finally:
            await msg.delete()

        response = await next(iter(done))

        if self.ctx.channel.permissions_for(self.ctx.me).manage_messages:
            await response.delete()

        return response.content


class _StopButton(discord.ui.Button):
    async def callback(self, interaction):
        view = self.view

        if view is None:
            raise RuntimeError('Missing view to disable.')

        view.stop()
        view._disable_children()

        if view.message is not None:
            await interaction.response.edit_message(view=view)


class ExitableMenu(InteractiveView):
    def __init__(self, ctx, timeout: int = 180):
        super().__init__(ctx, timeout)
        self.add_item(_StopButton(label='Exit'))
