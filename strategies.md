Listing des stratégies
====================================
*(avant répartition du code à écrire)*

1) Agrandir son territoire (Olivier)
2) former des armées / upgrader les armées (Luc ?)
3) utiliser les armées pour aller attaquer l'ennemi (Luc ?)


Idées en vrac: 
- Mettre en destination par défaut non pas le QG ennemi mais la case en diagonale la plus proche : elle est moins "surveillée",
  et une fois dessus, ça nous donne deux possibilités pour aller attaquer le QG

- un moment il va falloir calculer une carte avec des points de cibles potentielles de mouvement : toutes les cases qui enlèvent un max de points à l'adversaire :)

- actuellement nos unités se gênent dans leur déplacement.
  Il faudrait optimiser le spawn et le déplacement des unités, en suivant des diagonales

- on pose pas de tourelles pour le moment ! Réfléchir aux endroits les plus intéressants ...
  => cases qui protègent de grandes zones à nous ?
  ![En exemple](https://tof.cx/images/2019/05/17/26f4ce374a08d3be9323a8841c842b4e.jpg)

- si un guerrier peut aller à droite ou en bas, il choisit "aléatoirement", alors que par exemple si y'a un guerrier ennemi sur l'autre case,
il faut préférer ça.
  Pour commencer, on peut, pour les mouvements : 
    * faire un round avec juste les cases adjacentes, et calculer si y'a un truc intéressant => override
    * sinon algo actuel

- faire une carte des cibles à point, pour simplifier où on va : 
   * les mines adverses
   * les adversaires qu'on peut battre (dépend de qui on est)
   * les cases importantes pour l'ennemi (comme notre defense_map, mais pour l'ennemi)
       => on construit que celles à portée de notre zone ? on ira pas capturer une tile à l'autre bout de la map :)

- comme on peut spawn pleins d'unites 1 et que ça vole une case, on calcule si on peut faire des horizontal/vertical avec ça et couper BEAUCOUP de territoire ennemi :)
  => simuler le coup facile, mais leterritoire perdu c'est un peu long :(
                                 => juste ignorer les cases plus à droite/gauche/haut/bas pour simplfiier ? super simple alors !
*************
Optim calcul_defense_map: au lieu de faire par x,y on le fait par distance à notre QG : comme ça si on s'arrête, au moins on a fait les trucs utiles.
+ si on a un building sur une case on calcule pas (on pourra rien poser dessus)
             idem pour un bâtiment ? => veut dire que defense_map ne servira que pour des tourelles ...

PRIORITE: 
distanceWalk(p1, p2) qui donne la distance à pied entre deux points, donc ignore les murs et les batiments (sauf si batiment == p1 ou p2)

puis Point.nearestWalk()
puis Point.sortNearestwalk()


TODO
====
J'ai merdé les appels de fonctions Point, qui devraient pas passer tous les arguments mais faire monunite.getAdjacentes(). A réécrire

Il faut coder un truc de pathfinding, car mes mecs essaient de se marcher dessus et on a pleins d'ordres invalides :(