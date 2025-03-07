This file details my development process and thought process.

1. Created the base project using poetry and setted up the general python groundwork.
2. Evaluate various discord python libraries online like hikari, discord.py, interactions.py.
   Eventually settle on discord.py as it has the largest community.
3. Learn about the basic boilerplate from <https://www.youtube.com/watch?v=UYJDKSah-Ww>
4. Learn about slash commands etc from here: <https://www.youtube.com/watch?v=26Sj5hJFqUs>
5. Create a command handler that automatically loads in commands from the commands directory. This will ease up development. Sources: [discord.js docs for command handlers](https://discordjs.guide/creating-your-bot/command-handling.html#loading-command-files) (Don't mind me...), [Discord.py cogs docs]()
6. Setup the `respond` command. Get the API key from [gemini website](https://aistudio.google.com/apikey). Use the [Google Gen AI SDK](https://pypi.org/project/google-genai/).
7. Setup the `help` command. Sources: <https://www.youtube.com/watch?v=gX4_ZJl9BKg>
8. Create the `poll` command, sources: various
9. Implement reminder related commands, sources: <https://www.youtube.com/watch?v=kNUuYEWGOxA>, <https://www.youtube.com/watch?v=tQvzuVQPNyQ>, use `rapidfuzz`
10. Welcome message: <https://www.youtube.com/watch?v=V4ekOOPMg1k>, use `easy_pil`
11. Ask friends to test the bot, find multiple bugs and fix them.
12. Add docs
13. Improve the `/help` command
14. Add `summarize` context menu command
15. Rewrite `remind.py` using a min-heap
