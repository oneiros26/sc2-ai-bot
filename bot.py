import sc2
from sc2.bot_ai import BotAI
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
import time

class TerranBot(BotAI):
    async def on_step(self, iteration: int):
        # kolik iteraci probehlo
        print(f"Worker amount: {self.workers.amount}\n"
              f"Supply Used: {self.supply_used}\n"
              f"Current minerals: {self.minerals}")

        total_workers = self.units(UnitTypeId.SCV).amount + self.already_pending(UnitTypeId.SCV)
        total_marines = self.units(UnitTypeId.MARINE).amount + self.already_pending(UnitTypeId.MARINE)
        main_ramp = self.main_base_ramp
        corner_depots = list(main_ramp.corner_depots)
        sorted_depots = sorted(corner_depots, key=lambda p: p.x)
        close_ramp_depot = sorted_depots[0]
        far_ramp_depot = sorted_depots[-1]

        # vzichni nepracujici zpatky do prace
        await self.distribute_workers()

        # pokud mame townhall, prirad ho do var townhall
        if self.townhalls:
            townhall = self.townhalls.closest_to(self.start_location)
            townhall_2 = self.townhalls.furthest_to(self.start_location)

            # postav SUPPLY DEPOT [14] [0:20 ; 0:17] +3
            if not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=close_ramp_depot)

            # postav BARRACKS [15] [0:44 ; 0:39] +4
            elif not self.structures(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0 and self.can_afford(UnitTypeId.BARRACKS):
                pos = townhall.position.towards(self.enemy_start_locations[0], 7)
                await self.build(UnitTypeId.BARRACKS, pos)

                # ADVANCED STRATEGY, POSTAVIT WALLU ZE BARRACKS A SUPPLY DEPOTU NAD RAMPOU (VOJACI NEMUZOU PROJIT)
                # pos = main_ramp.barracks_in_middle
                # await self.build(UnitTypeId.BARRACKS, pos)

            # postav REFINERY [16] [0:49 ; 0:43] +6
            elif not self.structures(UnitTypeId.REFINERY) and self.structures(UnitTypeId.BARRACKS).amount == 1 and not self.already_pending(UnitTypeId.REFINERY):
                vespenes = self.vespene_geyser.closer_than(15, townhall)
                await self.build(UnitTypeId.REFINERY, vespenes.random)

            # posli SCV do rafinerie
            elif self.structures(UnitTypeId.REFINERY).ready and self.structures(UnitTypeId.REFINERY).ready.first.assigned_harvesters < 3:
                refinery = self.structures(UnitTypeId.REFINERY).ready.first
                scv_gas = self.units(UnitTypeId.SCV).first
                scv_gas.gather(refinery)

            # postav BARRACKS REACTOR [19] [1:33 ; 1:26] +7
            elif not self.structures(UnitTypeId.BARRACKSREACTOR) and not self.already_pending(UnitTypeId.BARRACKSREACTOR) and self.can_afford(UnitTypeId.BARRACKSREACTOR) and self.structures(UnitTypeId.BARRACKS):
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSREACTOR)

            # postav dalsi COMMAND CENTER [19] [1:44 ; 1:38] +6
            elif self.can_afford(UnitTypeId.COMMANDCENTER) and self.structures(UnitTypeId.BARRACKSREACTOR) and ((self.structures(UnitTypeId.COMMANDCENTER).amount == 1 and self.structures(UnitTypeId.ORBITALCOMMAND).amount == 0) or (self.structures(UnitTypeId.ORBITALCOMMAND).amount == 1 and self.structures(UnitTypeId.COMMANDCENTER).amount == 0)):
                expansion_location = await self.get_next_expansion()
                if expansion_location:
                    builder = self.workers.closest_to(expansion_location)
                    builder.build(UnitTypeId.COMMANDCENTER, expansion_location)

            # vylepsi home COMMAND CENTER na ORBITAL COMMAND [19] [1:46 ; 1:38] +8
            elif not self.structures(UnitTypeId.ORBITALCOMMAND) and self.can_afford(UnitTypeId.ORBITALCOMMAND)  and self.structures(UnitTypeId.COMMANDCENTER).amount == 2:
                townhall.build(UnitTypeId.ORBITALCOMMAND)

            # postav SUPPLY DEPOT [19] [1:50 ; 1:47] +3
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount == 1 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and townhall != townhall_2:
                await self.build(UnitTypeId.SUPPLYDEPOT, far_ramp_depot)

            # vycvic 2 MARINES [20]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 2 and self.structures(UnitTypeId.BARRACKSREACTOR):
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BUNKER [23] [2:18 ; 2:15] +3
            elif not self.structures(UnitTypeId.BUNKER) and self.already_pending(UnitTypeId.BUNKER) == 0 and self.can_afford(UnitTypeId.BUNKER) and total_marines >= 2:
                pos = townhall_2.position.towards(self.enemy_start_locations[0], 4)
                await self.build(UnitTypeId.BUNKER, pos)

            # vycvic 4 MARINES [23]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 6 and self.structures(UnitTypeId.BUNKER):
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav 2 BARRACKS [26] [2:23 ; 2:23] +0
            elif self.structures(UnitTypeId.BARRACKS).amount < 2 and not self.already_pending(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BUNKER):
                target_barracks = self.structures(UnitTypeId.BARRACKS).random
                pos = target_barracks.position.towards(self.enemy_start_locations[0], 5)
                await self.build(UnitTypeId.BARRACKS, pos)

            elif self.structures(UnitTypeId.BARRACKS).amount == 2 and not self.already_pending(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.BARRACKS):
                target_barracks = self.structures(UnitTypeId.BARRACKS).random
                pos = target_barracks.position.towards(close_ramp_depot, 5)
                await self.build(UnitTypeId.BARRACKS, pos)

            # vylepsi second COMMAND CENTER na ORBITAL COMMAND [29] [3:03 ; 2:50] +12
            elif self.can_afford(UnitTypeId.ORBITALCOMMAND) and (self.structures(UnitTypeId.BARRACKS).amount >= 2 or self.structures(UnitTypeId.BARRACKSREACTOR).amount >= 1) and self.structures(UnitTypeId.ORBITALCOMMAND).amount < 2 and not townhall_2.orders:
                townhall_2.build(UnitTypeId.ORBITALCOMMAND)

            # vycvic 4 MARINES [30]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 8 and townhall_2.orders and townhall != townhall_2:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BARRACKS TECH LAB [33] [0:00 ; 3:10]
            elif self.can_afford(UnitTypeId.BARRACKSTECHLAB) and self.structures(UnitTypeId.ORBITALCOMMAND).amount == 2 and not self.structures(UnitTypeId.BARRACKSTECHLAB):
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)

            # postav SUPPLY DEPOT [33] [0:00 ; 3:11]
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount < 3 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.BARRACKSTECHLAB):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall_2)

            # vycvic 2 MARINES [34]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 10 and self.structures(UnitTypeId.SUPPLYDEPOT).amount == 3:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BARRACKS TECH LAB [34] [0:00 ; 3:18]
            elif self.can_afford(UnitTypeId.BARRACKSTECHLAB) and total_marines >= 10 and self.structures(UnitTypeId.BARRACKSTECHLAB).amount < 2:
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)

            # postav 2 SUPPLY DEPOTY [44] [0:00 ; 3:43]
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount < 5 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.BARRACKSTECHLAB):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall_2)

            # postav 2 RAFINERY [63] [0:00 ; 4:32]
            elif self.structures(UnitTypeId.REFINERY).amount < 3 and self.structures(UnitTypeId.SUPPLYDEPOT).amount == 5:
                vespenes = self.vespene_geyser.closer_than(15, townhall_2)
                await self.build(UnitTypeId.REFINERY, vespenes.random)

            # postav FACTORY [63] [0:00 ; 4:33]
            # nechal jsem postavit 2. On v tutorialu ma jen jednu a zmeni ten addon, to je ale zbytecne komplikovany za me
            elif self.can_afford(UnitTypeId.FACTORY) and self.structures(UnitTypeId.FACTORY).amount < 2 and self.structures(UnitTypeId.REFINERY).amount == 3 and not self.already_pending(UnitTypeId.FACTORY):
                pos = townhall_2.position.towards(self.enemy_start_locations[0], 10)
                await self.build(UnitTypeId.FACTORY, pos)

            # postav ENGINEERING BAY [66] [0:00 ; 4:44]
            elif self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.structures(UnitTypeId.ENGINEERINGBAY) and self.structures(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.ENGINEERINGBAY):
                await self.build(UnitTypeId.ENGINEERINGBAY, near=townhall_2)

            # postav 2 BARRACKS [70] [0:00 ; 4:57]
            elif self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BARRACKS).amount < 5 and self.structures(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.BARRACKS):
                expansion_location = await self.get_next_expansion()
                target_barracks = self.structures(UnitTypeId.BARRACKS).furthest_to(self.start_location)
                pos = target_barracks.position.towards(expansion_location, 5)
                await self.build(UnitTypeId.BARRACKS, pos)

            # postav FACTORY REACTOR [74] [0:00 ; 5:18]
            elif self.can_afford(UnitTypeId.FACTORYREACTOR) and not self.structures(UnitTypeId.FACTORYREACTOR) and not self.already_pending(UnitTypeId.FACTORYREACTOR) and self.structures(UnitTypeId.FACTORY):
                if self.structures(UnitTypeId.FACTORY).ready.exists:
                    factory = self.structures(UnitTypeId.FACTORY).ready.first
                    if not factory:
                        pass
                    else:
                        factory.build(UnitTypeId.FACTORYREACTOR)

            # postav STAR PORT [74] [0:00 ; 5:20]
            elif self.can_afford(UnitTypeId.STARPORT) and not self.structures(UnitTypeId.STARPORT) and not self.already_pending(UnitTypeId.STARPORT) and self.structures(UnitTypeId.FACTORYREACTOR) and self.structures(UnitTypeId.FACTORYTECHLAB):
                await self.build(UnitTypeId.STARPORT, near=townhall)

            # postav REFINERY
            elif self.structures(UnitTypeId.REFINERY).amount < 4 and self.structures(UnitTypeId.STARPORT):
                vespenes = self.vespene_geyser.closer_than(15, townhall)
                await self.build(UnitTypeId.REFINERY, vespenes.random)

            # postav BARRACKS REACTOR
            elif self.structures(UnitTypeId.BARRACKSREACTOR).amount < 2 and not self.already_pending(UnitTypeId.BARRACKSREACTOR) and self.can_afford(UnitTypeId.BARRACKSREACTOR) and self.structures(UnitTypeId.REFINERY).amount >= 4:
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSREACTOR)

            # postav BARRACKS TECH LAB
            elif self.structures(UnitTypeId.BARRACKSTECHLAB).amount < 3 and not self.already_pending(UnitTypeId.BARRACKSTECHLAB) and self.can_afford(UnitTypeId.BARRACKSTECHLAB) and self.structures(UnitTypeId.BARRACKSREACTOR).amount >= 2:
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)

            # vycvic 2 MARINES
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 12 and self.structures(UnitTypeId.BARRACKSTECHLAB).amount >= 3:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav FACTORY TECH LAB [89] [0:00 ; 6:04]
            elif self.can_afford(UnitTypeId.FACTORYTECHLAB) and not self.structures(UnitTypeId.FACTORYTECHLAB) and not self.already_pending(UnitTypeId.FACTORYTECHLAB) and self.structures(UnitTypeId.FACTORYREACTOR) and self.structures(UnitTypeId.FACTORY).amount >= 2:
                if self.structures(UnitTypeId.FACTORY).ready.exists:
                    factory = self.structures(UnitTypeId.FACTORY).ready.first
                    if not factory:
                        pass
                    else:
                        factory.build(UnitTypeId.FACTORYTECHLAB)

            # vycvic MARAUDER

            # vycvic 4 SIEGE TANKS a 8 MEDIVACS





            # trenuj MARINES kdyz nemas co delat
                elif self.can_afford(UnitTypeId.MARINE) and self.structures(UnitTypeId.FACTORYTECHLAB):
                    pass # dodelat

            # trenuj SCV kdyz nemas co delat
            elif self.can_afford(UnitTypeId.SCV) and total_workers < 32:
                if not self.already_pending(UnitTypeId.SCV) and townhall != townhall_2:
                    townhall.train(UnitTypeId.SCV)
                    townhall_2.train(UnitTypeId.SCV)
                elif not self.already_pending(UnitTypeId.SCV):
                    townhall.train(UnitTypeId.SCV)










            #DEFEND            funguje zatim spatne jen pro zacatek
            # Check if the enemy is attacking or there are enemy units near
            if self.enemy_units.exists or self.enemy_structures.exists:
                # Gather all available Marines
                marines = self.units(UnitTypeId.MARINE).ready
                if marines:
                    # Get the enemy position (you can also use a specific enemy unit, structure, or location)
                    enemy_position = self.enemy_units.closest_to(
                        self.start_location).position if self.enemy_units else self.enemy_structures.closest_to(
                        self.start_location).position

                    # Move the Marines to the enemy location
                    for marine in marines:
                        # Move the Marines towards the enemy location
                        self.do(marine.move(enemy_position))

                    # Optionally, command the Marines to attack the enemy
                    # If we want them to automatically attack when in range
                    for marine in marines:
                        self.do(marine.attack(enemy_position))
                    print("Marines gathered to defend.")








            # vyzkoumej STIMPACK a COMBAT SHIELD - NESAHAT, FUNGUJE
            if self.structures(UnitTypeId.BARRACKSTECHLAB).amount == 1:
                for barracks in self.structures(UnitTypeId.BARRACKS).ready:
                    if barracks.has_add_on:
                        add_on_tag = barracks.add_on_tag
                        # Search for the add-on in the ready structures
                        add_on = None
                        for structure in self.structures.ready:
                            if structure.tag == add_on_tag:
                                add_on = structure
                                break
                        if add_on:
                            if add_on.type_id == UnitTypeId.BARRACKSTECHLAB:
                                # Check if Stimpack research is already pending
                                if not self.already_pending_upgrade(UpgradeId.STIMPACK):
                                    self.do(add_on(AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK))
                                    self.do(add_on(AbilityId.RESEARCH_COMBATSHIELD))

            # vyzkoumej TERRAN INFANTRY WEAPONS 1
            if self.structures(UnitTypeId.ENGINEERINGBAY).ready.exists:
                engineering_bay = self.structures(UnitTypeId.ENGINEERINGBAY).ready.first
                if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1) and self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                    self.do(engineering_bay.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1))

        # pokud nemame townhall a mame na nej penize, tak ho postav
        else:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.expand_now()

run_game(
     sc2.maps.get("Equilibrium513AIE"),
    [Bot(Race.Terran, TerranBot()), Computer(Race.Protoss, Difficulty.VeryEasy)],
    realtime = False
)