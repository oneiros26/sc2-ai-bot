import sc2
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
import random

class NetheriteBot(BotAI):
    async def on_step(self, iteration: int):
        # kolik iteraci probehlo
        print(f"Iteration: {iteration}!", \
              f"Worker amount: {self.workers.amount}")

        # pokud mame townhall, prirad ho do var commandcenter
        if self.townhalls:
            commandcenter = self.townhalls.random

            # pokud mame 22 pracovniku nevytvarej dalsi
            if commandcenter.is_idle and self.can_afford(UnitTypeId.SCV) and self.units(UnitTypeId.SCV) <= 22:
                commandcenter.train(UnitTypeId.SCV)

            # pokud nemame supply depot tak ho postav blizko commandcentru
            elif not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0:
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=commandcenter)

            # pokud mame min nez 5 supply depotu, tak ho postav smerem k nepriteli
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount < 5:
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # vyber supply depot co je nejblize k nepriteli
                    target_supplydepot = self.structures(UnitTypeId.SUPPLYDEPOT).closest_to(self.enemy_start_locations[0])
                    # postav supply depot vedle target_supplydepot smerem k nepriteli
                    pos = target_supplydepot.position.towards(self.enemy_start_locations[0], random.randrange(8, 15))
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=pos)

        # pokud nemame commandcenter a mame na nej penize, tak ho postav
        else:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.expand_now()

sc2.run_game(
    sc2.maps.get("Starlight"),
    [Bot(sc2.Race.Terran, NetheriteBot()), Computer(sc2.Race.Protoss, sc2.Difficulty.VeryEasy)],
    realtime=False,
)