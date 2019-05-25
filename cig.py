import sys
import time
import copy
import random
import math
from itertools import chain
import re

# MAP SIZE
WIDTH = 12
HEIGHT = 12

# OWNER
ME = 0
OPPONENT = 1

# BUILDING TYPE
HQ = 0
MINE = 1
TOWER = 2

# TILE TYPE
NEANT = "#"
NEUTRE = "."
ACTIVE = "O"
INACTIVE = "o"
ACTIVEOPPONENT = "X"
INACTIVEOPPONENT = "x"

# Compilations re
TRAIN_PATTERN = re.compile("^TRAIN ([0-9]*) ([0-9]*) ([0-9]*)$")

# On met notre distanceMap en global pour simplifier le code ... et désolé c'est dégueu :(
distanceMap = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

# debugTiming
debugTiming = dict()

class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f'({self.x},{self.y})'

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y)

    def __hash__(self):
        return hash(('x', self.x,
                 'y', self.y))

    # Retourne le point dans srcArray le plus proche de point
    # srcArray: Point[]
    def nearest(self, srcArray):
        nearest = None
        nearestDist = None

        for entity in srcArray:
            # on stocke l'appel a distance() car c'est une fction couteuse en CPU
            tmpDist = distance(entity, self)
            if nearest is None or tmpDist < nearestDist:
                nearest = entity
                nearestDist = tmpDist
        return nearest

    # Tri un tableau par distance, du plus proche au plus loin
    def sortNearest(self, srcArray):
        return sorted(srcArray, key = lambda src: distance(src, self))


    # Retourne les cases adjacentes, avec un filtre 
    def getAdjacentes(self, map, filtre = None):
        cases = []

        # ON RETOURNE LES CASES EN PRIORITE: droite/bas si on commence en 0,0, gauche/HAUT sinon
        if (map[0][0] == ACTIVE):
            #                 droite              bas                 haut                 gauche               
            combinaisons = [  [self.x+1, self.y], [self.x, self.y+1] ]
            combinaisons.extend(([self.x, self.y-1],  [self.x-1, self.y]))
        else:
            combinaisons = [ [self.x-1, self.y], [self.x, self.y-1] ]
            combinaisons.extend( ([self.x+1, self.y], [self.x, self.y+1]))
        
        for x,y in combinaisons:
            if x >= 0 and x < WIDTH and y >= 0 and y < HEIGHT:
                if filtre is None or map[x][y] in filtre:
                    cases.append(Point(x, y))
        return cases


class Unit (Point):
    # Couts entrainement / entretien.
    TRAINING  = [ 0, 10, 20, 30]
    ENTRETIEN = [ 0, 1, 4, 20 ]

    def __init__(self, owner: int, id: int, level: int, x: int, y: int):
        self.owner = owner
        self.id = id
        self.level = level

        # par defaut on peut bouger :)
        self.doNotMove = False
        Point.__init__(self, x, y)


class Building (Point):
    def __init__(self, owner, type, x: int, y: int):
        self.owner = owner
        self.type = type
        Point.__init__(self, x, y)

class Mine (Point): 
    def __init__(self, x: int, y: int):
        Point.__init__(self, x, y)

class Game:
    def __init__(self):
        self.buildings = []
        self.OpponentBuildings = []
        self.units = []
        self.OpponentUnits = []
        self.actions = []
        self.mines = []
        self.gold = 0
        self.income = 0
        self.opponent_gold = 0
        self.opponent_income = 0
        self.nbMines = 0
        self.nbOpponentMines = 0
        self.tour = 0

        # Si on a posé notre tourelle de défense en 2,2 ou 9,9
        self.tourelleDefense = False

        # les positions de defenses, avec des unites dedans à ne pas toucher
        self.defensePositions = []

        # init carte du jeu
        self.map = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

        # spawnMap
        self.spawnMap = [ [ True for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

        # le cache de decoupage
        self.cacheCalculDecoupeX = [ None for x in range( WIDTH ) ]
        self.cacheCalculDecoupeY = [ None for y in range( HEIGHT ) ]

        # coordonnées de notre QG (cache)
        self.hq = None
        # coordonnées du QG ennemi (cache)
        self.opponentHq = None

    def get_my_HQ(self)->Point:
        return self.hq


    def get_opponent_HQ(self)->Point:
        return self.opponentHq

    # Retourne les positions de notre case adjacente qui sera notre prochaine position si on veut se rendre en X,Y
    # Vérifie aussi si le déplacement est possible, donc si on récupère None, alors c'est qu'on peut pas y aller.
    def get_next_pos(self, nous: Unit, destination):
        casesPossibles = nous.getAdjacentes(self.map)
        for case in casesPossibles:
            if (distanceMap[destination.x][destination.y][case.x][case.y] == 
                distanceMap[destination.x][destination.y][nous.x][nous.y]-1 and 
                self.can_spawn_level(case.x, case.y, nous.level)
            ):
                # ça semble marcher
                return case
        # si on est là c'est que non, ça marche pas :(
        return None

    # Recupere toutes les cases qui respectent le type demandé
    # (pour éviter de recoder sans arret la même chose)
    def get_points_matching(self, types):
        casesVides = []
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.map[x][y] in types:
                    casesVides.append(Point(x, y))
        return casesVides

    # Met à jour la position d'une unité (putain de pass-by-reference-mais-en-fait-non en Python)
    def update_unit_pos(self, owner, id, position: Point):
        if owner == ME:
            for unit in self.units:
                if unit.id == id:
                    unit.x = position.x
                    unit.y = position.y
                    self.map[position.x][position.y] = ACTIVE
                    self.update_spawnMap()
                    return

        if owner == OPPONENT:
            for unit in self.OpponentUnits:
                if unit.id == id:
                    unit.x = position.x
                    unit.y = position.y
                    self.map[position.x][position.y] = ACTIVEOPPONENT
                    self.update_spawnMap()
                    return


    # Strategie de deplacement des unites (Olivier)
    # un truc que la règle ne dit pas de facon claire : si un soldat est sur une case inactive, il meurt !
    def move_units(self):
        # on commence simple : on va a la case vide/adversaire la plus proche

        # on bouge les unites au plus proche du QG ennemi d'abord
        for unit in self.get_opponent_HQ().sortNearest(self.units):
            # Defense ? 
            if unit.doNotMove == True:
                continue

            # Strategie Olivier: si niveau 3, on fonce sur l'adversaire / la tour / le batiment le plus proche
            if unit.level == 3:
                # on va taper de l'unité / du batiment ennemi
                tmpEnnemi = self.OpponentUnits.copy()
                tmpEnnemi.extend(self.OpponentBuildings)
                destination = unit.nearest(tmpEnnemi)

                # get_next_pos vérifie déjà si le déplacement est possible
                nextPos = self.get_next_pos(unit, destination)
                if nextPos is not None:
                    self.actions.append(f'MOVE {unit.id} {nextPos.x} {nextPos.y}')
                    # virer l'unite/building si y'a
                    for unit in self.OpponentUnits:
                        if unit == nextPos:
                            self.OpponentUnits.remove(unit)
                            break
                    for building in self.OpponentBuildings:
                        if building == nextPos:
                            self.OpponentBuildings.remove(building)
                            break
                    # maj de notre position (fait tout le taff)
                    self.update_unit_pos(ME, unit.id, nextPos)
                    continue

            # Si ennemi de mm niveau a coté on bouge pas
            doNotMove = False
            for case in unit.getAdjacentes(self.map):
                for ennemi in self.OpponentUnits:
                    if case == ennemi:
                        # on bouge pas
                        doNotMove = True
                        break
            
            if doNotMove:
                continue
            
            # on regarde si on a une case vide à proximité. On récupère les cases par priorité
            voisins = unit.getAdjacentes(self.map, [NEUTRE, INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT])
            moved = False
            while moved is False and len(voisins) > 1:
                voisin = voisins.pop(0)
                if self.can_spawn_level(voisin.x, voisin.y, unit.level):
                    self.actions.append(f'MOVE {unit.id} {voisin.x} {voisin.y}')
                    self.update_unit_pos(ME, unit.id, voisin)
                    moved = True
                    continue

            if moved:
                continue

            # pas de voisin correct, on va donc à la case intéressante la plus proche
            destination = unit.nearest(self.get_points_matching([NEUTRE, INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT]))
            if destination is not None: 
                nextPos = self.get_next_pos(unit, destination)
                if nextPos is not None:
                    #debug:
                    if unit.id == 3:
                        debugMsg(f"L260 nextPos={nextPos} , currentLevel={unit.level}")

                    self.actions.append(f'MOVE {unit.id} {nextPos.x} {nextPos.y}')
                    self.update_unit_pos(ME, unit.id, nextPos)
                    # TODO: virer l'unite/building si y'a ...
                    continue

            # ici c'est vraiment qu'on peut rien faire :/
            sys.stderr.write(f"move_units#{unit.id}({unit.x},{unit.y}), destination({destination}) impossible\n")

            

    # Stratégie d'entrainement des unites
    # Les niveaux > 1 doivent se faire SUR un ennemi histoire de gagner du temps :)
    def train_units(self):
        #DEBUG
        if (self.tour > 15):
            return

        # Strategie: on créé pleins de soldats, et on fait du niveau 2 quand il ne reste que X cases vides
        if len(self.get_points_matching([NEUTRE])) < 30 or len(self.units) >= 10:

            # Boucle 1: est-ce qu'on peut dégommer des niveaux 2 ou 3 en spawnant dessus ?
            # on la joue defense: on spawn sur les mecs qui nous mettent en danger
            for ennemi in self.get_my_HQ().sortNearest(self.OpponentUnits):
                if ennemi.level == 1:
                    # petite merde, on te considère même pas!
                    continue
                else:
                    # on considere qu'il est forcément 2 car on va l'écraser avec un 3
                    ennemi.level = 2
                
                # plus rapide que can_spawn_level() car niveau 3 fait ce qu'il veut, nananère
                if (len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0 and 
                self.gold >= (Unit.TRAINING[3]) and self.income >= Unit.ENTRETIEN[3]):
                    self.actions.append(f'TRAIN 3 {ennemi.x} {ennemi.y}')
                    self.gold   -= Unit.TRAINING[3]
                    self.income -= Unit.ENTRETIEN[3] -1 # on prend une case, ça rapporte
                    self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                    self.units.append(Unit(ME, 1, 3, ennemi.x, ennemi.y))
                    self.OpponentUnits.remove(ennemi) # on vire l'ennemi
                    self.update_spawnMap()
                    #debugMsg(f"Spawn Unit3({ennemi}) sur la tronche de {ennemi.id}")
            
            # Boucle 2 : est-ce qu'on peut dégommer une TOUR ennemie en spawnant un niveau 3 dessus ? ^^
            for ennemi in self.get_my_HQ().sortNearest(self.OpponentBuildings):
                if ennemi.type != TOWER:
                    continue
                
                if (len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0 and 
                self.gold >= (Unit.TRAINING[3]) and self.income >= Unit.ENTRETIEN[3]):
                    self.actions.append(f'TRAIN 3 {ennemi.x} {ennemi.y}')
                    self.gold   -= Unit.TRAINING[3]
                    self.income -= Unit.ENTRETIEN[3]  -1 # on prend une case, ça rapporte
                    self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                    self.units.append(Unit(ME, 1, 3, ennemi.x, ennemi.y))
                    self.OpponentBuildings.remove(ennemi) # on vire l'ennemi
                    self.update_spawnMap()

            # Boucle 4: est-ce qu'on peut dégommer un niveau 1 en spawnant un 2 dessus ? 
            for ennemi in self.get_my_HQ().sortNearest(self.OpponentUnits):
                if ennemi.level > 1:
                    continue
                # debug:seed=5862311708367631400

                if len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0:
                    # deux boucles: si on peut faire du niveau 2, ou du niveau 3
                    for level in range(min(3, ennemi.level+1), 3):
                        if (self.can_spawn_level(ennemi.x, ennemi.y, level) and 
                        self.gold >= (Unit.TRAINING[ennemi.level+1]) and self.income >= Unit.ENTRETIEN[ennemi.level+1]):
                            self.actions.append(f'TRAIN {ennemi.level+1} {ennemi.x} {ennemi.y}')
                            self.gold   -= Unit.TRAINING[ennemi.level+1]
                            self.income -= Unit.ENTRETIEN[ennemi.level+1] -1 # on prend une case, ça rapporte
                            self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                            self.units.append(Unit(ME, 1, ennemi.level+1, ennemi.x, ennemi.y))
                            self.OpponentUnits.remove(ennemi) # on vire l'ennemi
                            self.update_spawnMap()
                            break
            
        if self.check_timeout():
            debugMsg("TIMEOUT in move_units() apres boucle 4")
            return

        # Et si il reste de la tune: 
        if self.gold < 10 or self.income == 0:
            return

        # on garde l'algo (pas terrible) qu'on a déjà, pour le moment
        # TODO: optimiser ça :)
        casesANous = self.get_points_matching([ACTIVE])
        casesSpawn = []

        # On ajoute à ces cases là les inactives / neutres / ennemi
        for case in casesANous:
            # on peut optimiser en spawnant sur des cases actives de l'ennemi ? A tester
            casesSpawn.extend(case.getAdjacentes(self.map, [INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT, NEUTRE]))

        # on maximise la zone autour de notre QG
        casesSpawn = self.hq.sortNearest(list(dict.fromkeys(casesSpawn)))

        # ici on entraine que du niveau 1
        while len(casesSpawn) > 0 and self.gold >= Unit.TRAINING[1] and self.income >= Unit.ENTRETIEN[1]:
            # on entraine sur une case à nous, la plus proche du QG adverse
            case = casesSpawn.pop(0)

            if self.can_spawn_level(case.x, case.y, 1):
                self.actions.append(f'TRAIN 1 {case.x} {case.y}')
                # on baisse pas l'income, car on spawn sur une nouvelle case == rapporte 1 d'income
                self.gold   -= Unit.TRAINING[1]
                self.map[case.x][case.y] = ACTIVE # case prise maintenant donc on peut spawn les adjacentes :)
                self.update_spawnMap()
                
                casesSpawn.extend(case.getAdjacentes(self.map, [INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT, NEUTRE]))
                casesSpawn = self.hq.sortNearest(list(dict.fromkeys(casesSpawn)))

    # Construction des mines
    # Seulement si on est en expansion de territoire, donc qu'il reste bcoup de NEUTRAL
    # Il faut que la mine nous appartienne (case ACTIVE), avec personne dessus
    # et d'un point de vue économique on en veut pas plus d'une d'avance sur l'ennemi (sauf si max tunes)
    def build_mines(self):
        
        # on pause pas de mines si reste peu de points à prendre sur la carte (sauf si max tune)
        if len(self.get_points_matching([NEUTRE])) < 10 and self.gold < 150+(20+4*self.nbMines):
            return

        # d'un point de vue économique on en veut pas plus d'une d'avance sur l'ennemi (sauf si max tunes)
        if self.nbMines >= self.nbOpponentMines+1 and self.gold < 50+(20+4*self.nbMines):
            self.actions.append(f'MSG NOBUILDMINE gold < {50+(20+4*self.nbMines)}')
            return

        for mine in self.get_my_HQ().sortNearest(self.mines): 
            # si on a assez d'argent et que la case est possédée, active et non occupée.
            if self.map[mine.x][mine.y] in [ACTIVE]: 
                # si ennemi <= 3 cases, on construit pas
                ennemi = mine.nearest(self.OpponentUnits)
                if ennemi is not None and distance(ennemi, mine) <= 3:
                    continue
                # on verifie la tune et qu'on a personne dessus et pas de batiment
                if self.gold >= 20+4*self.nbMines and self.spawnMap[mine.x][mine.y]: 
                    self.actions.append(f'BUILD MINE {mine.x} {mine.y}')
                    self.gold -= 20+4*self.nbMines
                    self.nbMines += 1
                    if self.nbMines >= self.nbOpponentMines+1:
                        break


    # Top priorité : protéger la base, en spawnant un soldat de niveau suffisant sur la ligne de combat d'une unité adverse
    # TODO: on peut mieux faire ici, et avoir des tourelles à de meilleurs endroits
    def protect_base(self):
        # Optim:
        if self.gold < 15:
            return
        
        # J'aime l'idée de mettre une tourelle en 2,2 ou 9,9 si l'ennemi se rapproche, pour éviter les "rush" comme
        # certains joueurs le font.
        # Algo v2: si distance < (goldEnnemi+income)/10

        if self.tourelleDefense == False:
            ennemis = self.get_my_HQ().sortNearest(self.OpponentUnits)
            # En fait, ce n'est pas le mec le plus proche forcément le plus dangereux, donc dans le doute on vérifie tout le monde !
            for ennemi in ennemis: 
                # on fait distance-1 car il pourra se déplacer d'une case avant de mener son attaque

                # On force le mieux avant de calculer quelque chose de bien. Avant 2,2 et 9,9
                if distance(ennemi, self.get_my_HQ())-1 <= (self.opponent_gold+self.opponent_income)/10:
                    if self.get_my_HQ().x == 0:
                        positionTourelle = Point(1, 1)
                    else:
                        positionTourelle = Point(10, 10)
                    
                    # faire gaffe si y'a une mine ...
                    for building in self.buildings:
                        if building == positionTourelle:
                            if self.get_my_HQ().x == 0:
                                positionTourelle = Point(1, 1)
                            else:
                                positionTourelle = Point(10, 10)
                            break
                    
                    self.tourelleDefense = True
                    self.actions.append(f'BUILD TOWER {positionTourelle.x} {positionTourelle.y}')
                    self.gold -= 15
                    self.buildings.append(Building(ME, TOWER, positionTourelle.x, positionTourelle.y))
                    break
                #else:
                #    sys.stderr.write(f"protect_base sur ({ennemi.x},{ennemi.y}): distance={distance(ennemi, self.get_my_HQ())-1} > {(self.opponent_gold+self.opponent_income)/10}\n")



        # Sauvegarde de de la dernière chance : on spawn des unités au porte de notre base: 
        # on se focalise sur les unités ennemies les plus proches
        for unit in self.get_my_HQ().sortNearest(self.OpponentUnits): 
            if distance(unit, self.get_my_HQ()) > 3:
                break
            
            # par quel côté ?
            if self.get_my_HQ().x == 0:
                if unit.x == 1 and unit.y == 1:
                    spawnPoints = [ Point(0, 1), Point(1,0) ]
                else:
                    spawnPoints = [ unit.nearest( [ Point(0, 1), Point(1,0)]) ]
            else:
                if unit.x == 10 and unit.y == 10:
                    spawnPoints = [ Point(11, 10), Point(10,11) ]
                else:
                    spawnPoints = [ unit.nearest( [ Point(11, 10), Point(10,11)]) ]
            
            # pas de verif de tune,c'est une question de vie ou de mort
            for spawnPoint in spawnPoints: 
                # on spawn un level superieur
                if unit.level == 3:
                    unit.level = 2 # on fait style, on va spawn un level+1
                self.actions.append(f'TRAIN {unit.level+1} {spawnPoint.x} {spawnPoint.y}')
                self.gold   -= Unit.TRAINING[unit.level+1]
                self.income -= Unit.ENTRETIEN[unit.level+1]
                self.defensePositions.append(spawnPoint)


    # Debug du jeu !
    def init(self):
        numberMineSpots = int(input())
        for _ in range(numberMineSpots):
            x, y = [int(j) for j in input().split()]
            self.mines.append(Mine(x, y))


    # Réécrit totalement !
    # On met dans cette carte les points d'intérêts pour des tourelles. Ce sont des positions stratégiques sur la carte
    def calcul_carte_defense(self):
        self.defenseMap = [ [ 0 for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

        # On commence par les 4 cases du milieu
        for x in range(5, 6):
            for y in range(5, 6):
                self.defenseMap[x][y] = 10
        
        # TODO: trouver les passages souvent utilisés. Peut se calculer au premier round
        

    # Pose de tourelle sur la defenseMap (prioritaire par rapport à l'achat d'unités)
    def pose_tourelle(self):
        # pour être sûr ...
        self.update_spawnMap()

        for case in self.get_opponent_HQ().sortNearest(self.get_points_matching([ACTIVE])):
            if self.gold < 15:
                return

            if self.defenseMap[case.x][case.y] >= 10:
                # on peut poser ?
                # une tour c'est comme une unité de niveau 1:p
                # TODO: verifier si on a une tourelle pas loin
                if self.can_spawn_level(case.x, case.y, 1) is True and distance(case, case.nearest(self.buildings)) >= 3 and case not in self.mines:
                    debugMsg(f"BUILDTOWER({case}) spawnMap={self.spawnMap[case.x][case.y]}")
                    self.actions.append(f'BUILD TOWER {case.x} {case.y}')
                    self.gold -= 15
                    # une par tour max
                    return


    # Construction de tours avec la tune restante
    def build_towers(self):
        if self.gold < 50:
            return

        # on cherche une case à nous pas loin du QG ennemi (dist <= 5)
        towerCases = self.get_opponent_HQ().sortNearest( self.get_points_matching([ACTIVE]) )
        for case in towerCases:
            # tune ? 
            if self.gold < 50:
                break
            
            if distance(case, self.get_opponent_HQ()) > 5:
                break

            # check construction
            if self.spawnMap[case.x][case.y]:
                self.actions.append(f'BUILD TOWER {case.x} {case.y}')
                self.gold -= 15

    # Return false if timeout near and we should stop what we are doing
    def check_timeout(self)-> bool:
        if self.tour <= 1:
            timeout = 1
        else:
            timeout = 0.045
        if (time.time() - self.startTime) > timeout:
            return True
        return False

    # return True si une case est vide (personne dessus) et n'est pas un mur
    # EXCEPTION DU QG ADVERSE: c'est une case vide :p
    def case_vide(self,x,y)->bool:
        if self.map[x][y]  == NEANT:
            return False
        vide = True
        for unit in self.units:
            if unit.x ==x and unit.y == y:
                vide = False
                break
        for unit in self.OpponentUnits:
            if unit.x ==x and unit.y == y:
                vide = False
                break
        for unit in self.buildings:
            if unit.x ==x and unit.y == y:
                vide = False
                break
        for unit in self.OpponentBuildings:
            if unit.x == x and unit.y == y and unit.type != HQ:
                vide = False
                break

        return vide

    def update(self):
        self.units.clear()
        self.OpponentUnits.clear()
        self.buildings.clear()
        self.OpponentBuildings.clear()
        self.actions.clear()

        self.tour += 1

        self.gold = int(input())
        self.startTime = time.time()
        self.income = int(input())
        self.opponent_gold = int(input())
        self.opponent_income = int(input())
        self.nbMines = 0
        self.nbOpponentMines = 0
        self.cacheCalculDecoupeX = [ None for x in range( WIDTH ) ]
        self.cacheCalculDecoupeY = [ None for y in range( HEIGHT ) ]

        for y in range(HEIGHT):
            line = input()
            x=0
            for char in list(line):
                self.map[x][y] = char
                x += 1

        building_count = int(input())
        for _ in range(building_count):
            owner, building_type, x, y = [int(j) for j in input().split()]
            if (owner == ME):
                self.buildings.append(Building(owner, building_type, x, y))
                if building_type == MINE:
                    self.nbMines += 1
                elif building_type == HQ:
                    self.hq = Point(x, y)
            else:
                self.OpponentBuildings.append(Building(owner, building_type, x, y))
                if building_type == HQ:
                    self.opponentHq = Point(x, y)
                elif building_type == MINE:
                    self.nbOpponentMines += 1

        unit_count = int(input())
        for _ in range(unit_count):
            owner, unit_id, level, x, y = [int(j) for j in input().split()]
            if (owner == ME):
                obj = Unit(owner, unit_id, level, x, y)

                # On defend ?
                for defensePoint in self.defensePositions:
                    if distance(obj, defensePoint) == 0: 
                        obj.doNotMove = True
                self.units.append(obj)
            else:
                self.OpponentUnits.append(Unit(owner, unit_id, level, x, y))

        # spawnMap
        self.update_spawnMap()

        # Cartes des distances.
        # techniquement, pour le pathfinding il faudrait calculer la carte des distances pour chaque point possible.
        # et bah en fait c'est exactement ce qu'on va faire car ça calcule super vite et qu'on a une seconde sur ce run !
        # et on réintegre la fonction distance() qui se basera dessus (juste aller chercher des coordonnées au bon endroit)
        # NOTE: distanceMap est une variable *GLOBALE* (oui c'est mal)
        if distanceMap[0][0] is None:
            self.calcul_distance_map()

        # de la marge sur l'income après le tour 10 pour pas se mettre à sec
        if self.tour >= 10:
            self.income -= 15
        
        # MAJ du temps:
        debugTiming['update'] = time.time() - self.startTime 

    def update_spawnMap(self):
        # carte des spawns, avec les positions sur lesquelles on peut spawn (cases vides): 
        self.spawnMap = [ [ True for y in range( HEIGHT ) ] for x in range( WIDTH ) ]
        # on enleve les cases impossibles:
        for case in self.get_points_matching([NEANT]):
            self.spawnMap[case.x][case.y] = False
        for case in self.units:
            self.spawnMap[case.x][case.y] = False
        for case in self.buildings:
            self.spawnMap[case.x][case.y] = False


    # verifie si on peut spawn une unite de niveau LEVEL sur la case en question
    # ignoreAdjacente = ignore le test de case adjacente (quand on fait des projections par exemple)
    def can_spawn_level(self, x: int, y: int, level: int, ignoreAdjacente = False)->bool:
        if self.spawnMap[x][y] == False:
            return False

        # et on doit avoir une case adjacente !
        if ignoreAdjacente is False and len(Point(x, y).getAdjacentes(self.map, [ACTIVE])) == 0:
            return False

        if level == 3:
            # on peut tout faire
            return True

        for unit in self.OpponentUnits:
            if unit == Point(x, y) and unit.level >= level:
                return False
        
        # on verifie les tourelles
        for building in self.OpponentBuildings:
            # si la case est déjà à nous rien à foutre :p
            if building.type == TOWER and (building == Point(x, y) or (self.map[x][y] not in [ACTIVE] and Point(x, y) in building.getAdjacentes(self.map))):
                return False
        
        # bah maintenant rien n'empeche :)
        return True


    def calcul_distance_map(self):
        p = Pathfinding()
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.map[x][y] != NEANT:
                    distanceMap[x][y] = p.buildDistanceMap(self.map, Point(x, y))


    # Calcul si une capture directe est possible, c'est à dire en spawnant pleins d'unités jusqu'au QG ennemi
    # Si oui, alors on gagne en un coup \o/
    def calcul_capture_directe(self)->bool:
        # Notre tune == distance max
        # comme on fait ce calcul à chaque tour, case la plus proche de l'ennemi == forcément une unité

        for unitDepart in self.get_opponent_HQ().sortNearest(self.units):
            # on verifie si economiquement c'est viable
            if distance(unitDepart, self.get_opponent_HQ()) > self.gold/10:
                continue

            found = False

            # ah! si on est ici c'est que c'est théoriquement possible. On verifie maintenant que chaque case de la solution est libre/battable
            currentGold = self.gold # on met de coté pour pas tout casser
            currentDistance = distance(unitDepart, self.get_opponent_HQ())
            currentPos = unitDepart # position courante
            actions = []
            sys.stderr.write(f"Unit({unitDepart.x},{unitDepart.y}): curDist={currentDistance}, curGold={currentGold} ")
            while currentDistance > 0 and currentGold > 0:
                # on fait des trucs
                found = False
                for voisin in currentPos.getAdjacentes(self.map):
                    # on veut pas de mur :p
                    if self.map[voisin.x][voisin.y] == NEANT:
                        continue

                    # on verifie le chemin le plus court
                    if distance(voisin, self.get_opponent_HQ()) != currentDistance-1:
                        continue

                    # on verifie que la case est vide
                    # TODO: améliorer ici pour chercher plsieurs chemins ...
                    for level in [1, 2, 3]:
                        if self.can_spawn_level(voisin.x, voisin.y, level, True):
                            currentPos = voisin
                            currentDistance -= 1
                            currentGold -= Unit.TRAINING[level]
                            found = True
                            actions.append(f'TRAIN {level} {voisin.x} {voisin.y}')
                            break
                        # ici on teste si y'a un mec de niveau 2 ou 3 qu'on peut butter


                # si on a rien trouvé c'est mort pour partir de la
                if found == False:
                    break
            
            # au fait c'est bon ?
            sys.stderr.write(f"distFinale: {currentDistance}, gold={currentGold}, found={found}\n")
            if found == True and currentDistance == 0 and currentGold >= 0:
                self.actions.extend(actions)
                self.actions.append("MSG LONG LIVE THE KING") # pour reconnaitre qu'on est dans cette strat'
                return True # oui !

        # fin de l'algo, pas fini donc False
        return False


    # Strategie de decoupe de l'adversaire : 
    # on vérifie x et y avec 4 <= x ou y <= 8 soit 5+5 == 10 boucles.
    # Pour chaque ligne/colonne : 
    #     - on vérifie si la map est "facile", donc pas de mur au milieu ou ce genre de trucs (bref, NEANT accepte qu'aux extremités)
    #     - on regarde si on a une unite sur la ligne, si on peut construire sur toute la ligne (tune)
    #     - A partir de là, on calcule "combien" ça fait perdre de tunes à l'adversaire. TILE=1 ; UNIT=sa valeur
    #     - on garde la strat si coût*2 < (tune perdue par l'adversaire)
    #     On ordonne les stratégies (plus grosse perte pour l'ennemi en premier)
    #     On applique la meilleure
    def calcul_decoupe_adversaire(self)->bool:
        scoresDecoupe = [] # on stockera un tableau avec [x => 4, score => 99] et on ordonnera par le champ score

        # OPTIM: sert à rien de découper avant le tour 10, on a pas la tune pour :)
        if self.tour < 10:
            return False

        for x in range(4, 9):
            scoresDecoupe.append( {"x": x, "score": self.calcul_decoupe(x, None)} )
        for y in range(4, 9):           
            scoresDecoupe.append( {"y": y, "score": self.calcul_decoupe(None, y)} )
        
        # on ordonne les scores
        scores = sorted(scoresDecoupe, key = lambda i: i['score'], reverse=True)

        if len(scores) == 0:
            return False
                
        # on prend juste la meilleure :)

        obj = scores.pop(0)

        # on veut au moins 1 au score: 
        if obj['score'] < 1:
            return False
        
        if 'x' in obj:
            sys.stderr.write(f"DecoupeX({obj['x']})={obj['score']}\n")
            self.actions.extend(self.cacheCalculDecoupeX[obj['x']])
        elif 'y' in obj:
            sys.stderr.write(f"DecoupeY({obj['y']})={obj['score']}\n")
            self.actions.extend(self.cacheCalculDecoupeY[obj['y']])
        else:
            self.actions.append(f"ERROR: CODE INVALIDE EXECUTE") # que ce soit un peu visuel ...
        
        # On rejoue les actions TRAIN (en grepant ce qu'on fait), pour mettr à jour gold et income
        # comme ça on peut encore spawn des unites apres :p
        for action in self.actions:
            match = TRAIN_PATTERN.match(action)
            if match is not None:
                level = int(match.group(1))
                x = int(match.group(2))
                y = int(match.group(3))
                self.gold   -= Unit.TRAINING[level]
                self.income -= Unit.ENTRETIEN[level] -1 # on prend une case, ça rapporte
                self.map[x][y] = ACTIVE # case prise maintenant :D
                self.units.append(Unit(ME, 1, level, x, y))
                #todo: virer les adversaires qu'on a écrasé lamentablement
        self.update_spawnMap()

        return True

        

    # algo de calcul de decoupe ligne par ligne/ col par col
    def calcul_decoupe(self, x = None, y = None)->float:
        if x is None and y is None:
            return 0 # pas normal
        
        # on en profite pour garder un tableau avec les operations. Comme on calcule, autant pas faire le taff deux fois
        actions = []

        # Calculer combien perd l'adversaire. C'est le plus simple, ça permet de voir si ça a un intérêt
        # TODO: prendre en compte si l'ennemi a une tour dans la zone "découpée" : lui permet de garder des cases et perd sans doute de son intéret ...
        argentPerdu = 0
        cases = self.get_points_matching([ACTIVEOPPONENT])
        for case in cases:
            # si on decoupe en vertical + HQ(0,0):
            if self.hq.x == 0 and y is None and case.x <= x:
                argentPerdu += 1

            # si on découpe en horizontal + HQ(0,0):
            elif self.hq.x == 0 and x is None and case.y <= y:
                argentPerdu += 1

            # si on decoupe en vertical + HQ(1,11):
            if self.hq.x == 11 and y is None and case.x >= x:
                argentPerdu += 1

            # si on découpe en horizontal + HQ(11,11):
            elif self.hq.x == 11 and x is None and case.y >= y:
                argentPerdu += 1 

        # Armee: 
        for unit in self.OpponentUnits:
            # si on decoupe en vertical + HQ(0,0):
            if self.hq.x == 0 and y is None and unit.x <= x:
                argentPerdu += Unit.TRAINING[unit.level]

            # si on découpe en horizontal + HQ(0,0):
            elif self.hq.x == 0 and x is None and unit.y <= y:
                argentPerdu += Unit.TRAINING[unit.level]
            
            # si on decoupe en vertical + HQ(11,11):
            if self.hq.x == 11 and y is None and unit.x >= x:
                argentPerdu += Unit.TRAINING[unit.level]

            # si on découpe en horizontal + HQ(11,11):
            elif self.hq.x == 11 and x is None and unit.y >= y:
                argentPerdu += Unit.TRAINING[unit.level]

        # on veut qu'il perde au moins deux unites ou une T2
        if argentPerdu < 20:
            return 0
        
        # On part de notre unite et on incrémente vers la droite si on peut construire
        costBuild = 0

        # on vérifie si la map est "facile"
        # donc pas de mur au milieu ou ce genre de trucs (bref, NEANT accepte qu'aux extremités)
        if y is None:
            #######CE MORCEAU EST COPIE/COLLE PLUS BAS, PUTAIN DE CODE DE MERDE C'EST VRAIMENT DEGUEU ######
            start = 0
            end   = WIDTH-1
            while self.map[x][start] == NEANT and start < WIDTH:
                start += 1

            while self.map[x][end] == NEANT and end >= 0:
                end -= 1

            if start == WIDTH-1 or end == 0:
                # Toute la ligne pas bonne ? bizarre
                #sys.stderr.write(f"calcul_decoupe({x},{y}: ligne vide :(")
                return 0

            # on verifie qu'on a pas de mur entre les deux
            # TODO: on verifie qu'on a TOUT ou que c'est neutral "AVANT" ou "APRES", et on change start/end en consequence
            for tmpy in range(start, end):
                if self.map[x][tmpy] != NEANT:
                    continue

                # mur au milieu, on ajuste start/end: 
                # test qu'on a tout à gauche: 
                on_a_tout_a_gauche = True
                on_a_tout_a_droite = True
                for tmp2y in range(0, tmpy):
                    if self.map[x][tmp2y] not in [NEANT, ACTIVE, INACTIVE]:
                        on_a_tout_a_gauche = False
                        break
                
                # test qu'on a tout à droite: 
                for tmp2y in range(tmpy, WIDTH):
                    if self.map[x][tmp2y] not in [NEANT, ACTIVE, INACTIVE]:
                        on_a_tout_a_droite = False
                        break

                if on_a_tout_a_gauche == False and on_a_tout_a_droite == False:
                    debugMsg(f"calcul_decoupe({x},none): mur au milieu et on a pas tout a gauche ou droite")
                    return 0
                
                if on_a_tout_a_gauche:
                    start = tmpy
                    break
                if on_a_tout_a_droite:
                    end = tmpy
                    break

            # comme on le disait plus haut, c'est forcément une unité qui est la plus proche
            unitStart = None
            for unit in self.opponentHq.sortNearest(self.units):
                # l'unité est sur la bonne ligne
                if unit.x == x:
                    unitStart = unit
                    break
            
            if unitStart is None:
                return 0

            # vers en bas / en haut
            for tmpy in chain(range(unitStart.y+1, end+1), range(unitStart.y-1, start-1, -1)):
                # c'est déjà à nous ? 
                if self.map[x][tmpy] in [ACTIVE, NEANT]:
                    # on a la case, ça coute rien :)
                    continue
   
                goodToGo = False
                for level in [1, 2, 3]:
                    # TODO: verifier qu'on explose pas le budget
                    if self.can_spawn_level(x, tmpy, level, True):
                        actions.append(f"TRAIN {level} {x} {tmpy}")
                        costBuild += Unit.TRAINING[level]
                        goodToGo = True
                        break
                
                # on peut pas :(
                if goodToGo == False:
                    return 0
            # coute rien car on a toute la ligne
            if costBuild == 0:
                return 0

        # faire pareil quand 'y' est défini
        else:
            #######CE MORCEAU EST COPIE/COLLE PLUS HAUT, PUTAIN DE CODE DE MERDE C'EST VRAIMENT DEGUEU ######
            start = 0
            end   = WIDTH-1
            while self.map[start][y] == NEANT and start < HEIGHT:
                start += 1

            while self.map[end][y] == NEANT and end >= 0:
                end -= 1

            if start == HEIGHT-1 or end == 0:
                return 0

            # on verifie qu'on a pas de mur entre les deux
            # TODO: on verifie qu'on a TOUT ou que c'est neutral "AVANT" ou "APRES", et on change start/end en consequence
            for tmpx in range(start, end):
                if self.map[tmpx][y] != NEANT:
                    continue

                # mur au milieu, on ajuste start/end: 
                # test qu'on a tout au dessus: 
                on_a_tout_dessus = True
                on_a_tout_dessous = True
                for tmp2x in range(0, tmpx):
                    if self.map[tmp2x][y] not in [NEANT, ACTIVE, INACTIVE]:
                        on_a_tout_dessus = False
                        break
                
                # test qu'on a tout dessous
                for tmp2x in range(tmpx, HEIGHT):
                    if self.map[tmp2x][y] not in [NEANT, ACTIVE, INACTIVE]:
                        on_a_tout_dessous = False
                        break

                if on_a_tout_dessus == False and on_a_tout_dessous == False:
                    debugMsg(f"calcul_decoupe(none,{y}): mur au milieu et on a pas tout dessus/dessous")
                    return 0
                
                if on_a_tout_dessus:
                    start = tmpx
                    break
                if on_a_tout_dessous:
                    end = tmpx
                    break

            # - on regarde si on a une unite sur la ligne au moins
            unitStart = None

            for unit in self.opponentHq.sortNearest(self.units):
                # sur la bonne ligne
                if unit.y == y:
                    unitStart = unit
                    break
            
            if unitStart is None:
                return 0

            # vers gauche / Droite
            debugMsg(f" tmpyChain(y={y}) unitstart:{unitStart}, start={start}, end={end}")
            for tmpx in chain(range(unitStart.x+1, end+1), range(unitStart.x-1, start-1, -1)):
                # c'est déjà à nous ? 
                if self.map[tmpx][y] in [ACTIVE, NEANT]:
                    # on a la case, ça coute rien :)
                    continue
   
                goodToGo = False
                for level in [1, 2, 3]:
                    # todo: verifier qu'on explose pas le budget
                    if self.can_spawn_level(tmpx, y, level, True):
                        actions.append(f"TRAIN {level} {tmpx} {y}")
                        costBuild += Unit.TRAINING[level]
                        goodToGo = True
                        break
                
                # on peut pas :(
                if goodToGo == False:
                    return 0
            # si on a déjà toute la ligne en bref :p
            if costBuild == 0:
                return 0
            ######FIN DU COPIER COLLE DEGUEU ########

        # si ca coute plus cher que ce qu'on a, ça sert à rien
        if self.gold < costBuild:
            debugMsg(f"calcul_decoupe({x},{y})=FALSE: cout {costBuild} > argent {self.gold}\n")
            return 0

        #sys.stderr.write(f"({x}, none) actions={actions}\n")

        
        # on stock les actions
        if y is None:
            self.cacheCalculDecoupeX[x] = actions
        elif x is None:
            self.cacheCalculDecoupeY[y] = actions

        # coût < (tune perdue par l'adversaire)
        debugMsg(f"calcul_decoupe({x},{y})=TRUE: argentPerdu={argentPerdu} costBuild={costBuild} start={start} end={end}\n")
        return (argentPerdu/costBuild)

    def timingFunc(self, funcName):
        tmp = time.time()
        r = funcName()
        debugTiming[funcName.__name__] = time.time() - tmp
        return r

    def build_output(self):
        self.timingFunc(self.calcul_carte_defense)

        # deplacement des unites
        self.timingFunc(self.move_units)

        # On peut gagner en un tour ?
        if self.timingFunc(self.calcul_capture_directe):
            return

        # Calcul si on peut decouper l'adversaire
        self.timingFunc(self.calcul_decoupe_adversaire)

        # Tourelles défensives
        if self.tour >= 10:
            self.timingFunc(self.pose_tourelle)

        # on a encore de la tune ? on essaie !
        self.timingFunc(self.protect_base)
        self.timingFunc(self.build_mines)
        self.timingFunc(self.train_units)

        # il reste de la tune ? on ajoute des tours :)
        if not self.check_timeout():
            self.timingFunc(self.build_towers)


    def output(self):
        if self.actions:
            print(';'.join(self.actions))
        else:
            print('WAIT')
        
        # Temps mis dans chaque fonction: 
        totalTime = self.getTotalTime()

        sys.stderr.write("TOUR #"+str(self.tour)+": "+str(totalTime)+"ms - ")
        if totalTime == 0:
            return


        for key, value in sorted(debugTiming.items(), reverse=True, key=lambda x: x[1]):
            sys.stderr.write(key+": "+str(round(value*1000/totalTime*100))+"% ")
        
        # Si on veut recup la carte: 
        debugPythonMap(self.map)

    # get total time in ms
    def getTotalTime(self)-> int:
        return round((time.time() - self.startTime)*1000)


class Pathfinding:
    # construit une carte des distances basé sur macarte, par rapport à position.
    # on la veut générique, donc si position n'est pas un angle faut que ça marche quand même.
    # argument facultatif: maxDist pour calculer qu'un bout de la carte
    def buildDistanceMap(self, macarte, position, murs = [NEANT], maxDist = 99):
        tmpcarte = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]
        
        # en itératif on incremente en partant du QG
        aTraiter = [ [position, 0] ]
        debugi = 0
        while len(aTraiter) > 0 and debugi < 500:
            debugi += 1
            element, distance = aTraiter.pop(0)

            # si on a deja fait en mieux
            if tmpcarte[element.x][element.y] is not None and tmpcarte[element.x][element.y] <= distance:
                continue
            
            tmpcarte[element.x][element.y] = distance

            # si distance max atteinte, on quitte
            if (distance >= maxDist):
                continue
            
            cases = element.getAdjacentes(macarte)
            for case in cases:
                # si c'est un mur on passe: 
                if macarte[case.x][case.y] in murs:
                    continue
                
                if tmpcarte[case.x][case.y] is None or tmpcarte[case.x][case.y] > distance and [ case, distance + 1] not in aTraiter:
                    aTraiter.append([ case, distance + 1])
        
        return tmpcarte
        
# calcule la distance entre deux cases. Hyper utilise donc mis en global
# On peut pas aller en diagonale donc en fait c'est simple
# on utilise la distanceMap de f et on cherche la valeur de t
def distance(f: Point, t: Point) -> int:
    return distanceMap[f.x][f.y][t.x][t.y]


def debugMap(macarte, loops = 0):
    sys.stderr.write("*** DEBUG CARTE (loops: "+str(loops)+")***\n")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if macarte[x][y] is None:
                sys.stderr.write(" **")
            else:
                sys.stderr.write(f" {str(macarte[x][y]):2s}")
        sys.stderr.write("\n")
    sys.stderr.write("\n")

def debugPythonMap(macarte):
    sys.stderr.write(str(macarte)+"\n")

def debugMsg(msg):
    sys.stderr.write(str(msg)+"\n")