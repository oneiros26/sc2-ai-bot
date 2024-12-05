import sc2
from sc2.bot_ai import BotAI
from sc2.player import Bot, Computer
from sc2.data import Difficulty, Race
from sc2 import maps

class TerranBot(BotAI):
    async def on_step(self, iteration: int):
        print(f"Iteration: {iteration}!")

sc2.run_game(
    sc2.maps.get("Starlight"),
    [Bot(sc2.Race.Terran, TerranBot()), Computer(sc2.Race.Protoss, sc2.Difficulty.VeryEasy)],
    realtime=False,
)