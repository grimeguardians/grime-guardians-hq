"""
Discord Approval View
Renders ✅ Approve / ❌ Deny buttons on inbound message drafts.
On approval, fires the message via GHL. On denial, cancels cleanly.
"""

import logging
import discord

from ..config.settings import get_settings
from ..integrations.gohighlevel_integration import GoHighLevelIntegration

logger = logging.getLogger(__name__)
settings = get_settings()


class ApprovalView(discord.ui.View):
    """
    Discord UI view with Approve and Deny buttons.
    Attached to every inbound message draft posted by the router.
    """

    def __init__(
        self,
        conversation_id: str,
        draft: str,
        contact_name: str,
        msg_type: str = "SMS",
        timeout: float = 3600.0,   # 1 hour before buttons expire
    ):
        super().__init__(timeout=timeout)
        self.conversation_id = conversation_id
        self.draft = draft
        self.contact_name = contact_name
        self.msg_type = msg_type

    @discord.ui.button(label="✅ Approve & Send", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Send the drafted message via GHL and update the embed."""
        await interaction.response.defer()

        sent = False
        if self.conversation_id:
            try:
                async with GoHighLevelIntegration() as ghl:
                    sent = await ghl.send_message(
                        conversation_id=self.conversation_id,
                        message=self.draft,
                        message_type=self.msg_type if self.msg_type in ("SMS", "Email") else "SMS",
                    )
            except Exception as e:
                logger.error(f"Failed to send approved message: {e}")

        # Update the embed to reflect outcome
        for child in self.children:
            child.disabled = True

        if sent:
            result_text = f"✅ **Sent** by {interaction.user.display_name}"
            color = discord.Color.green()
        else:
            result_text = f"⚠️ **Approval recorded** but GHL send failed — send manually.\nApproved by {interaction.user.display_name}"
            color = discord.Color.yellow()

        original = interaction.message
        embed = original.embeds[0] if original.embeds else discord.Embed()
        embed.color = color
        embed.set_footer(text=result_text)

        await interaction.message.edit(embed=embed, view=self)
        logger.info(f"Message to {self.contact_name} {'sent' if sent else 'failed'} after approval by {interaction.user.display_name}")

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the draft and mark the embed as denied."""
        await interaction.response.defer()

        for child in self.children:
            child.disabled = True

        original = interaction.message
        embed = original.embeds[0] if original.embeds else discord.Embed()
        embed.color = discord.Color.dark_gray()
        embed.set_footer(text=f"❌ Denied by {interaction.user.display_name} — handle manually or re-draft.")

        await interaction.message.edit(embed=embed, view=self)
        logger.info(f"Draft for {self.contact_name} denied by {interaction.user.display_name}")

    async def on_timeout(self):
        """Disable buttons after timeout — prevents orphaned interactive elements."""
        for child in self.children:
            child.disabled = True
        logger.info(f"Approval view for {self.contact_name} timed out.")
