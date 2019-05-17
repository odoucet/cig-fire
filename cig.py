import sys
import math

# First draft from "starterkit"
# https://raw.githubusercontent.com/Azkellas/a-code-of-ice-and-fire/develop/src/test/starterkit/starter.py

# MAP SIZE
WIDTH = 12
HEIGHT = 12

# OWNER
ME = 0
OPONENT = 1

# BUILDING TYPE
HQ = 0

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


class Unit (Point):
    def __init__(self, owner, id, level, x: int, y: int):
        self.owner = owner
        self.id = id
        self.level = level
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
        self.units = []
        self.actions = []
        self.mines = []
        self.gold = 0
        self.income = 0
        self.opponent_gold = 0
        self.opponent_income = 0
        # init selfmap
        self.map = [ [ None for y in range( HEIGHT ) ] for x in range( WIDTH ) ]

    def get_my_HQ(self):
        for b in self.buildings:
            if b.type == HQ and b.owner == ME:
                return b


    def get_oponent_HQ(self):
        for b in self.buildings:
            if b.type == HQ and b.owner == OPONENT:
                return b

    # Strategie de deplacement des unites (Olivier)
    def move_units(self):
        # on commence simple : on va a la case vide/adversaire la plus proche

        # on recupere la liste des cases vides
        casesVides = []
        for x in range(WIDTH):
            for y in range(HEIGHT):
                # TODO: refaire cette liste mieux, on peut aller ailleurs
                if self.map[x][y] == NEUTRE or self.map[x][y] == INACTIVEOPPONENT or self.map[x][y] == ACTIVEOPPONENT:
                    casesVides.append(Point(x, y))
        

        # TODO Etape 2: on stocke ces cases pour que deux guerriers aillent pas au mm endroit
        
        for unit in self.units:
            if unit.owner == ME:
                destination = Point.nearest(self, unit, casesVides)
                if (destination is not None): 
                    self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                else:
                    # destination == HQ ennemi ! 
                    destination = self.get_oponent_HQ()
                    self.actions.append(f'MOVE {unit.id} {destination.x} {destination.y}')
                    


    def get_train_Point(self):
        hq = self.get_my_HQ()

        if hq.x == 0:
            return Point(0, 1)
        return Point(11, 10)


    def train_units(self):
        # TODO: delete def get_train_Point() and train in best spot
        train_pos = self.get_train_Point()

        # on entraine que si on a suffisemment d'income
        # TODO: il faudra affiner en fction des autres actions sur le round
        if self.gold >= 10 and self.income >= 1:
            self.actions.append(f'TRAIN 1 {train_pos.x} {train_pos.y}')
            self.income -= 1


    def init(self):
        # Unused in Wood 3
        numberMineSpots = int(input())
        for _ in range(numberMineSpots):
            x, y = [int(j) for j in input().split()]
            self.mines.append(Mine(x, y))



    def update(self):
        self.units.clear()
        self.buildings.clear()
        self.actions.clear()

        self.gold = int(input())
        self.income = int(input())
        self.opponent_gold = int(input())
        self.opponent_income = int(input())

        for y in range(HEIGHT):
            line = input()
            x=0
            for char in list(line):
                self.map[x][y] = char
                x += 1

        building_count = int(input())
        for _ in range(building_count):
            owner, building_type, x, y = [int(j) for j in input().split()]
            self.buildings.append(Building(owner, building_type, x, y))

        unit_count = int(input())
        for _ in range(unit_count):
            owner, unit_id, level, x, y = [int(j) for j in input().split()]
            self.units.append(Unit(owner, unit_id, level, x, y))


    def build_output(self):
        # TODO "core" of the AI
        self.train_units()
        self.move_units()


    def output(self):
        if self.actions:
            print(';'.join(self.actions))
        else:
            print('WAIT')


# calcule la distance entre deux cases. Hyper utilise donc mis en global
def distance(f, t) -> float:
    return math.sqrt(math.pow(f.x - t.x, 2)+math.pow(f.y - t.y, 2))

g = Game()

g.init()
while True:
    g.update()
    g.build_output()
    g.output()
