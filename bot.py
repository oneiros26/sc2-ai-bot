import sc2
from sc2.bot_ai import BotAI
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.unit_typeid import UnitTypeId
import time
import math

class TerranBot(BotAI):
    def __init__(self):
        self.scvs_finished_attack = False
        self.first_marine_attack = False
    async def on_step(self, iteration: int):

        if iteration % 5 == 0:
            rounded_time = math.floor(self.time)
            print(rounded_time)

        total_workers = self.units(UnitTypeId.SCV).amount + self.already_pending(UnitTypeId.SCV)
        total_marines = self.units(UnitTypeId.MARINE).amount + self.already_pending(UnitTypeId.MARINE)
        total_marauders = self.units(UnitTypeId.MARAUDER).amount + self.already_pending(UnitTypeId.MARAUDER)
        total_medivacs = self.units(UnitTypeId.MEDIVAC).amount + self.already_pending(UnitTypeId.MEDIVAC)
        total_siegetanks = self.units(UnitTypeId.SIEGETANK).amount + self.already_pending(UnitTypeId.SIEGETANK)
        main_ramp = self.main_base_ramp
        corner_depots = list(main_ramp.corner_depots)
        sorted_depots = sorted(corner_depots, key=lambda p: p.x)
        close_ramp_depot = sorted_depots[0]
        far_ramp_depot = sorted_depots[-1]

        # pokud mame townhall, prirad ho do var townhall
        if self.townhalls:
            townhall = self.townhalls.closest_to(self.start_location)
            townhall_2 = self.townhalls.furthest_to(self.start_location)

            # vycvic 3 SCV proti worker rush strategii
            if total_workers < 15:
                townhall.train(UnitTypeId.SCV)

            # postav SUPPLY DEPOT [14] [0:20 ; 0:17] +3
            elif not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and total_workers >= 15:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=close_ramp_depot)
                print("1st SUPPLY DEPOT built")

            # postav BARRACKS [15] [0:44 ; 0:39] +4
            elif not self.structures(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0 and self.can_afford(UnitTypeId.BARRACKS):
                pos = townhall.position.towards(self.enemy_start_locations[0], 7)
                await self.build(UnitTypeId.BARRACKS, pos)
                print("1st BARRACKS built")

                # ADVANCED STRATEGY, POSTAVIT WALLU ZE BARRACKS A SUPPLY DEPOTU NAD RAMPOU (VOJACI NEMUZOU PROJIT)
                # pos = main_ramp.barracks_in_middle
                # await self.build(UnitTypeId.BARRACKS, pos)

            # postav REFINERY [16] [0:49 ; 0:43] +6
            elif not self.structures(UnitTypeId.REFINERY) and self.structures(UnitTypeId.BARRACKS).amount == 1 and not self.already_pending(UnitTypeId.REFINERY):
                vespenes = self.vespene_geyser.closer_than(15, townhall)
                await self.build(UnitTypeId.REFINERY, vespenes.random)
                print("1st REFINERY built")

            # posli SCV do rafinerie
            elif self.structures(UnitTypeId.REFINERY).ready and self.structures(UnitTypeId.REFINERY).ready.first.assigned_harvesters < 3 and not self.structures(UnitTypeId.FACTORYTECHLAB):
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
                        print("1st BARRACKS REACTOR built")

            # postav dalsi COMMAND CENTER [19] [1:44 ; 1:38] +6
            elif self.can_afford(UnitTypeId.COMMANDCENTER) and self.structures(UnitTypeId.BARRACKSREACTOR) and ((self.structures(UnitTypeId.COMMANDCENTER).amount == 1 and self.structures(UnitTypeId.ORBITALCOMMAND).amount == 0) or (self.structures(UnitTypeId.ORBITALCOMMAND).amount == 1 and self.structures(UnitTypeId.COMMANDCENTER).amount == 0)):
                expansion_location = await self.get_next_expansion()
                if expansion_location:
                    builder = self.workers.closest_to(expansion_location)
                    builder.build(UnitTypeId.COMMANDCENTER, expansion_location)
                    print("2nd COMMANDCENTER built")

            # vylepsi home COMMAND CENTER na ORBITAL COMMAND [19] [1:46 ; 1:38] +8
            elif not self.structures(UnitTypeId.ORBITALCOMMAND) and self.can_afford(UnitTypeId.ORBITALCOMMAND)  and self.structures(UnitTypeId.COMMANDCENTER).amount == 2:
                townhall.build(UnitTypeId.ORBITALCOMMAND)
                print("1st ORBITAL COMMAND built")

            # postav SUPPLY DEPOT [19] [1:50 ; 1:47] +3
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount == 1 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and townhall != townhall_2:
                await self.build(UnitTypeId.SUPPLYDEPOT, far_ramp_depot)
                print("2nd SUPPLYDEPOT built")

            # vycvic 2 MARINES [20]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 2 and self.structures(UnitTypeId.BARRACKSREACTOR):
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BUNKER [23] [2:18 ; 2:15] +3
            elif not self.structures(UnitTypeId.BUNKER) and self.already_pending(UnitTypeId.BUNKER) == 0 and self.can_afford(UnitTypeId.BUNKER) and total_marines >= 2:
                pos = townhall_2.position.towards(self.game_info.map_center, 12)
                await self.build(UnitTypeId.BUNKER, pos)
                print("1st BUNKER built")

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
                print("2nd BARRACKS built")

            elif self.structures(UnitTypeId.BARRACKS).amount == 2 and not self.already_pending(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.BARRACKS):
                target_barracks = self.structures(UnitTypeId.BARRACKS).random
                pos = target_barracks.position.towards(close_ramp_depot, 5)
                await self.build(UnitTypeId.BARRACKS, pos)
                print("3rd BARRACKS built")

            # vylepsi second COMMAND CENTER na ORBITAL COMMAND [29] [3:03 ; 2:50] +12
            elif self.can_afford(UnitTypeId.ORBITALCOMMAND) and (self.structures(UnitTypeId.BARRACKS).amount >= 2 or self.structures(UnitTypeId.BARRACKSREACTOR).amount >= 1) and self.structures(UnitTypeId.ORBITALCOMMAND).amount < 2 and not townhall_2.orders:
                townhall_2.build(UnitTypeId.ORBITALCOMMAND)
                print("2nd ORBITAL COMMAND built")

            # vycvic 4 MARINES [30]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 10 and townhall_2.orders and townhall != townhall_2:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav FACTORY [63] [0:00 ; 4:33]
            elif self.can_afford(UnitTypeId.FACTORY) and not self.structures(UnitTypeId.FACTORY) and self.structures(UnitTypeId.ORBITALCOMMAND).amount == 2 and not self.already_pending(UnitTypeId.FACTORY):
                pos = townhall_2.position.towards(self.enemy_start_locations[0], 6)
                await self.build(UnitTypeId.FACTORY, pos)
                print("1st FACTORY built")

            # postav FACTORY TECH LAB [89] [0:00 ; 6:04]
            elif self.can_afford(UnitTypeId.FACTORYTECHLAB) and not self.structures(UnitTypeId.FACTORYTECHLAB) and not self.already_pending(UnitTypeId.FACTORYTECHLAB) and self.structures(UnitTypeId.FACTORY):
                if self.structures(UnitTypeId.FACTORY).ready.exists:
                    factory = self.structures(UnitTypeId.FACTORY).ready.first
                    if not factory:
                        pass
                    else:
                        factory.build(UnitTypeId.FACTORYTECHLAB)
                        print("1st FACTORY TECH LAB built")

            # vycvic 2 SIEGE TANK
            elif self.can_afford(UnitTypeId.SIEGETANK) and self.structures(UnitTypeId.FACTORYTECHLAB) and not self.already_pending(UnitTypeId.SIEGETANK) and total_siegetanks < 2:
                factory_ready = self.structures(UnitTypeId.FACTORY).ready
                for factory in factory_ready:
                    factory.train(UnitTypeId.SIEGETANK)

            # udelej 1 nebo 2 SIEGE TANK do defense modu
            elif self.units(UnitTypeId.SIEGETANK).amount == 2 and self.siege_def == False:
                for siege in self.units(UnitTypeId.SIEGETANK):
                    self.do(siege(AbilityId.SIEGEMODE_SIEGEMODE))
                self.siege_def = True

            # postav BARRACKS TECH LAB [33] [0:00 ; 3:10]
            elif self.can_afford(UnitTypeId.BARRACKSTECHLAB) and self.structures(UnitTypeId.FACTORYTECHLAB) and not self.structures(UnitTypeId.BARRACKSTECHLAB):
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)
                        print("1st BARRACKS TECH LAB built")

            # postav SUPPLY DEPOT [33] [0:00 ; 3:11]
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount < 3 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.BARRACKSTECHLAB):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall_2)
                print("3rd SUPPLY DEPOT built")

            # vycvic 2 MARINES [34]
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 15 and self.structures(UnitTypeId.SUPPLYDEPOT).amount == 3:
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
                        print("1st BARRACKS TECH LAB built")

            # postav 2 SUPPLY DEPOTY [44] [0:00 ; 3:43]
            elif self.structures(UnitTypeId.SUPPLYDEPOT).amount < 5 and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.BARRACKSTECHLAB):
                front_of_base = townhall_2.position.towards(self.game_info.map_center, distance=15)
                await self.build(UnitTypeId.SUPPLYDEPOT, near=front_of_base)
                print("4th and 5th SUPPLY DEPOTS built")

            # postav 2 RAFINERY [63] [0:00 ; 4:32]
            elif self.structures(UnitTypeId.REFINERY).amount < 3 and self.structures(UnitTypeId.SUPPLYDEPOT).amount == 5 and not self.already_pending(UnitTypeId.REFINERY):
                vespenes = self.vespene_geyser.closer_than(15, townhall_2)
                await self.build(UnitTypeId.REFINERY, vespenes.random)
                print("3rd and 4th REFINERY built")

            # postav ENGINEERING BAY [66] [0:00 ; 4:44]
            elif self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.structures(UnitTypeId.ENGINEERINGBAY) and self.structures(UnitTypeId.REFINERY).amount >= 2 and not self.already_pending(UnitTypeId.ENGINEERINGBAY):
                await self.build(UnitTypeId.ENGINEERINGBAY, near=townhall_2)
                print("1st ENGINEERING BAY built")

            # postav 2 BARRACKS [70] [0:00 ; 4:57]
            elif self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BARRACKS).amount < 4 and self.structures(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.BARRACKS):
                expansion_location = await self.get_next_expansion()
                target_barracks = self.structures(UnitTypeId.BARRACKS).furthest_to(self.start_location)
                pos = target_barracks.position.towards(expansion_location, 5)
                await self.build(UnitTypeId.BARRACKS, pos)
                print("2nd BARRACKS built")

            elif self.can_afford(UnitTypeId.BARRACKS) and self.structures(UnitTypeId.BARRACKS).amount < 5 and self.structures(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.BARRACKS):
                target_barracks = self.structures(UnitTypeId.BARRACKS).furthest_to(self.start_location)
                pos = target_barracks.position.towards(close_ramp_depot, 7)
                await self.build(UnitTypeId.BARRACKS, pos)
                print("3rd BARRACKS built")

            # postav STAR PORT [74] [0:00 ; 5:20]
            elif self.can_afford(UnitTypeId.STARPORT) and not self.structures(UnitTypeId.STARPORT) and not self.already_pending(UnitTypeId.STARPORT) and self.structures(UnitTypeId.BARRACKS).amount >= 5 and self.structures(UnitTypeId.FACTORYTECHLAB):
                await self.build(UnitTypeId.STARPORT, near=townhall)
                print("1st STARCRAFT built")

            # postav BARRACKS REACTOR
            elif self.structures(UnitTypeId.BARRACKSREACTOR).amount < 2 and not self.already_pending(UnitTypeId.BARRACKSREACTOR) and self.can_afford(UnitTypeId.BARRACKSREACTOR) and self.structures(UnitTypeId.REFINERY).amount >= 2:
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSREACTOR)
                        print("2nd BARRACKS REACTOR built")

            # postav BARRACKS TECH LAB
            elif self.structures(UnitTypeId.BARRACKSTECHLAB).amount < 3 and not self.already_pending(UnitTypeId.BARRACKSTECHLAB) and self.can_afford(UnitTypeId.BARRACKSTECHLAB) and self.structures(UnitTypeId.BARRACKSREACTOR).amount >= 2:
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)
                        print("1st BARRACKS TECH LAB")

            # vycvic dalsi MARINES
            elif self.can_afford(UnitTypeId.MARINE) and total_marines < 22 and self.structures(UnitTypeId.BARRACKSTECHLAB).amount >= 3:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # vycvic 5 MARAUDER
            elif self.can_afford(UnitTypeId.MARAUDER) and self.structures(UnitTypeId.BARRACKSTECHLAB).amount >= 3 and self.already_pending(UnitTypeId.MARAUDER) <= 2 and total_marauders < 5:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARAUDER)

            # vycvic 4 SIEGE TANKS
            elif self.can_afford(UnitTypeId.SIEGETANK) and self.structures(UnitTypeId.BARRACKSTECHLAB).amount >= 3 and not self.already_pending(UnitTypeId.SIEGETANK) and total_siegetanks < 4:
                factory_ready = self.structures(UnitTypeId.FACTORY).ready
                for factory in factory_ready:
                    factory.train(UnitTypeId.SIEGETANK)

            # vycvic 6 MEDAVACS
            elif self.can_afford(UnitTypeId.MEDIVAC) and self.structures(UnitTypeId.BARRACKSTECHLAB).amount >= 3 and not self.already_pending(UnitTypeId.MEDIVAC) and total_medivacs < 6:
                starport_ready = self.structures(UnitTypeId.STARPORT).ready
                for starport in starport_ready:
                    starport.train(UnitTypeId.MEDIVAC)

            # TIME TO WIN at 9 min. no matter what
            if self.time >= 540:
                target = self.enemy_start_locations[0]
                marines = self.units(UnitTypeId.MARINE)
                siege_t = self.units(UnitTypeId.SIEGETANK)
                marauders = self.units(UnitTypeId.MARAUDER)
                medivacs = self.units(UnitTypeId.MEDIVAC)

                for marine in marines:
                    self.do(marine.attack(target))
                    # aktivuj STIMPACK na MARINE
                    if not marine.has_buff(BuffId.STIMPACK) and AbilityId.EFFECT_STIM not in marine.orders:
                        marine(AbilityId.EFFECT_STIM)
                for siege in siege_t:
                    self.do(siege.attack(target))
                for marauder in marauders:
                    self.do(marauder.attack(target))
                for medivac in medivacs:
                    damaged_units = self.units.filter(lambda unit: unit.health < unit.health_max)

                    if damaged_units.exists:
                        target = min(damaged_units, key=lambda unit: unit.health)
                        self.do(medivac(AbilityId.MEDIVACHEAL_HEAL, target))
                    else:
                        soldiers = self.units.filter(lambda unit: unit.type_id in {UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK})
                        if soldiers.exists:
                            target = random.choice(soldiers)
                            self.do(medivac.smart(target))
                        else:
                            self.do(medivac.smart(self.start_location))

                scvs = self.units(UnitTypeId.SCV)
                for scv in scvs:
                    self.do(scv.stop())
                await self.distribute_workers()

            # trenuj SCV kdyz nemas co delat
            elif self.can_afford(UnitTypeId.SCV) and total_workers < 32:
                if not self.already_pending(UnitTypeId.SCV) and townhall != townhall_2:
                    townhall.train(UnitTypeId.SCV)
                    townhall_2.train(UnitTypeId.SCV)
                elif not self.already_pending(UnitTypeId.SCV):
                    townhall.train(UnitTypeId.SCV)

            # stav SUPPLY DEPOTS kdyz nemas co delat
            elif self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.structures(UnitTypeId.FACTORYTECHLAB) and self.structures(UnitTypeId.SUPPLYDEPOT).amount < 12:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall)
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall_2)

            # trenuj MARINES kdyz nemas co delat
            elif self.can_afford(UnitTypeId.MARINE) and self.already_pending(UnitTypeId.MARINE) <= 2 and self.units(UnitTypeId.SIEGETANK).amount >= 2:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # vyzkoumej STIMPACK a COMBAT SHIELD - NESAHAT, FUNGUJE
            if self.structures(UnitTypeId.BARRACKSTECHLAB).ready.exists:
                for barracks in self.structures(UnitTypeId.BARRACKS).ready:
                    if barracks.has_add_on:
                        add_on_tag = barracks.add_on_tag
                        add_on = None
                        for structure in self.structures.ready:
                            if structure.tag == add_on_tag:
                                add_on = structure
                                break
                        if add_on:
                            if add_on.type_id == UnitTypeId.BARRACKSTECHLAB:
                                if not self.already_pending_upgrade(UpgradeId.STIMPACK):
                                    self.do(add_on(AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK))
                                    self.do(add_on(AbilityId.RESEARCH_COMBATSHIELD))

            # vyzkoumej TERRAN INFANTRY WEAPONS 1
            if self.structures(UnitTypeId.ENGINEERINGBAY).ready.exists:
                engineering_bay = self.structures(UnitTypeId.ENGINEERINGBAY).ready.first
                if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1) and self.can_afford(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                    self.do(engineering_bay.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1))

            # DEFEND
            defend_radius = 40
            nearby_enemy_units = self.enemy_units.closer_than(defend_radius, self.start_location)
            enemy_base = self.enemy_start_locations[0]
            front_of_base = townhall_2.position.towards(self.game_info.map_center, distance = 12)

            # against worker rush
            if nearby_enemy_units.exists and total_marines < 2:
                self.scvs_finished_attack = True
                scvs = self.units(UnitTypeId.SCV)

                for scv in scvs:
                    self.do(scv.attack(enemy_base))
            elif self.scvs_finished_attack == True:
                scvs = self.units(UnitTypeId.SCV)
                for scv in scvs:
                    self.do(scv.stop())
                await self.distribute_workers()
                self.scvs_finished_attack = False
            else:
                await self.distribute_workers()

            # normal defense
            if nearby_enemy_units.exists and total_marines >= 2:
                marines = self.units(UnitTypeId.MARINE)
                siege_t = self.units(UnitTypeId.SIEGETANK)
                marauders = self.units(UnitTypeId.MARAUDER)
                medivacs = self.units(UnitTypeId.MEDIVAC)
                for marine in marines:
                    self.do(marine.attack(enemy_base))
                    # aktivuj STIMPACK na MARINE
                    if not marine.has_buff(BuffId.STIMPACK) and AbilityId.EFFECT_STIM not in marine.orders:
                        marine(AbilityId.EFFECT_STIM)
                for siege in siege_t:
                    self.do(siege.attack(enemy_base))
                for marauder in marauders:
                    self.do(marauder.attack(enemy_base))
                for medivac in medivacs:
                    damaged_units = self.units.filter(lambda unit: unit.health < unit.health_max)
                    if damaged_units.exists:
                        target = min(damaged_units, key=lambda unit: unit.health)
                        self.do(medivac(AbilityId.MEDIVACHEAL_HEAL, target))
                    else:
                        soldiers = self.units.filter(
                            lambda unit: unit.type_id in {UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.SIEGETANK})
                        if soldiers.exists:
                            target = random.choice(soldiers)
                            self.do(medivac.smart(target))
                        else:
                            self.do(medivac.smart(self.start_location))

            else:
                marines = self.units(UnitTypeId.MARINE)
                marauders = self.units(UnitTypeId.MARAUDER)
                medivacs = self.units(UnitTypeId.MEDIVAC)

                for marine in marines:
                    self.do(marine.move(front_of_base))
                for marauder in marauders:
                    self.do(marauder.move(front_of_base))
                for medivac in medivacs:
                    self.do(medivac.smart(front_of_base))

        # pokud nemame townhall a mame na nej penize, tak ho postav
        else:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.expand_now()

class WorkerRushBot(BotAI):
    async def on_step(self, iteration: int):
        if self.townhalls:
            townhall = self.townhalls.closest_to(self.start_location)
            workers = self.units(UnitTypeId.PROBE)
            enemy_base = self.enemy_start_locations[0]

            for worker in workers:
                self.do(worker.attack(enemy_base))

class AFKBot(BotAI):
    async def on_step(self, iteration: int):
        if self.townhalls:
            await self.distribute_workers()

class BoostedBot(BotAI):
    async def on_step(self, iteration: int):
        await self.distribute_workers()

        if self.townhalls:
            townhall = self.townhalls.closest_to(self.start_location)

            # postav SUPPLY DEPOT
            if not self.structures(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) == 0 and self.can_afford(UnitTypeId.SUPPLYDEPOT):
                await self.build(UnitTypeId.SUPPLYDEPOT, near=townhall)

            # postav BARRACKS
            elif not self.structures(UnitTypeId.BARRACKS) and self.already_pending(UnitTypeId.BARRACKS) == 0 and self.can_afford(UnitTypeId.BARRACKS):
                pos = townhall.position.towards(self.enemy_start_locations[0], 7)
                await self.build(UnitTypeId.BARRACKS, pos)

            # postav REFINERY
            elif not self.structures(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY) and self.can_afford(UnitTypeId.REFINERY):
                vespenes = self.vespene_geyser.closer_than(15, townhall)
                await self.build(UnitTypeId.REFINERY, vespenes.random)

            # posli SCV do rafinerie
            elif self.structures(UnitTypeId.REFINERY).ready and self.structures(UnitTypeId.REFINERY).ready.first.assigned_harvesters < 3 and not self.structures(UnitTypeId.FACTORYTECHLAB):
                refinery = self.structures(UnitTypeId.REFINERY).ready.first
                scv_gas = self.units(UnitTypeId.SCV).first
                scv_gas.gather(refinery)

            # vycvic MARINE
            elif self.units(UnitTypeId.MARINE).amount < 1:
                barracks_ready = self.structures(UnitTypeId.BARRACKS).ready
                for barracks in barracks_ready:
                    barracks.train(UnitTypeId.MARINE)

            # postav BARRACKS TECH LAB
            elif self.can_afford(UnitTypeId.BARRACKSTECHLAB) and self.structures(UnitTypeId.BARRACKS) and not self.structures(UnitTypeId.BARRACKSTECHLAB):
                if self.structures(UnitTypeId.BARRACKS).ready.exists:
                    barracks = self.structures(UnitTypeId.BARRACKS).ready.first
                    if not barracks:
                        pass
                    else:
                        barracks.build(UnitTypeId.BARRACKSTECHLAB)

            # postav ENGINEERING BAY
            elif self.can_afford(UnitTypeId.ENGINEERINGBAY) and not self.structures(UnitTypeId.ENGINEERINGBAY) and not self.already_pending(UnitTypeId.ENGINEERINGBAY):
                await self.build(UnitTypeId.ENGINEERINGBAY, near=townhall)

            # vyzkoumej STIMPACK a COMBAT SHIELD - NESAHAT, FUNGUJE
            if self.structures(UnitTypeId.BARRACKSTECHLAB).ready.exists:
                for barracks in self.structures(UnitTypeId.BARRACKS).ready:
                    if barracks.has_add_on:
                        add_on_tag = barracks.add_on_tag
                        # Search for the add-on in the ready structures+
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
                if not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1) and self.can_afford(
                        UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                    self.do(engineering_bay.research(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1))

            # davej efekt na marine
            for marine in self.units(UnitTypeId.MARINE).ready:
                if not marine.has_buff(BuffId.STIMPACK) and AbilityId.EFFECT_STIM not in marine.orders:
                    marine(AbilityId.EFFECT_STIM)

            for marine in self.units(UnitTypeId.MARINE).ready:
                if BuffId.STIMPACK in marine.buffs:
                    print(f"Marine {marine.tag} has Stimpack activated!")
                else:
                    print(f"Marine {marine.tag} does not have Stimpack activated.")


run_game(
    sc2.maps.get("Equilibrium513AIE"),
    [Bot(Race.Terran, TerranBot()), Computer(Race.Protoss, Difficulty.Hard)],
    realtime = False
)