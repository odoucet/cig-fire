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


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


    def nearest(self, point: Point, srcArray: array) -> Point:
        nearest = null
        nearestDist = null
        for entity in srcArray:
            # on stocke l'appel a distance() car c'est une fction couteuse en CPU
            tmpDist = distance(entity, point)
            if (nearest = null or tmpDist < nearestDist)
                nearest = entity
                nearestDist = tmpDist
        return nearest


class Unit:
    def __init__(self, owner, id, level, x, y):
        self.owner = owner
        self.id = id
        self.level = level
        self.pos = Point(x, y)


class Building:
    def __init__(self, owner, type, x, y):
        self.owner = owner
        self.type = type
        self.pos = Point(x, y)


class Game:
    def __init__(self):
        self.buildings = []
        self.units = []
        self.actions = []
        self.gold = 0
        self.income = 0
        self.opponent_gold = 0
        self.opponent_income = 0


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
        # Etape 2: on stocke ces cases pour que deux guerriers aillent pas au mm endroit
        center = Point(5, 5)

        for unit in self.units:
            if unit.owner == ME:
                self.actions.append(f'MOVE {unit.id} {center.x} {center.y}')


    def get_train_Point(self):
        hq = self.get_my_HQ()

        if hq.pos.x == 0:
            return Point(0, 1)
        return Point(11, 10)


    def train_units(self):
        # TODO: delete def get_train_Point() and train in best spot
        train_pos = self.get_train_Point()

        # on entraine que si on a suffisemment d'income
        # TODO: il faudra affiner en fction des autres actions sur le round
        if self.gold > 30 and self.income > 1:
            self.actions.append(f'TRAIN 1 {train_pos.x} {train_pos.y}')
            self.income -= 1


    def init(self):
        # Unused in Wood 3
        numberMineSpots = int(input())
        for i in range(numberMineSpots):
            x, y = [int(j) for j in input().split()]


    def update(self):
        self.units.clear()
        self.buildings.clear()
        self.actions.clear()

        self.gold = int(input())
        self.income = int(input())
        self.opponent_gold = int(input())
        self.opponent_income = int(input())

        for i in range(12):
            line = input()
            print(line, file=sys.stderr)

        building_count = int(input())
        for i in range(building_count):
            owner, building_type, x, y = [int(j) for j in input().split()]
            self.buildings.append(Building(owner, building_type, x, y))

        unit_count = int(input())
        for i in range(unit_count):
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
def distance(f, t):
    return sqrt(pow(f.x - t.x, 2)+pow(f.y - t.y, 2))

g = Game()

g.init()
while True:
    g.update()
    g.build_output()
    g.output()
