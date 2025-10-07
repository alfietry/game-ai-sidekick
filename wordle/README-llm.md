# Local mock LLM server for contributors

This project includes a tiny mock LLM HTTP server so contributors can test the `custom` LLM platform without needing external services.

Run the mock server:

```powershell
cd wordle
py .\tools\mock_llm_server.py
```

This starts a server at `http://localhost:8080/predict` which accepts a POST JSON payload like:

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]}
```

and responds with JSON:

```json
{"guess": "arise"}
```

How to use from the running game:

1. Start the mock server (as above).
2. In the game's API thread or stdin, run:

```
set-llm-endpoint http://localhost:8080/predict
set-llm-platform custom
new-game
ai-play
```

The game will POST messages to the mock server and use the returned `guess` value. If `requests` isn't installed, the game will fall back to the local solver; install dependencies with:

```powershell
py -3 -m pip install -r requirements.txt
```
