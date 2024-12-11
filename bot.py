import sc2
from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Difficulty, Race

class TerranBot(BotAI):
    async def on_step(self, iteration: int):
        # kolik iteraci probehlo
        print(f"Iteration: {iteration}!",
              f"Worker amount: {self.workers.amount}\n"
              f"Supply Used: {self.supply_used}")

        total_workers = self.units(UnitTypeId.SCV).amount + self.already_pending(UnitTypeId.SCV)
        total_marines = self.units(UnitTypeId.MARINE).amount + self.already_pending(UnitTypeId.MARINE)
        main_ramp = self.main_base_ramp
        corner_depots = list(main_ramp.corner_depots)
        sorted_depots = sorted(corner_depots, key=lambda p: p.x)
        left_ramp_depot = sorted_depots[0]
        right_ramp_depot = sorted_depots[-1]

        # vzichni nepracujici zpatky do prace
        await self.distribute_workers()

        # pokud mame townhall, prirad ho do var townhall
        if self.townhalls:
            townhall = self.townhalls.closest_to(self.start_location)
            townhall_2 = self.townhalls.furthest_to(self.start_location)

            # vycvic 2 SCV [12]
            if self.can_afford(UnitTypeId.SCV) and total_workers < 14:
                townhall.train(UnitTypeId.SCV)

            # postav SUPPLY DEPOT [14]
            elif not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and total_workers >= 14:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=right_ramp_depot)

            #SCV dalsi
            elif self.can_afford(UnitTypeId.SCV) and total_workers < 15 and self.structures(UnitTypeId.SUPPLYDEPOT):
                townhall.train(UnitTypeId.SCV)

            # postav BARRACKS [15]
            elif not self.structures(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0 and self.can_afford(UnitTypeId.BARRACKS) and total_workers >= 15:
                pos = townhall.position.towards(self.enemy_start_locations[0], 10)
                await self.build(UnitTypeId.BARRACKS, near=pos)

            # postav REFINERY [16]
            elif not self.structures(UnitTypeId.REFINERY) and self.structures(UnitTypeId.BARRACKS).amount == 1 and not self.already_pending(UnitTypeId.REFINERY):
                vespenes = self.vespene_geyser.closer_than(15, townhall)
                await self.build(UnitTypeId.REFINERY, vespenes.random)

            # posleme SCV do rafinerie pracovat
            elif self.structures(UnitTypeId.REFINERY).ready and self.structures(UnitTypeId.REFINERY).ready.first.assigned_harvesters < 3:
                refinery = self.structures(UnitTypeId.REFINERY).ready.first
                scv_gas = self.units(UnitTypeId.SCV).first
                scv_gas.gather(refinery)

            # vycvic SCV [14]
            elif self.can_afford(UnitTypeId.SCV) and total_workers < 19 and self.structures(UnitTypeId.SUPPLYDEPOT):
                townhall.train(UnitTypeId.SCV)

            # postav BARRACKS REACTOR [19]
            elif not self.structures(UnitTypeId.BARRACKSREACTOR) and not self.already_pending(UnitTypeId.BARRACKSREACTOR) and self.can_afford(UnitTypeId.BARRACKSREACTOR):
                barracks = self.structures(UnitTypeId.BARRACKS).ready.filter(lambda b: not b.has_add_on)
                barracks.random.build(UnitTypeId.BARRACKSREACTOR)

            # postav dalsi COMMAND CENTER na dalsi resources a expanzi baseky
            elif self.can_afford(UnitTypeId.COMMANDCENTER) and self.structures(UnitTypeId.BARRACKSREACTOR) and ((self.structures(UnitTypeId.COMMANDCENTER).amount == 1 and self.structures(UnitTypeId.ORBITALCOMMAND).amount == 0) or (self.structures(UnitTypeId.ORBITALCOMMAND).amount == 1 and self.structures(UnitTypeId.COMMANDCENTER).amount == 0)):
                expansion_location = await self.get_next_expansion()
                if expansion_location:
                    builder = self.workers.closest_to(expansion_location)
                    builder.build(UnitTypeId.COMMANDCENTER, expansion_location)

            # postav ORBITAL COMMAND
            elif not self.structures(UnitTypeId.ORBITALCOMMAND) and self.can_afford(UnitTypeId.ORBITALCOMMAND)  and self.structures(UnitTypeId.COMMANDCENTER).amount == 2:
                townhall.build(UnitTypeId.ORBITALCOMMAND)

            # postav dalsi SUPPLY DEPOT
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount == 1 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.COMMANDCENTER) and self.structures(UnitTypeId.ORBITALCOMMAND):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=left_ramp_depot)

            # vycvic 3 SCV
            elif self.can_afford(UnitTypeId.SCV) and total_workers < 22 and self.structures(UnitTypeId.SUPPLYDEPOT).amount == 2:
                townhall.train(UnitTypeId.SCV)

            # vycvic 2 MARINES
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 2 and self.structures(UnitTypeId.BARRACKSREACTOR):
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BUNKER
            elif not self.structures(UnitTypeId.BUNKER) and self.already_pending(UnitTypeId.BUNKER) == 0 and self.can_afford(UnitTypeId.BUNKER) and total_marines >= 2:
                await self.build(UnitTypeId.BUNKER, near=townhall_2)

            # vycvic 8 MARINES
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 10 and self.structures(UnitTypeId.BUNKER):
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav 2 BARRACKS
            elif self.structures(UnitTypeId.BARRACKS).amount < 3 and self.already_pending(UnitTypeId.BARRACKS) < 2 and self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BUNKER):
                target_barracks = self.structures(UnitTypeId.BARRACKS).closest_to(self.enemy_start_locations[0])
                pos = target_barracks.position.towards(self.enemy_start_locations[0], 7)
                await self.build(UnitTypeId.BARRACKS, near=pos)

            # postav druhy ORBITAL COMMAND
            elif self.structures(UnitTypeId.ORBITALCOMMAND) == 1 and self.can_afford(UnitTypeId.ORBITALCOMMAND) and self.structures(UnitTypeId.BARRACKS).amount == 3:
                command_centers = self.structures(UnitTypeId.COMMANDCENTER).ready

                for cc in command_centers:
                    # Check if we can afford the upgrade and the Command Center is not already upgrading
                    if self.can_afford(UnitTypeId.ORBITALCOMMAND):
                        cc.build(UnitTypeId.ORBITALCOMMAND)





        # pokud nemame townhall a mame na nej penize, tak ho postav
        else:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.expand_now()

run_game(
     sc2.maps.get("Equilibrium513AIE"),
    [Bot(Race.Terran, TerranBot()), Computer(Race.Protoss, Difficulty.VeryEasy)],
    realtime = False
)