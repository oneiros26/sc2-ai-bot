import sc2
from sc2.bot_ai import BotAI
from sc2.player import Bot, Computer
from sc2.data import Difficulty, Race
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId

class NetheriteBot(BotAI):
    async def on_step(self, iteration: int):
        print(f"Iteration: {iteration}!")

        if self.townhalls:
            nexus = self.townhalls.random
            if nexus.is_idle and self.can_afford(UnitTypeId.SCV):
                nexus.train(UnitTypeId.SCV)

sc2.run_game(
    sc2.maps.get("Starlight"),
    [Bot(sc2.Race.Terran, NetheriteBot()), Computer(sc2.Race.Protoss, sc2.Difficulty.VeryEasy)],
    realtime=False,
)