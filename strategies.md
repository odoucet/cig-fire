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