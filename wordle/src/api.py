import os # needed to set OpenAI API key at runtime
import re

from pygame import time

from assets.valid_words import VALID_WORDS
from classes.GameState import GameState, Status
from constants import ANIMATION_DURATION, FEEDBACK_DIFF_DURATION


def matches_regex(pattern, string):
    return bool(re.fullmatch(pattern, string))


def api(game: GameState):
    while True:
        try:
            string_input = input()
        except EOFError:
            # stdin closed (e.g., process was started with a pipe); exit thread cleanly
            print("API input closed — exiting API thread")
            return

        # ignore empty/blank lines
        if not string_input or not string_input.strip():
            continue

        tokens = string_input.split()
        if not tokens:
            continue

        cmd = tokens[0]
        args = tokens[1:]
        print()

        match cmd:
            case 'guess':
                if args[0] and args[0].lower() in VALID_WORDS:
                    if game.status != Status.game:
                        print("Error: No active game\n")
                        continue

                    guess_word = args[0].lower()
                    game.enter_word_from_solver(guess_word)
                    delay = FEEDBACK_DIFF_DURATION * 4 + ANIMATION_DURATION + \
                        100 if not game.disable_animations else 0
                    time.delay(delay)
                    offset = 0 if game.status == Status.end else 1
                    feedback = game.words[game.current_word_index -
                                          offset].get_feedback()

                    # print game status
                    print(
                        f"status: {'Completed' if game.status == Status.end else 'In progress'}\n"
                        f"tries: {game.num_of_tries()} / {game.num_guesses}\n"
                        f"success: {game.success if game.status == Status.end else 'NA'}\n"
                    )

                    # print feedback from guess
                    for idx, fdb in enumerate(feedback):
                        print(f"{guess_word[idx]}: {fdb.value}")
                else:
                    print("Invalid guess input")
            case 'new-game':
                if game.status == Status.start:
                    game.status = Status.game
                else:
                    game.reset()

                print("Starting game")
            case 'set-openai-key':
                # usage: set-openai-key <key>
                if len(args) < 1 or not args[0]:
                    print("Error: Missing API key")
                    continue

                key = args[0]
                # set for current process and re-init the client's platform
                os.environ["OPENAI_API_KEY"] = key
                try:
                    game.set_llm_platform("openai")
                    print("OpenAI API key set and client initialized")
                except Exception as e:
                    print(f"Error initializing OpenAI client: {e}")

            case 'set-llm-platform':
                # usage: set-llm-platform <platform>
                if len(args) < 1 or not args[0]:
                    print("Error: Missing platform (openai|gemini|ollama)")
                    continue

                platform = args[0]
                try:
                    game.set_llm_platform(platform)
                    print(f"LLM platform set to {platform}")
                except Exception as e:
                    print(f"Error setting platform: {e}")

            case 'set-ollama-model':
                # usage: set-ollama-model <model-name>
                if len(args) < 1 or not args[0]:
                    print("Error: Missing model name")
                    continue

                model = args[0]
                # store per-game instance so GameState will use it
                setattr(game, 'ollama_model', model)
                print(f"Ollama model set to {model} for this game instance")

            case 'ai-play':
                # let the configured LLM play the current game until completion
                if game.status != Status.game:
                    print("Error: No active game\n")
                    continue

                if game.llm_platform != "openai" and game.llm_platform != "gemini" and game.llm_platform != "ollama":
                    print("Error: Unsupported LLM platform configured")
                    continue

                # simple loop: ask the LLM to make guesses until the game ends
                while game.status != Status.end:
                    game.enter_word_from_ai()

                    delay = FEEDBACK_DIFF_DURATION * 4 + ANIMATION_DURATION + \
                        100 if not game.disable_animations else 0
                    time.delay(delay)
                    offset = 0 if game.status == Status.end else 1
                    # current word is the most recently locked word
                    try:
                        feedback = game.words[game.current_word_index - offset].get_feedback()
                        guess_word = game.words[game.current_word_index - offset].guessed_word
                    except Exception:
                        feedback = []
                        guess_word = ""

                    # print game status
                    print(
                        f"status: {'Completed' if game.status == Status.end else 'In progress'}\n"
                        f"tries: {game.num_of_tries()} / {game.num_guesses}\n"
                        f"success: {game.success if game.status == Status.end else 'NA'}\n"
                    )

                    # print feedback from guess (if any)
                    if feedback:
                        print(f"AI guessed: {guess_word}")
                        for idx, fdb in enumerate(feedback):
                            print(f"{guess_word[idx]}: {fdb.value}")
                    else:
                        print("No feedback available for the last AI guess")
            case 'config':
                if args[0] and args[0] == "lies" and args[1] and matches_regex(r"\b[0-5]\b", args[1]):
                    game.status = Status.config
                    lies = int(args[1])
                    game.num_lies = lies

                    print(f"Number of lies -> {args[1]}")
                elif args[0] and args[0] == "guesses" and args[1] and matches_regex(r"\b[6-9]\b", args[1]):
                    game.status = Status.config
                    guesses = int(args[1])
                    game.num_guesses = guesses

                    print(f"Number of guesses -> {args[1]}")
                else:
                    print("Error: Invalid config")
            case _:
                print("Error: Invalid command")

        print()  # newline for spacing
