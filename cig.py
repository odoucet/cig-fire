import sys
import math

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

num_sites = int(raw_input())
for i in xrange(num_sites):
    site_id, x, y, radius = [int(j) for j in raw_input().split()]

# game loop
while True:
    # touched_site: -1 if none
    gold, touched_site = [int(i) for i in raw_input().split()]
    for i in xrange(num_sites):
        # gold_remaining: -1 if unknown
        # max_mine_size: -1 if unknown
        # structure_type: -1 = No structure, 0 = Goldmine, 1 = Tower, 2 = Barracks
        # owner: -1 = No structure, 0 = Friendly, 1 = Enemy
        site_id, gold_remaining, max_mine_size, structure_type, owner, param_1, param_2 = [int(j) for j in raw_input().split()]
    num_units = int(raw_input())
    for i in xrange(num_units):
        # unit_type: -1 = QUEEN, 0 = KNIGHT, 1 = ARCHER, 2 = GIANT
        x, y, owner, unit_type, health = [int(j) for j in raw_input().split()]

    # Write an action using print
    # To debug: print >> sys.stderr, "Debug messages..."


    # First line: A valid queen action
    # Second line: A set of training instructions
    print "WAIT"
    print "TRAIN"