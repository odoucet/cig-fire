import sys 
import os
import time

# Pour faire de beaux dessins
from PIL import Image, ImageDraw, ImageFont

from cig import Game, Pathfinding, Building, Point, Unit, OPPONENT, ME, distanceMap, MINE, TOWER

## Draw
DRAWZOOM=50

def drawMap(macarte, name, type="map", texte=None): 

    # no draw on Travis-CI
    if 'TRAVIS' in os.environ:
        return
    
    r = Image.new('RGBA', [len(macarte[0])*DRAWZOOM,len(macarte)*DRAWZOOM])

    # get a drawing context
    d = ImageDraw.Draw(r)

    # On écrit la carte qu'on nous donne
    fnt = ImageFont.truetype("arial.ttf", 12)
    for x in range(len(macarte)):
        for y in range(len(macarte)):
            if type == "map":
                if macarte[x][y] == "#":
                    fillColor=(50,50,50)
                elif macarte[x][y] == "o":
                    fillColor=(100,0,0)
                elif macarte[x][y] == "O":
                    fillColor=(255,0,0)
                elif macarte[x][y] == "X":
                    fillColor=(0,0,255)
                elif macarte[x][y] == "x":
                    fillColor=(0,0,100)
                elif macarte[x][y] == ".":
                    fillColor=(200,200,200)
                else:
                    fillColor=(0,0,0)

                d.rectangle([x*DRAWZOOM, y*DRAWZOOM, x*DRAWZOOM+DRAWZOOM, y*DRAWZOOM+DRAWZOOM], fill=fillColor)
            else:
                d.text((DRAWZOOM+x*DRAWZOOM-DRAWZOOM/2, DRAWZOOM+y*DRAWZOOM-DRAWZOOM/2), str(macarte[x][y]), font=fnt, fill=(0,0,100))

    # on écrit les x,y
    legend = ImageFont.truetype("arial.ttf", 8)
    for x in range(len(macarte)+1):
        d.text((x*DRAWZOOM-DRAWZOOM/2, 3), str(x-1), font=legend, fill=(0,0,0))
        d.text((3, x*DRAWZOOM-DRAWZOOM/2,), str(x-1), font=legend, fill=(0,0,0))

    # Quadrillage
    for x in range(len(macarte)):
        d.line([(x*DRAWZOOM, 0), (x*DRAWZOOM, DRAWZOOM*len(macarte))], fill=(0,0,0))
        d.line([(0, x*DRAWZOOM), (DRAWZOOM*len(macarte), x*DRAWZOOM)], fill=(0,0,0))
    d.line([(len(macarte)*DRAWZOOM-1, 0), (len(macarte)*DRAWZOOM-1, DRAWZOOM*len(macarte)-1)], fill=(0,0,0))
    d.line([(0, len(macarte)*DRAWZOOM-1), (DRAWZOOM*len(macarte)-1, len(macarte)*DRAWZOOM-1)], fill=(0,0,0))

    if texte is not None:
        d.text([10, len(macarte)*DRAWZOOM-10], texte, font=legend, fill=(0,0,0))

    r.save('tests/'+name+'.png', 'PNG')
## end raw

# def test_map_cas1(): 
#     g = Game()
#     # attention, carte "inversée" visuellement ici 
#     g.map = [
#         ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
#         ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['#', '#', 'O', 'O', 'O', 'X', 'X', 'O', 'X', 'X', 'X', 'O'], 
#         ['#', 'O', 'O', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'O'], 
#         ['O', 'O', 'X', 'X', 'O', 'X', '.', 'X', 'X', 'X', '.', '.'], 
#         ['O', 'O', 'O', 'X', 'X', 'X', '.', 'X', 'X', 'X', '.', '.'], 
#         ['.', 'O', 'O', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.', '#'], 
#         ['.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#', '#'], 
#         ['.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'], 
#         ['.', '.', 'X', 'X', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
#         ['#', '.', 'X', 'X', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]
#     # buildings:
#     g.hq = Point(0, 0)
#     g.opponentHq = Point(11,11)
#     g.calcul_distance_map()
#     #drawMap(g.map, "map")
    
#     g.startTime = time.time()

#     g.calcul_carte_defense()
#     #drawMap(g.defenseMap, "defensemap","map")

#     # Petite marge
#     #assert (time.time()-g.startTime) > 0.06
#     assert g.defenseMap[2][2] is not None and g.defenseMap[2][2] > 30
#     assert g.defenseMap[2][5] is not None and g.defenseMap[2][5] > 20

# ### CAS NUMERO 2 ###
# def test_map_cas2(): 
#     g = Game()
    
#     # attention, carte "inversée" visuellement ici 
#     g.map = [
#         ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
#         ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['#', '#', 'O', 'O', 'O', 'x', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['#', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
#         ['O', 'O', 'O', 'O', 'x', 'O', 'O', 'O', 'O', 'O', 'O', '#'], 
#         ['O', 'O', 'O', 'O', 'x', 'O', 'O', 'O', 'O', 'O', '#', '#'], 
#         ['.', '.', 'x', 'x', 'x', 'O', 'O', 'O', 'O', 'O', 'O', '.'], 
#         ['.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'], 
#         ['#', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X']
#     ]

#     # buildings:
#     g.hq = Point(0, 0)
#     g.opponentHq = Point(11,11)
#     g.calcul_distance_map()
#     drawMap(g.map, "map")

#     g.startTime = time.time()
#     g.calcul_carte_defense()
#     # on veut pas que la defenseMap prenne plus de 50ms
#     assert time.time()-g.startTime < 0.5
#     drawMap(g.defenseMap, "defensemap","defmap")
#     assert g.defenseMap[4][10] is not None and g.defenseMap[4][10] == 1
    


# ### CAS NUMERO 3 ###
# def test_map_cas3(): 
    g = Game()
    
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', 'X', 'X', 'X', 'O', 'O', 'O', 'O', 'O'], 
        ['#', 'O', 'O', 'O', 'O', 'X', 'X', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'O', 'O', 'X', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', 'X', 'X', 'X', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'X', 'X', '.', 'X', 'X', 'O', '.', '#'], 
        ['O', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#', '#'], 
        ['.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.'], 
        ['.', '.', 'X', 'X', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
        ['#', '.', '.', '.', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]

    # buildings:
    g.hq = Point(0, 0)
    g.opponentHq = Point(11,11)
    g.calcul_distance_map()
    drawMap(g.map, "map")

    g.startTime = time.time()
    g.calcul_carte_defense()
    #drawMap(g.debugMapANous, "mapanous","defmap")
    sys.stderr.write("Temps de construction: "+str(time.time()-g.startTime))

    #drawMap(g.defenseMap, "defensemap","defmap")
    assert g.defenseMap[2][2] is not None and g.defenseMap[2][2] > 10
    assert g.defenseMap[2][6] is not None and g.defenseMap[2][6] == 1


### Distances ###
def test_algo_distance1(): 
    g = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    macarte = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', 'X', 'X', 'X', 'O', 'O', 'O', 'O', 'O'], 
        ['#', 'O', 'O', 'O', 'O', 'X', 'X', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'O', 'O', 'X', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', 'X', 'X', 'X', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'X', 'X', '.', 'X', 'X', 'O', '.', '#'], 
        ['O', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#', '#'], 
        ['.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.'], 
        ['.', '.', 'X', 'X', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
        ['#', '.', '.', '.', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]

    #drawMap(macarte, "mapdistance")

    g.startTime = time.time()
    distanceMap= g.buildDistanceMap(macarte, Point(0, 0))
    #drawMap(distanceMap, "distancemap1","defmap", "Temps de construction: "+str(time.time()-g.startTime))
    assert distanceMap[3][0] is None
    assert distanceMap[2][2] is not None and distanceMap[2][2] == 4
    assert distanceMap[2][6] is not None and distanceMap[11][9] == 20

    # Autre cas avec la même carte : départ au milieu ! 
    g.startTime = time.time()
    distanceMap= g.buildDistanceMap(macarte, Point(5, 5))
    #drawMap(distanceMap, "distancemap2","defmap", "Temps de construction: "+str(time.time()-g.startTime))
    assert distanceMap[11][7] is None
    assert distanceMap[2][2] is not None and distanceMap[2][2] == 6
    assert distanceMap[2][6] is not None and distanceMap[11][9] == 10

def test_algo_distance2(): 
    g = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    macarte = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', '#', 'X', 'X', 'O', 'O', 'O', 'O', 'O'], 
        ['#', 'O', 'O', 'O', '#', 'X', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'O', 'O', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', '#', 'X', 'X', 'O', 'O', 'O'], 
        ['O', 'O', 'O', '#', 'X', 'X', '#', 'X', 'X', 'O', '.', '#'], 
        ['O', '.', 'X', '#', 'X', 'X', '#', 'X', 'X', 'X', '#', '#'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
        ['#', '.', '.', '#', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]

    #drawMap(macarte, "mapdistance")

    startTime = time.time()
    distanceMap= g.buildDistanceMap(macarte, Point(0, 0))
    #drawMap(distanceMap, "distancemap3","defmap", "Temps de construction: "+str(time.time()-startTime))
    assert distanceMap[4][4] is None
    assert distanceMap[2][2] is not None and distanceMap[8][7] == 17
    assert distanceMap[9][9] is not None and distanceMap[9][9] == 18

    # Autre cas avec la même carte : départ au milieu ! 
    startTime = time.time()
    distanceMap= g.buildDistanceMap(macarte, Point(5, 5))
    #drawMap(distanceMap, "distancemap4","defmap", "Temps de construction: "+str(time.time()-startTime))
    assert distanceMap[10][8] is None
    assert distanceMap[0][2] is not None and distanceMap[0][2] == 8
    assert distanceMap[5][7] is not None and distanceMap[5][7] == 6

# la capture directe, c'est le fait de spawner pleins d'unités lvl1 jusqu'à la base ennemie
def test_algo_capture_directe1():
    g = Game()
    p = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', '#', 'X', 'X', 'O', 'O', 'O', 'O', 'O'], 
        ['#', 'O', 'O', 'O', '#', 'X', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'O', 'O', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', '#', 'X', 'X', 'O', 'O', 'O'], 
        ['O', 'O', 'O', '#', 'X', 'X', '#', 'X', 'X', 'O', '.', '#'], 
        ['O', '.', 'X', '#', 'X', 'X', '#', 'X', 'X', 'O', '#', '#'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
        ['#', '.', '.', '#', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]
    # on va avoir besoin des bâtiments et unités ennemies: 
    g.units.append(Unit(ME, 1, 1, 8, 9))
    g.hq = Point(0, 0)
    g.opponentHq = Point(11,11)
    g.calcul_distance_map()

    # test1: aucun bâtiment ni unité énnemi
    g.gold = 50
    g.income = 1 # doit pas jouer
    drawMap(g.map, "cd1-map")
    drawMap(distanceMap[11][11], "cd1-distancemap", "defmap")


    assert g.calcul_capture_directe() is True
    # ensuite on verifie les actions
    print(g.actions)
    assert "TRAIN 1 9 9" in g.actions
    assert "TRAIN 1 11 11" in g.actions

def test_algo_capture_directe2():
    g = Game()
    p = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', '#', 'X', 'X', 'O', 'O', 'O', 'O', 'O'], 
        ['#', 'O', 'O', 'O', '#', 'X', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'X', 'O', 'O', '#', 'X', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', '#', 'X', 'X', 'O', 'O', 'O'], 
        ['O', 'O', 'O', '#', 'X', 'X', '#', 'X', 'X', 'O', '.', '#'], 
        ['O', '.', 'X', '#', 'X', 'X', '#', 'X', 'X', 'O', '#', '#'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#'], 
        ['.', '.', 'X', '#', 'X', 'X', 'X', '#', '#', '#', 'X', 'X'], 
        ['#', '.', '.', '#', 'X', '.', '#', '#', '#', '#', 'X', 'X']]
    # on va avoir besoin des bâtiments et unités ennemies: 
    # test2: on rajoute un niveau 1 sur le chemin
    g.units.append(Unit(ME, 1, 1, 8, 9))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 10, 10))
    g.hq = Point(0, 0)
    g.opponentHq = Point(11,11)
    g.gold = 70
    g.income = 1 # doit pas jouer
    drawMap(g.map, "cd2-map")

    g.startTime = time.time()
    g.calcul_distance_map()
    distanceMap = p.buildDistanceMap(g.map, Point(11, 11))
    drawMap(distanceMap, "cd2-distance","defmap", "Temps de construction: "+str(time.time()-g.startTime))

    # mini check quand mm
    assert distanceMap[8][9] == 5

    assert g.calcul_capture_directe() is True
    # ensuite on verifie les actions
    assert "TRAIN 1 9 9" in g.actions
    assert "TRAIN 2 10 10" in g.actions
    assert "TRAIN 1 11 11" in g.actions


# Un cas qu'on a eu en prod: on a masse tune, on est prêt de la base adverse, et pourtant on capture pas :(
def test_algo_capture_directe3():
    g = Game()
    p = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', 'O', '#', '#', '#', '#', '#', 'x', 'x', '#'],
        ['O', 'O', 'O', 'O', 'O', '#', '#', '#', 'O', 'x', 'x', '#'],
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'x', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', '#', '#', '#', 'O', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', '#'],
        ['#', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', 'X', 'O', 'O', 'O', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'X', 'X', 'X', 'O', 'X', 'X'],
        ['#', 'O', 'O', 'O', '#', '#', '#', 'X', 'X', 'X', 'X', 'X'],
        ['#', 'O', 'O', '#', '#', '#', '#', '#', 'X', 'X', 'X', 'X']
    ]

    # on va avoir besoin des bâtiments et unités ennemies: 
    g.units.append(Unit(ME, 1, 1, 9, 9))
    g.hq = Point(0, 0)
    g.opponentHq = Point(11,11)
    g.OpponentBuildings.append(Building(OPPONENT, TOWER, 10, 10))
    g.gold = 145
    g.income = 1 # doit pas jouer
    #drawMap(g.map, "cd3-map")
    g.calcul_distance_map()

    assert g.calcul_capture_directe() is True
    # ensuite on verifie les actions
    print(g.actions)
    assert "TRAIN 3 10 9" in g.actions
    assert "TRAIN 1 11 9" in g.actions
    assert "TRAIN 3 11 10" in g.actions
    assert "TRAIN 1 11 11" in g.actions

# Decoupage de l'armée adverse
def test_algo_decoupe_ennemi():
    g = Game()
    p = Pathfinding()
    
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', '#', '#', '#', '#', '.', '.', '.', '.', '#'],
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'X', 'X', 'X', '#'],
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', '.', 'X', 'X', 'X', '#'],
        ['#', 'O', 'O', 'O', 'O', 'O', 'O', '.', 'X', 'X', 'X', '#'],
        ['#', 'O', 'O', '.', 'O', 'O', '.', '.', 'X', 'X', 'X', '#'],
        ['#', '.', '.', 'X', 'X', 'O', 'O', 'O', 'X', 'X', 'X', '#'],
        ['#', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#'],
        ['#', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#'],
        ['#', '.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#'],
        ['#', '.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
        ['#', '.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'],
        ['#', '.', '.', '.', '.', '#', '#', '#', '#', 'X', 'X', 'X']
    ]

    g.units.append(Unit(ME, 1, 1, 5, 7))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 1, 8))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 1, 9))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 1, 10))

    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 6, 5))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 6, 6))
    g.OpponentUnits.append(Unit(OPPONENT, 1, 1, 6, 7))
    g.hq = Point(0, 0)
    g.opponentHq = Point(11,11)
    g.gold   = 33
    g.income = 27
    g.tour = 30 # tour 30 !

    drawMap(g.map, "decoupe1-map")

    g.startTime = time.time()
    assert g.calcul_decoupe_adversaire() is True

    print(g.actions)
    drawMap(g.map, "decoupe1-mapfinal")
    assert "TRAIN 1 5 8" in g.actions
    assert "TRAIN 1 5 9" in g.actions
    assert "TRAIN 1 5 10" in g.actions


