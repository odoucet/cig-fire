import sys
import math
import time
import copy

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

# On met notre distanceMap en global pour simplifier le code ... et désolé c'est dégueu :(
distanceMap = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

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
        #                 gauche                   droite                 haut                    bas
        combinaisons = [ [self.x-1, self.y], [self.x+1, self.y], [self.x, self.y-1], [self.x, self.y+1]]
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

        # les positions de defenses, avec des unites dedans à ne pas toucher
        self.defensePositions = []

        # init carte du jeu
        self.map = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

        # coordonnées de notre QG (cache)
        self.hq = None
        # coordonnées du QG ennemi (cache)
        self.opponentHq = None

    def get_my_HQ(self)->Point:
        return self.hq


    def get_opponent_HQ(self)->Point:
        return self.opponentHq


    # Recupere toutes les cases qui respectent le type demandé
    # (pour éviter de recoder sans arret la même chose)
    def get_points_matching(self, types):
        casesVides = []
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.map[x][y] in types:
                    casesVides.append(Point(x, y))
        return casesVides


    # Strategie de deplacement des unites (Olivier)
    # un truc que la règle ne dit pas de facon claire : si un soldat est sur une case inactive, il meurt !
    def move_units(self):
        # on commence simple : on va a la case vide/adversaire la plus proche

        # on recupere la liste des cases
        casesVides = self.get_points_matching([NEUTRE, INACTIVEOPPONENT, ACTIVEOPPONENT])
        
        # on bouge les unites au plus proche du QG ennemi d'abord
        for unit in self.get_opponent_HQ().sortNearest(self.units):
            # Defense ? 
            if unit.doNotMove == True:
                continue

            # Strategie Olivier: si niveau 3, on fonce sur l'adversaire / la tour / le batiment MINE le plus proche
            if unit.level == 3:
                if not self.OpponentUnits: 
                    # on va sur la base ennemi
                    destination = self.get_opponent_HQ()
                else:
                    # on va taper de l'unité / du batiment ennemi
                    # TODO: on peut optimiser ici car le QG est forcément un building ennemi
                    tmpEnnemi = self.OpponentUnits.copy()
                    tmpEnnemi.extend(self.OpponentBuildings)
                    destination = unit.nearest(tmpEnnemi)

                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                unit.x = destination.x
                unit.y = destination.y
                continue

            # ici on devrait boucler jusqu'à trouver une bonne destination : 
            # - pas déjà ciblée par une autre unité
            # - 
            destination = unit.nearest(casesVides)
            if (destination is not None): 
                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                # que quelqu'un d'autre n'y aille pas
                casesVides.remove(destination)
            else:
                # destination == HQ ennemi ! 
                destination = self.get_opponent_HQ()
                self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')

    # Stratégie d'entrainement des unites
    # Les niveaux > 1 doivent se faire SUR un ennemi histoire de gagner du temps :)
    def train_units(self):

        # Strategie: on créé pleins de soldats, et on fait du niveau 2 quand il ne reste que X cases vides
        if len(self.get_points_matching([NEUTRE])) < 30 or len(self.units) >= 10:

            # Boucle 1: est-ce qu'on peut dégommer des niveaux 2 ou 3 en spawnant dessus ?
            for ennemi in self.OpponentUnits:
                if ennemi.level < 2:
                    continue
                if ennemi.level == 3:
                    # on considere qu'il est 2 car on va l'écraser avec un 3
                    ennemi.level = 2
                
                if (len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0 and 
                self.gold >= (Unit.TRAINING[ennemi.level+1]) and self.income >= Unit.ENTRETIEN[ennemi.level+1]):
                    self.actions.append(f'TRAIN {ennemi.level+1} {ennemi.x} {ennemi.y}')
                    self.gold   -= Unit.TRAINING[ennemi.level+1]
                    self.income -= Unit.ENTRETIEN[ennemi.level+1]
                    self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                    self.OpponentUnits.remove(ennemi) # on vire l'ennemi
            
            # Boucle 2 : est-ce qu'on peut dégommer une TOUR ennemies en spawnant un niveau 3 dessus ? ^^
            for ennemi in self.OpponentBuildings:
                if ennemi.type != TOWER:
                    continue
                
                if (len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0 and 
                self.gold >= (Unit.TRAINING[3]) and self.income >= Unit.ENTRETIEN[3]):
                    self.actions.append(f'TRAIN 3 {ennemi.x} {ennemi.y}')
                    self.gold   -= Unit.TRAINING[3]
                    self.income -= Unit.ENTRETIEN[3]
                    self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                    self.OpponentBuildings.remove(ennemi) # on vire l'ennemi

            # Boucle 4: est-ce qu'on peut dégommer un niveau 1 en spawnant un 2 dessus ? 
            for ennemi in self.OpponentUnits:
                if ennemi.level > 1:
                    continue
                
                if (len(ennemi.getAdjacentes(self.map, [ACTIVE])) > 0 and 
                self.gold >= (Unit.TRAINING[ennemi.level+1]) and self.income >= Unit.ENTRETIEN[ennemi.level+1]):
                    self.actions.append(f'TRAIN {ennemi.level+1} {ennemi.x} {ennemi.y}')
                    self.gold   -= Unit.TRAINING[ennemi.level+1]
                    self.income -= Unit.ENTRETIEN[ennemi.level+1]
                    self.map[ennemi.x][ennemi.y] = ACTIVE # case prise maintenant :D
                    self.OpponentUnits.remove(ennemi) # on vire l'ennemi
            
        else:
            # on garde l'algo (pas terrible) qu'on a déjà, pour le moment
            # TODO: optimiser ça :)
            casesANous = self.get_points_matching([ACTIVE])
            casesSpawn = []

            # Premier tour
            if len(casesANous) == 1:
                if (self.map[0][0] == ACTIVE):
                    casesSpawn.extend([Point(1,0), Point(0,1)])
                else:
                    casesSpawn.extend([Point(10,11), Point(11,10)])

            # On ajoute à ces cases là les inactives / neutres / ennemi
            for case in casesANous:
                # on peut optimiser en spawnant sur des cases actives de l'ennemi ? A tester
                casesSpawn.extend(case.getAdjacentes(self.map, [INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT, NEUTRE]))

            # et on deduplique
            casesSpawn = self.get_opponent_HQ().sortNearest(list(dict.fromkeys(casesSpawn)))

            # ici on entraine que du niveau 1
            while len(casesSpawn) > 0 and self.gold >= Unit.TRAINING[1] and self.income >= Unit.ENTRETIEN[1]:
                # on entraine sur une case à nous, la plus proche du QG adverse
                case = casesSpawn.pop(0)

                if self.spawnMap[case.x][case.y]:
                    self.actions.append(f'TRAIN 1 {case.x} {case.y}')
                    self.income -= Unit.ENTRETIEN[1]
                    self.gold   -= Unit.TRAINING[1]
                    self.map[case.x][case.y] = ACTIVE # case prise maintenant donc on peut spawn les adjacentes :)
                    
                    casesSpawn.extend(case.getAdjacentes(self.map, [INACTIVE, INACTIVEOPPONENT, ACTIVEOPPONENT, NEUTRE]))
                    casesSpawn = self.get_opponent_HQ().sortNearest(list(dict.fromkeys(casesSpawn)))

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
        
        # J'aime l'idée de mettre une tourelle en 2,2 ou 9,9 si l'ennemi se rapproche, pour éviter les "rush" comme
        # certains joueurs le font.
        # On essaie ça : si 3 adversaires sont à une distance <= 6, on pause la tourelle
        nbAdversairesProche = 0
        for unit in self.OpponentUnits:
            if distance(unit, self.get_my_HQ()) <= 6:
                nbAdversairesProche += 1
        
        #a reecrire mieux:
        if nbAdversairesProche >= 3:
            poserTourelle = True
            if self.get_my_HQ().x == 0:
                positionTourelle = Point(2, 2)
            else:
                positionTourelle = Point(9, 9)
            
            for building in self.buildings:
                if building.type == TOWER and building.x == positionTourelle.x and building.y == positionTourelle.y:
                    poserTourelle = False
                    break
            if poserTourelle:
                self.actions.append(f'BUILD TOWER {positionTourelle.x} {positionTourelle.y}')
                self.gold -= 15
                self.buildings.append(Building(ME, TOWER, positionTourelle.x, positionTourelle.y))


        # On essaie d'avoir des tourelles sur les super points (defenseMap >= 20)
        for x in range(WIDTH):
            for y in range(HEIGHT): 
                if self.defenseMap[x][y] is not None and self.defenseMap[x][y] >= 20:
                    # on check qu'on a pas deja une tour dessus ou à coté
                    built = False
                    for building in self.buildings:
                        if building.type == TOWER and distance(building, Point(x, y)) <= 1:
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
                        self.buildings.append(Building(ME, TOWER, x, y))
                        #todo: marquer case occupée


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


    # Construction d'une carte avec les points de defense importants chez nous
    # Pour se faire, pour chaque case à nous on calcule notre surface si on la perd
    # On va s'en servir pour mettre des tourelles par exemple
    def calcul_carte_defense(self):
        self.defenseMap = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

        # si on a pas bcoup de cases en fait on s'en fout, soit c'est trop tôt, soit on est mort
        # pareil si on possede toute la carte
        nbCasesANous = len(self.get_points_matching([ACTIVE]))
        if nbCasesANous < 15 or len(self.get_points_matching([ACTIVEOPPONENT])) < 15:
            return

        # on passe maintenant au taff
        # TODO: faire ce taff pour toutes les cases ACTIVE, par ordre de distance avec notre QG
        for x in range(WIDTH):
            for y in range(HEIGHT): 
                # on a assez de temps ?
                if self.check_timeout():
                    sys.stderr.write("TIMEOUT REACHED in calcul_carte_defense("+str(x)+","+str(y)+") WE EXITED BEFORE DEFENSEMAP COMPLETE\n")
                    return
                
                # on peut sauter la case si on a déjà une tour dessus ou à une distance de 1
                # TODO: reecrire ça mieux ...
                if Point(x, y) in self.buildings:
                    continue
                skip = False
                for point in Point(x,y).getAdjacentes(self.map):
                    if point.x == x and point.y == y:
                        skip = True
                        break
                if skip:
                    continue

                # pas de raison de pas calculer pour cette case ...
                if self.map[x][y] == ACTIVE:
                    # si on est trop pres de notre QG ça sert à rien
                    if distance(Point(x,y), self.get_my_HQ()) < 3:
                        self.defenseMap[x][y] = 0
                        continue

                    # la grosse formule commence ici
                    # Etape 1 - on copie la map 
                    # IL FAUT ABSOLUMENT UTILISER DEEPCOPY CAR ON A UN TABLEAU DE TABLEAU!
                    newMap =  copy.deepcopy(self.map)

                    # Ensuite on la modifie pour virer la case courante
                    newMap[x][y] = INACTIVE
                    newMapParcours = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

                    # Ici on recalcule une nouvelle carte
                    aTraiter = [ self.get_my_HQ()  ]
                    debugi = 0
                    while len(aTraiter) > 0 and debugi < 500:
                        debugi += 1
                        element = aTraiter.pop(0)

                        # si deja fait
                        if newMapParcours[element.x][element.y] == 1:
                            continue
                        
                        newMapParcours[element.x][element.y] = 1
                        
                        cases = element.getAdjacentes(newMap, [ACTIVE])
                        for case in cases:
                            if newMapParcours[case.x][case.y] is None and case not in aTraiter:
                                aTraiter.append(case)
                 
                    # Maintenant on calcule le nbre de cases à nous: 
                    nbCases = 0
                    for tmpx in range(WIDTH):
                        for tmpy in range(HEIGHT):
                            if newMapParcours[tmpx][tmpy] == 1:
                                nbCases += 1
                    self.defenseMap[x][y] = abs(nbCasesANous - nbCases)

                    
        #debugPythonMap(self.map)
        #debugMap(self.defenseMap)
        

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
        self.nbMines = 0
        self.nbOpponentMines = 0

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

        # Cartes des distances.
        # techniquement, pour le pathfinding il faudrait calculer la carte des distances pour chaque point possible.
        # et bah en fait c'est exactement ce qu'on va faire car ça calcule super vite et qu'on a une seconde sur ce run !
        # et on réintegre la fonction distance() qui se basera dessus (juste aller chercher des coordonnées au bon endroit)
        # NOTE: distanceMap est une variable *GLOBALE* (oui c'est mal)
        if distanceMap[0][0] is None:
            p = Pathfinding()
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    if self.map[x][y] != NEANT:
                        distanceMap[x][y] = p.buildDistanceMap(self.map, Point(x, y))

        # TODO: deplacer ça dans une fonction pour ecrire le test qui va bien :)
        # carte des spawns, avec les positions sur lesquelles on peut spawn (cases vides): 
        self.spawnMap = [ [ True for y in range( HEIGHT ) ] for x in range( WIDTH ) ]
        # on enleve les cases impossibles:
        for case in self.get_points_matching([NEANT]):
            self.spawnMap[case.x][case.y] = False
        # on enleve toutes les unites et les buildings
        for case in self.OpponentUnits:
            self.spawnMap[case.x][case.y] = False
        for case in self.units:
            self.spawnMap[case.x][case.y] = False
        for case in self.buildings:
            self.spawnMap[case.x][case.y] = False
        for case in self.OpponentBuildings:
            self.spawnMap[case.x][case.y] = False


    def build_output(self):
        self.calcul_carte_defense()

        self.move_units()

        self.protect_base()
        self.build_mines()
        self.train_units()
        

        # il reste de la tune ? on ajoute des tours :)
        self.build_towers()


    def output(self):
        if self.actions:
            print(';'.join(self.actions))
        else:
            print('WAIT')
        sys.stderr.write("Time spent in this round: "+str(self.getTotalTime())+"ms")

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
def distance(f, t) -> float:
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
