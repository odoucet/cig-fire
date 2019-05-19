import sys 
import os

# Pour faire de beaux dessins
from PIL import Image, ImageDraw, ImageFont

from cig import *

## Draw
DRAWZOOM=50

def drawMap(macarte, name, type="map"): 
    r = Image.new('RGBA', [len(macarte[0])*DRAWZOOM,len(macarte)*DRAWZOOM])

    # get a drawing context
    d = ImageDraw.Draw(r)

    # Quadrillage
    for x in range(len(macarte)):
        d.line([(x*DRAWZOOM, 0), (x*DRAWZOOM, DRAWZOOM*len(macarte))], fill=(0,0,0))
        d.line([(0, x*DRAWZOOM), (DRAWZOOM*len(macarte), x*DRAWZOOM)], fill=(0,0,0))
    d.line([(len(macarte)*DRAWZOOM-1, 0), (len(macarte)*DRAWZOOM-1, DRAWZOOM*len(macarte)-1)], fill=(0,0,0))
    d.line([(0, len(macarte)*DRAWZOOM-1), (DRAWZOOM*len(macarte)-1, len(macarte)*DRAWZOOM-1)], fill=(0,0,0))

    # on écrit les x,y
    legend = ImageFont.truetype("arial.ttf", 8)
    for x in range(len(macarte)+1):
        d.text((x*DRAWZOOM-DRAWZOOM/2, 3), str(x-1), font=legend, fill=(0,0,0))
        d.text((3, x*DRAWZOOM-DRAWZOOM/2,), str(x-1), font=legend, fill=(0,0,0))

    # On écrit la carte qu'on nous donne
    fnt = ImageFont.truetype("arial.ttf", 12)
    for x in range(len(macarte)):
        for y in range(len(macarte)):
            if type == "map":
                if macarte[x][y] == "o":
                    char = "i"
                else:
                    char = macarte[x][y]
            else:
                char = macarte[x][y]
            d.text((DRAWZOOM+x*DRAWZOOM-DRAWZOOM/2, DRAWZOOM+y*DRAWZOOM-DRAWZOOM/2), str(char), font=fnt, fill=(0,0,100))

    r.save('tests/'+name+'.png', 'PNG')
## end raw

def test_maps(): 
    g = Game()
    # attention, carte "inversée" visuellement ici 
    g.map = [
        ['O', 'O', 'O', '#', '#', '#', 'O', 'O', 'O', 'O', 'O', '#'], 
        ['O', 'O', 'O', '#', '#', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O'], 
        ['#', '#', 'O', 'O', 'O', 'X', 'X', 'O', 'X', 'X', 'X', 'O'], 
        ['#', 'O', 'O', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'O'], 
        ['O', 'O', 'X', 'X', 'O', 'X', '.', 'X', 'X', 'X', '.', '.'], 
        ['O', 'O', 'O', 'X', 'X', 'X', '.', 'X', 'X', 'X', '.', '.'], 
        ['.', 'O', 'O', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '.', '#'], 
        ['.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', '#', '#'], 
        ['.', '.', '.', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X', 'X'], 
        ['.', '.', 'X', 'X', 'X', 'X', 'X', '#', '#', 'X', 'X', 'X'], 
        ['#', '.', 'X', 'X', 'X', '.', '#', '#', '#', 'X', 'X', 'X']]
    # buildings:
    g.buildings = [Building(ME, HQ, 0, 0)]
    g.OpponentBuildings = [Building(opponent, HQ, 11, 11)]
    drawMap(g.map, "map")
    g.startTime = time.time()

    g.calcul_carte_defense()
    drawMap(g.defenseMap, "defensemap","map")
    assert g.debugMapANous[4][11] is not None and g.debugMapANous[4][11] == 15
    assert g.debugMapANous[5][4] is not None and g.debugMapANous[5][4] == -1
    assert g.debugMapANous[7][2] is not None and g.debugMapANous[7][2] == 11

    # Petite marge
    assert (time.time()-g.startTime) > 0.06
    assert g.defenseMap[2][2] is not None and g.defenseMap[2][2] > 30
    assert g.defenseMap[2][5] is not None and g.defenseMap[2][5] > 20
