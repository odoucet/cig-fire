import sys
import math
import time
import copy

# First draft from "starterkit"
# https://raw.githubusercontent.com/Azkellas/a-code-of-ice-and-fire/develop/src/test/starterkit/starter.py

# MAP SIZE
WIDTH = 12
HEIGHT = 12

# OWNER
ME = 0
opponent = 1

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


class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    # Retourne le point dans srcArray le plus proche de point
    # point: Point
    # srcArray: Point[]
    def nearest(self, point, srcArray):
        nearest = None
        nearestDist = None

        for entity in srcArray:
            # on stocke l'appel a distance() car c'est une fction couteuse en CPU
            tmpDist = distance(entity, point)
            if nearest is None or tmpDist < nearestDist:
                nearest = entity
                nearestDist = tmpDist
        return nearest

    # Tri un tableau par distance, du plus proche au plus loin
    def sortNearest(self, point, srcArray):
        return sorted(srcArray, key = lambda src: distance(src, point))


    # Retourne les cases adjacentes, avec un filtre 
    def getAdjacentes(self, point, map, filtre):
        cases = []
        #                 gauche                   droite                 haut                    bas
        combinaisons = [ [point.x-1, point.y], [point.x+1, point.y], [point.x, point.y-1], [point.x, point.y+1]]
        for x,y in combinaisons:
            if x >= 0 and x < WIDTH and y >= 0 and y < HEIGHT and map[x][y] in filtre:
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
        self.nbMinesDuJoueur = 0

        # les positions de defenses, avec des unites dedans à ne pas toucher
        self.defensePositions = []

        # init selfmap
        self.map = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

    def get_my_HQ(self):
        for b in self.buildings:
            if b.type == HQ and b.owner == ME:
                return b


    def get_opponent_HQ(self):
        for b in self.OpponentBuildings:
            if b.type == HQ and b.owner == opponent:
                return b


    # Recupere toutes les cases qui respectent le type demandé
    # (pour éviter de recoder sans arret la même chose)
    def get_points_matching(self, types):
        casesVides = []
        for x in range(WIDTH):
            for y in range(HEIGHT):
                # TODO: refaire cette liste mieux, on peut aller ailleurs
                if self.map[x][y] in types:
                    casesVides.append(Point(x, y))
        return casesVides


    # Strategie de deplacement des unites (Olivier)
    # un truc que la règle ne dit pas de facon claire : si un soldat est sur une case inactive, il meurt !
    def move_units(self):
        # on commence simple : on va a la case vide/adversaire la plus proche

        # on recupere la liste des cases vides
        # TODO: enlever les cases qui ont un adversaire dessus
        casesVides = self.get_points_matching([NEUTRE, INACTIVEOPPONENT, ACTIVEOPPONENT])
        
        for unit in self.units:
            # Defense ? 
            if unit.doNotMove == True:
                continue

            # Strategie Olivier: si niveau 3, on fonce sur l'adversaire le plus proche
            if unit.level == 3:
                if not self.OpponentUnits: 
                    # on va sur la base ennemi
                    destination = self.get_opponent_HQ()
                else:
                    # on va taper de l'unité ennemie
                    destination = Point.nearest(self, unit, self.OpponentUnits)

                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                # on met a jour notre carte avec là où devrait etre notre unité
                self.map[destination.x][destination.y] = ACTIVE
                unit.x = destination.x
                unit.y = destination.y
                continue

            # ici on devrait boucler jusqu'à trouver une bonne destination : 
            # - pas déjà ciblée par une autre unité
            # - 
            destination = Point.nearest(self, unit, casesVides)
            if (destination is not None): 
                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                # que quelqu'un d'autre n'y aille pas
                casesVides.remove(destination)
            else:
                # destination == HQ ennemi ! 
                destination = self.get_opponent_HQ()
                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')

    # Stratégie d'entrainement des unites
    # La règle n'est pas claire: en fait on doit entrainer les unités sur une case vide forcément
    # et on ne peut pas "upgrader" une unité : il faut la construire avec un gros level directement
    # TODO: optimiser ces boucles, je suis sûr qu'on fait du taff pour rien
    def train_units(self):

        # Strategie: on créé pleins de soldats, et on fait du niveau 2 quand il ne reste que X cases vides
        if len(self.get_points_matching([NEUTRE])) < 30 or len(self.units) >= 10:

            # Olivier: choix de stratégie: on fait que des mecs niveau 3
            # on spawn au plus proche des troupes ennemies proches de notre base
            for level in [3]: # ici [3, 2] pour construire des unités de niveau 2 aussi
                # boucle sur les troupes ennemies
                ennemis = Point.sortNearest(self, self.get_my_HQ(), self.OpponentUnits)

                for case in ennemis:
                    # on trouve une case à nous autour ?
                    casesAutour = Point.getAdjacentes(self, case, self.map, [ACTIVE, NEUTRE])
                    for case in casesAutour:
                        taken = False
                        for unit in self.units:
                            if distance(unit, case) == 0: 
                                taken = True
                                break
                        
                        if taken == False and self.gold >= (Unit.TRAINING[level]) and self.income >= Unit.ENTRETIEN[level]:
                            self.actions.append(f'TRAIN {level} {case.x} {case.y}')
                            self.gold   -= Unit.TRAINING[level]
                            self.income -= Unit.ENTRETIEN[level]
                            self.map[case.x][case.y] = ACTIVE # case prise maintenant

        else: 
            casesANous = self.get_points_matching([ACTIVE])
            casesSpawn = []

            # On ajoute à ces cases là les inactives / neutres 
            for case in casesANous:
                # TODO: on peut optimiser en spawnant sur des cases actives de l'ennemi ? A tester
                casesSpawn.extend(Point.getAdjacentes(self, case, self.map, [INACTIVE, INACTIVEOPPONENT, NEUTRE]))

            # et on deduplique
            casesSpawn = list(dict.fromkeys(casesSpawn))

            # ici on entraine que du niveau 1
            while self.gold >= Unit.TRAINING[1] and self.income >= Unit.ENTRETIEN[1]:
                # on entraine sur une case à nous, la plus proche du QG adverse
                
                # pour le premier tour il faut ajouter les voisins ...
                if len(casesANous) == 1:
                    if (self.map[0][0] == ACTIVE):
                        casesSpawn.extend([Point(1,0), Point(0,1)])
                    else:
                        casesSpawn.extend([Point(10,11), Point(11,10)])

                case = Point.nearest(self, self.get_opponent_HQ(), casesSpawn)
                if case is not None:
                    self.actions.append(f'TRAIN 1 {case.x} {case.y}')
                    self.income -= Unit.ENTRETIEN[1]
                    self.gold   -= Unit.TRAINING[1]
                    self.map[case.x][case.y] = ACTIVE # case prise maintenant
                    # la case va etre prise donc on ne la considere plus
                    casesSpawn.remove(case)
                else:
                    break

    # Construction des mines
    # Il faut que la mine nous appartienne (case ACTIVE), avec personne dessus
    def build_mines(self):

        for mine in self.mines: 
            # si on a assez d'argent et que la case est possédée, active et non occupée.
            if self.map[mine.x][mine.y] in [ACTIVE]: 
                if self.gold >= 20+4*self.nbMinesDuJoueur: 
                    # on verifie qu'on a personne dessus et pas de batiment
                    yadumonde = False
                    for building in self.buildings:
                        if distance(building, mine) == 0:
                            yadumonde = True
                            break
                    for unit in self.units:
                        if distance(unit, mine) == 0:
                            yadumonde = True
                            break

                    if (yadumonde == False):
                        self.actions.append(f'BUILD MINE {mine.x} {mine.y}')
                        self.gold -= 20+4*self.nbMinesDuJoueur
                        self.nbMinesDuJoueur += 1


    # Top priorité : protéger la base, en spawnant un soldat de niveau suffisant sur la ligne de combat d'une unité adverse
    def protect_base(self):

        # On essaie d'avoir des tourelles sur les super points (defenseMap >= 20)
        for x in range(WIDTH):
            for y in range(HEIGHT): 
                if self.defenseMap[x][y] is not None and self.defenseMap[x][y] >= 20:
                    # on check qu'on a pas deja une tour
                    built = False
                    for building in self.buildings:
                        if building.type == TOWER and distance(building, Point(x, y)) == 0:
                            built = True
                            break
                    # et pas sur une mine
                    for mine in self.mines:
                        if distance(mine, Point(x, y)) == 0:
                            built = True
                            break
                    if built == False and self.gold > 15:
                        self.actions.append(f'BUILD TOWER {x} {y}')
                        self.gold -= 15
                        #todo: marquer case occupée


        # on se focalise sur les unités ennemies les plus proches
        units = Point.sortNearest(self, self.get_my_HQ(), self.OpponentUnits)
        if units is None:
            return

        for unit in units: 
            if distance(unit, self.get_my_HQ()) >= 3:
                break
            
            # par quel côté ?
            if self.get_my_HQ().x == 0:
                if unit.x == 1 and unit.y == 1:
                    spawnPoints = [ Point(0, 1), Point(1,0) ]
                else:
                    spawnPoints = [ Point.nearest(self, unit, [ Point(0, 1), Point(1,0)]) ]
            else:
                if unit.x == 1 and unit.y == 1:
                    spawnPoints = [ Point(11, 10), Point(10,11) ]
                else:
                    spawnPoints = [ Point.nearest(self, unit, [ Point(11, 10), Point(10,11)]) ]
            
            # pas de verif de tune,c'est une question de vie ou de mort
            for spawnPoint in spawnPoints: 
                self.actions.append(f'TRAIN {unit.level} {spawnPoint.x} {spawnPoint.y}')
                self.gold   -= Unit.TRAINING[unit.level]
                self.income -= Unit.ENTRETIEN[unit.level]
                self.defensePositions.append(spawnPoint)

    def init(self):
        numberMineSpots = int(input())
        for _ in range(numberMineSpots):
            x, y = [int(j) for j in input().split()]
            self.mines.append(Mine(x, y))


    # Construction d'une carte avec les points de defense importants chez nous
    # Pour se faire, pour chaque case à nous on calcule notre surface si on la perd
    # On va s'en servir pour mettre des tourelles par exemple
    def calcul_carte_defense(self):
        self.defenseMap = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]
        # calcul du moment: on a combien de case à nous ? 
        nbCasesANous = 0
        
        # on calcule une premiere carte, sur les cases à nous, avec la distance à notre QG
        mapANous = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]
        # cleanup: 
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.map[x][y] != ACTIVE:
                    mapANous[x][y] = None
                else:
                    nbCasesANous += 1
                    mapANous[x][y] = -1

        # si on a pas bcoup de cases en fait on s'en fout, soit c'est trop tôt, soit on est mort
        #if nbCasesANous < 15:
        #    return

        # en itératif on incremente en partant du QG
        aTraiter = [ [self.get_my_HQ(), 0] ]
        debugi = 0
        while len(aTraiter) > 0 and debugi < 5000:
            debugi += 1
            element, distance = aTraiter.pop(0)
            mapANous[element.x][element.y] = distance
            cases = Point.getAdjacentes(self, element, self.map, [ACTIVE])
            for case in cases:
                if mapANous[case.x][case.y] == -1 or mapANous[case.x][case.y] >= distance+1:
                    aTraiter.append([ case, distance + 1])

        # A partir d'ici, on a donc mapANous avec les distances au QG
        self.debugMapANous = mapANous

        # on passe maintenant au taff
        for x in range(WIDTH):
            for y in range(HEIGHT): 
                # on a assez de temps ?
                if self.check_timeout():
                    sys.stderr.write("TIMEOUT REACHED in calcul_carte_defense("+str(x)+","+str(y)+") WE EXITED BEFORE DEFENSEMAP COMPLETE\n")
                    return
                
                if self.map[x][y] == ACTIVE:
                    # si on est trop pres de notre QG ça sert à rien
                    if mapANous[x][y] < 3:
                        continue

                    # la grosse formule commence ici
                    # Etape 1 - on copie la map 
                    # IL FAUT ABSOLUMENT UTILISER DEEPCOPY CAR ON A UN TABLEAU DE TABLEAU!
                    newMap =  copy.deepcopy(self.map)

                    # Ensuite on la modifie pour virer la case courante
                    newMap[x][y] = INACTIVE

                    # Puis pour faire ça bien, on fait un calcul récursif en prenant les cases adjacentes
                    aTraiter = Point.getAdjacentes(self, Point(x, y), newMap, [ACTIVE])
                    debugi = 0
                    while len(aTraiter) > 0 and debugi < 5000:
                        debugi += 1
                        element = aTraiter.pop(0)
                        # si l'element a au moins un voisin inférieur c'est bon, sinon non
                        keepit = False
                        for voisin in Point.getAdjacentes(self, element, newMap, [ACTIVE]):
                            if mapANous[voisin.x][voisin.y] < mapANous[element.x][element.y]:
                                keepit = True
                                break
                        if keepit is False:
                            newMap[element.x][element.y] = INACTIVE
                            aTraiter.extend(Point.getAdjacentes(self, Point(element.x, element.y), newMap, [ACTIVE]))


                    # Maintenant on calcule le nbre de cases à nous: 
                    nbCases = 0
                    for tmpx in range(WIDTH):
                        for tmpy in range(HEIGHT):
                            if newMap[tmpx][tmpy] == ACTIVE:
                                nbCases += 1
                    self.defenseMap[x][y] = abs(nbCasesANous - nbCases)
        debugMap(self.defenseMap)

    # Return false if timeout near and we should stop what we are doing
    def check_timeout(self)-> bool:
        if (time.time()-self.startTime) > 0.05:
            return True
        return False 


    def update(self):
        self.units.clear()
        self.OpponentUnits.clear()
        self.buildings.clear()
        self.OpponentBuildings.clear()
        self.actions.clear()

        self.gold = int(input())
        self.startTime = time.time()
        self.income = int(input())
        self.opponent_gold = int(input())
        self.opponent_income = int(input())
        self.nbMinesDuJoueur = 0

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
                    self.nbMinesDuJoueur += 1
            else:
                self.OpponentBuildings.append(Building(owner, building_type, x, y))

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


    def build_output(self):
        # TODO: calculer cette carte que plus tard dans la game non ?
        self.calcul_carte_defense()

        self.protect_base()
        self.build_mines()
        self.train_units()
        self.move_units()


    def output(self):
        if self.actions:
            print(';'.join(self.actions))
        else:
            print('WAIT')
        sys.stderr.write("Time spent in this round: "+str(self.getTotalTime())+"ms")

    # get total time in ms
    def getTotalTime(self)-> int:
        return round((time.time() - self.startTime)*1000)

# calcule la distance entre deux cases. Hyper utilise donc mis en global
def distance(f, t) -> float:
    # optimisation si mm point:
    if f.x == t.x and f.y == t.y:
        return 0

    # On peut pas aller en diagonale donc en fait c'est simple
    return abs(f.x - t.x)+abs(f.y - t.y)


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
