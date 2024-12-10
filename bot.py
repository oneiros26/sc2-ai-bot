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
              f"Worker amount: {self.workers.amount}"
              f"Supply Used: {self.supply_used}")

        # pokud mame townhall, prirad ho do var commandcenter
        if self.townhalls:
            commandcenter = self.townhalls.random

            # pokud mame 22 pracovniku nevytvarej dalsi
            if commandcenter.is_idle and self.can_afford(UnitTypeId.SCV) and self.units(UnitTypeId.SCV) < 23:
                commandcenter.train(UnitTypeId.SCV)






            # pokud nemame supply depot tak ho postav blizko commandcentru
            elif not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0:
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    await self.build(UnitTypeId.SUPPLYDEPOT, near=commandcenter)

            #pokud nam zbyva min nez 4 suppply, tak postav dalsi supplydepot
            elif self.supply_left < 4 and self.can_afford(UnitTypeId.SUPPLYDEPOT):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=self.townhalls.ready.first.position.towards(self.game_info.map_center, distance=5))






            #A Barracks allows you to start producing Marines, the backbone of your early army, and is required to tech up. Usually, your Barracks is started immediately after your first Supply Depot while your Command Center is producing SCVs.
            elif self.supply_used >= 16 and self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                # Find a suitable location near the Command Center to build Barracks
                cc = self.townhalls.ready.first
                if cc:
                    pos = cc.position.towards(self.game_info.map_center, distance=5)
                    await self.build(UnitTypeId.BARRACKS, near=pos)

            #build refinery early in the game to collect vespene gas
            elif self.supply_used >= 16 and not self.already_pending(UnitTypeId.REFINERY):
                for cc in self.townhalls.ready:
                    vespene_geysers = self.vespene_geyser.closer_than(10, cc)
                    for vg in vespene_geysers:
                        if self.can_afford(UnitTypeId.REFINERY) and not self.gas_buildings.closer_than(1, vg):
                            await self.build(UnitTypeId.REFINERY, target=vg)
                            break

            # After the Barracks is finished, attach a Reactor
            barracks = self.structures(UnitTypeId.BARRACKS).ready.first  # Get the first completed Barracks
            if barracks and not barracks.has_addon:  # If the Barracks is built and doesn't already have an Addon
                if self.can_afford(UnitTypeId.REACTOR) and not self.already_pending(UnitTypeId.REACTOR):
                    await self.build(UnitTypeId.REACTOR, near=barracks)  # Build a Reactor next to the Barracks

            # Build Marines once the Reactor is ready
            if self.structures(UnitTypeId.REACTOR).ready:
                barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                if barracks.has_addon and self.can_afford(UnitTypeId.MARINE):
                    barracks.train(UnitTypeId.MARINE)

            # Check if the Command Center is ready and not yet upgraded to Orbital Command
            command_center = self.townhalls.ready.first  # Get the first ready Command Center
            if command_center and not command_center.has_addon:  # Check if it has no addon (Orbital Command is not yet built)
                if self.can_afford(UnitTypeId.ORBITALCOMMAND):  # Check if we can afford the upgrade
                    await self.build(UnitTypeId.ORBITALCOMMAND, near=command_center)  # Upgrade the Command Center







        # pokud nemame commandcenter a mame na nej penize, tak ho postav
        else:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.expand_now()

sc2.run_game(
    sc2.maps.get("Starlight"),
    [Bot(sc2.Race.Terran, NetheriteBot()), Computer(sc2.Race.Protoss, sc2.Difficulty.VeryEasy)],
    realtime=False,
)