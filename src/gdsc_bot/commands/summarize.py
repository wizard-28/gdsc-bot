import discord
from google import genai
import os
from discord import app_commands
from discord.ext import commands
from loguru import logger


@app_commands.context_menu(name="Summarize")
async def summarize(interaction: discord.Interaction, message: discord.Message) -> None:
    """Provides a context menu option fo the user to summarize long messages.

    Basically the same as `respond.py` except with the additional summarize prompt
    """
    await interaction.response.defer()  # Defer response if the API call takes time

    # Load the API key
    genai_key = os.getenv("GEMINI_API_KEY")

    if not genai_key:
        logger.error("Unable to road gemini api key")

    # Make the gemini client
    genai_client = genai.Client(api_key=genai_key)

    try:
        # Call the API to get the response for the user's prompt
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Summraize the following message: \n{message.content}",
        )

        if not response:
            await interaction.followup.send("No response")
            return

        text = response.text
        if not text:
            logger.debug("No response from gemini")
            return

        # HACK: Since discord has a 2000 characters limit, therefore split it into chunks
        if len(text) <= 2000:
            await interaction.followup.send(text)
        else:
            chuncks = []
            current_chunk = ""

            for line in text.splitlines():
                # If we can't fit any more lines into the current chunk
                # Then add the current chunk to the chunks list (as it's over)
                #
                # Start the next current chunk with the unadded line
                if len(current_chunk) + len(line) + 1 > 2000:
                    chuncks.append(current_chunk)
                    current_chunk = line  # Start a new chunk
                else:
                    # Else append the current line to the current chunk
                    # or just the current line if it's empty
                    current_chunk += ("\n" + line) if current_chunk else line

            if current_chunk:
                chuncks.append(current_chunk)

            for chunk in chuncks:
                await interaction.followup.send(chunk)

        logger.info(f"User {interaction.user} used /respond with message: {message}")

    # Blanket `Exception` is bad I know, but the user doesn't need to know which error occured.
    # So just log it instead
    except Exception as e:
        logger.error(f"Error in /respond: {e}")
        await interaction.followup.send("An error occurred. Please try again.")


async def setup(bot: commands.Bot) -> None:
    bot.tree.add_command(summarize)
