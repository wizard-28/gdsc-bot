def get_response(user_input: str) -> str:
    lowered = user_input.lower()

    if not lowered:
        return "You're silent"
    else:
        return "Hello there!"
