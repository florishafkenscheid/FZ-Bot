from fz_api import FZClient
from tokens import DISCORD_TOKEN

class Main:
    def __init__(self):
        self.client: (FZClient | None) = None

    async def main(self):
        self.client = FZClient()
        await self.client.connect()
        await self.client.wait_sync()

def main():
    from discordbot import Bot
    discordBot = Bot(Main)
    discordBot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()