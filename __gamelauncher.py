#############################################
############### Game launcher ###############

g = Game()

g.init()
while True:
    g.update()
    startTime = time.time()
    g.build_output()
    g.output()
