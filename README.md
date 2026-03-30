## Start

1. clon repo
2. edit .env file in tgbot folder:
```
   BOT_TOKEN=your_token
```
3. start:
```bash
   docker compose up --build
```
4. download model (first time):
```bash
   docker compose exec ollama ollama pull llama3
```
5. open http://localhost:8000
