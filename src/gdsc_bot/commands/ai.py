from collections import defaultdict
import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from loguru import logger


class AIGroup(commands.GroupCog, group_name="ai"):  # type: ignore[call-arg]
    """
    Command for responding to user messages using Gemini API with conversation memory
    """

    def __init__(self, bot: commands.Bot):
        # Load the API key
        genai_key = os.getenv("GEMINI_API_KEY")

        if not genai_key:
            logger.error("Unable to load Gemini API key")

        # Create Gemini client
        self.genai_client = genai.Client(api_key=genai_key)
        self.bot = bot

        # Store conversation history: {user_id: [(role, message), ...]}
        self.conversations: defaultdict[int, list[tuple[str, str]]]
        self.conversations = defaultdict(list)

    @app_commands.command(
        name="respond", description="Chat using Gemini API with memory!"
    )
    @app_commands.describe(prompt="Enter your message for Gemini")
    async def respond(self, interaction: discord.Interaction, prompt: str) -> None:
        await interaction.response.defer()

        user_id = interaction.user.id

        # Append user message to history
        self.conversations[user_id].append(("user", prompt))

        # Keep only the last 10 exchanges to avoid excessive memory usage
        self.conversations[user_id] = self.conversations[user_id][-10:]

        try:
            # Construct conversation context for the API
            conversation_history = "\n".join(
                [f"{role}: {message}" for role, message in self.conversations[user_id]]
            )

            # Call the Gemini API with chat history
            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash", contents=conversation_history
            )

            if not response:
                await interaction.followup.send("No response")
                return

            text = response.text
            if not text:
                logger.debug("No response from Gemini")
                return

            # Append bot response to conversation history
            self.conversations[user_id].append(("assistant", text))

            # Ensure Discord message fits within 2000 characters
            if len(text) <= 2000:
                await interaction.followup.send(text)
            else:
                # Split into multiple messages
                chunks = []
                current_chunk = ""

                for line in text.splitlines():
                    if len(current_chunk) + len(line) + 1 > 2000:
                        chunks.append(current_chunk)
                        current_chunk = line  # Start a new chunk
                    else:
                        current_chunk += ("\n" + line) if current_chunk else line

                if current_chunk:
                    chunks.append(current_chunk)

                for chunk in chunks:
                    await interaction.followup.send(chunk)

            logger.info(f"User {interaction.user} used /respond with prompt: {prompt}")

        except Exception as e:
            logger.error(f"Error in /respond: {e}")
            await interaction.followup.send("An error occurred. Please try again.")

    @app_commands.command(name="clearmemory", description="Clear chat memory")
    async def clear_memory(self, interaction: discord.Interaction) -> None:
        """Command to clear the user's conversation memory"""
        user_id = interaction.user.id
        if user_id in self.conversations:
            del self.conversations[user_id]
            await interaction.response.send_message(
                "Your chat memory has been cleared."
            )
        else:
            await interaction.response.send_message("No conversation history found.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AIGroup(bot))
