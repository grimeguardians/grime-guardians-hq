"""
Discord Approval View
Renders ✅ Approve / ✏️ Amend & Send / ❌ Deny buttons on inbound message drafts.
On approval, fires the message via GHL. On amend, opens a modal for edits then sends.
On denial, cancels cleanly.
"""

import logging
import discord

from ..integrations.gohighlevel_integration import GoHighLevelIntegration

logger = logging.getLogger(__name__)


async def _send_via_ghl(
    conversation_id: str,
    message: str,
    msg_type: str,
) -> bool:
    """Send a message through GHL and return success bool."""
    try:
        async with GoHighLevelIntegration() as ghl:
            return await ghl.send_message(
                conversation_id=conversation_id,
                message=message,
                message_type=msg_type if msg_type in ("SMS", "Email") else "SMS",
            )
    except Exception as e:
        logger.error(f"GHL send_message error: {e}")
        return False


class AmendModal(discord.ui.Modal, title="Amend Message"):
    """
    Modal dialog that lets the user edit the draft before sending.
    Opened when the ✏️ Amend & Send button is clicked.
    """

    amended_text = discord.ui.TextInput(
        label="Edited message",
        style=discord.TextStyle.paragraph,
        placeholder="Type your revised message here…",
        max_length=1600,
    )

    def __init__(self, view: "ApprovalView"):
        super().__init__()
        self.approval_view = view
        # Pre-fill with the current draft so user only needs to change what they want
        self.amended_text.default = view.draft

    async def on_submit(self, interaction: discord.Interaction):
        """Send the amended message via GHL and update the embed."""
        await interaction.response.defer()

        new_message = self.amended_text.value.strip()
        sent = False

        if self.approval_view.conversation_id and new_message:
            sent = await _send_via_ghl(
                self.approval_view.conversation_id,
                new_message,
                self.approval_view.msg_type,
            )

        # Disable all buttons on the original message
        for child in self.approval_view.children:
            child.disabled = True

        if sent:
            result_text = f"✏️ **Amended & Sent** by {interaction.user.display_name}"
            color = discord.Color.blurple()
        else:
            result_text = (
                f"⚠️ **Amend recorded** but GHL send failed — send manually.\n"
                f"Amended by {interaction.user.display_name}"
            )
            color = discord.Color.yellow()

        original = interaction.message
        embed = original.embeds[0] if original.embeds else discord.Embed()
        embed.color = color

        # Replace the draft field with the amended text so there's a record
        new_fields = []
        for field in embed.fields:
            if "draft" in field.name.lower():
                new_fields.append(
                    discord.EmbedField(
                        name=f"{field.name} → amended",
                        value=f"```{new_message}```",
                        inline=False,
                    )
                )
            else:
                new_fields.append(field)
        embed.clear_fields()
        for f in new_fields:
            embed.add_field(name=f.name, value=f.value, inline=f.inline)

        embed.set_footer(text=result_text)
        await interaction.message.edit(embed=embed, view=self.approval_view)
        logger.info(
            f"Amended message to {self.approval_view.contact_name} "
            f"{'sent' if sent else 'failed'} by {interaction.user.display_name}"
        )


class ApprovalView(discord.ui.View):
    """
    Discord UI view with Approve, Amend & Send, and Deny buttons.
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

        sent = await _send_via_ghl(self.conversation_id, self.draft, self.msg_type)

        for child in self.children:
            child.disabled = True

        if sent:
            result_text = f"✅ **Sent** by {interaction.user.display_name}"
            color = discord.Color.green()
        else:
            result_text = (
                f"⚠️ **Approval recorded** but GHL send failed — send manually.\n"
                f"Approved by {interaction.user.display_name}"
            )
            color = discord.Color.yellow()

        original = interaction.message
        embed = original.embeds[0] if original.embeds else discord.Embed()
        embed.color = color
        embed.set_footer(text=result_text)
        await interaction.message.edit(embed=embed, view=self)
        logger.info(
            f"Message to {self.contact_name} {'sent' if sent else 'failed'} "
            f"after approval by {interaction.user.display_name}"
        )

    @discord.ui.button(label="✏️ Amend & Send", style=discord.ButtonStyle.primary)
    async def amend(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open a modal so the user can edit the draft before sending."""
        modal = AmendModal(view=self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.secondary)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the draft and mark the embed as denied."""
        await interaction.response.defer()

        for child in self.children:
            child.disabled = True

        original = interaction.message
        embed = original.embeds[0] if original.embeds else discord.Embed()
        embed.color = discord.Color.dark_gray()
        embed.set_footer(
            text=f"❌ Denied by {interaction.user.display_name} — handle manually or re-draft."
        )
        await interaction.message.edit(embed=embed, view=self)
        logger.info(f"Draft for {self.contact_name} denied by {interaction.user.display_name}")

    async def on_timeout(self):
        """Disable buttons after timeout — prevents orphaned interactive elements."""
        for child in self.children:
            child.disabled = True
        logger.info(f"Approval view for {self.contact_name} timed out.")
