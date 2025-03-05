# GDSC Bot

## Features Implemented

- `respond`: Respond to user messages in the Discord server using the Gemini API
- reminders: Create, delete, and modify reminders for users in the Discord server. Users should
  be able to set a reminder by sending a message with the time and date of the
  reminder in a specific format
- `poll`: Users should be able to create Polls.
- Automatic welcome card when a new user joins

## Running instructions

### If just inviting

Invite URL: <https://discord.com/oauth2/authorize?client_id=1346339416045649950>

The bot maybe offline most of the time, as I'm not hosting it.

### Self Hosting

1. Create [your own bot app in discord](https://discord.com/developers/applications/)
2. Get [gemini api key](https://aistudio.google.com/apikey)
3. Add a `.env` file to the project root directory in this format

```monospace
TOKEN=<token>
GEMINI_API_KEY=<gemini_api_key>
```

4. Install [Poetry](https://python-poetry.org/) and [Python](https://www.python.org/)
5. Run the following commands

```bash
git clone https://github.com/wizard-28/gdsc-bot.git
cd gdsc-bot

poetry install

poetry run python -m gdsc_bot
```

6. Enjoy the bot

## Implementation details

Detailed using docstrings and comments in the code.

Start from [**main**.py](src/gdsc_bot/__main__.py)

See [JOURNAL.md](/JOURNAL.md) for my development process.
