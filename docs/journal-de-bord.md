# Journal de bord

Notes de travail accumulées dans le `README.md` pendant le développement du
moteur terminal. Déplacées ici telles quelles lors de la Phase 0 (le README est
redevenu une présentation du projet).

Contenu historique : conservé mot pour mot, seule la mise en forme a été
reprise. Plusieurs points sont depuis résolus — voir
[`code-review-2026-06.md`](./code-review-2026-06.md) et
[`roadmap.md`](./roadmap.md).

---

## 01/12 — détection des blocages

> Réalisation : à chaque move il faut trouver un moyen de vérifier quelles cases
> ne sont plus prise via "blocage"
> ie : un pion devant un fou ?
>
> idée -> à chaque move, vérifier la square from et le square to en diagonale, en
> ligne et en L pour changer le taken_board
>
> surtout il faut que je regarde ce qui est le plus pratique entre regarder
> uniquement les check et checkmate à chaque tour et faire un calcul de "blocage"
> ou de "take" pour voir si c'est un checkmate ?
>
> TRES porbablement mieux que mon idée de "taken_board"
>
> --> la logique est de vérifier si il y a check à chaque tour non

## 10/12 — pat, en passant, promotion

> - The pat mechanism must be coded --> new function in BOARD class
> - The En passant move must be added to the pawn `_is_valid_move` function
> - the action of changing a pawn for an other piece if it reaches the opposite
>   backrank --> how does it work, execute move then choose ? or do both in the
>   command line (in this case it is in the pawn class that it happens)

## 12/12 — mise en œuvre de la promotion

> the action of changing a pawn for an other piece if it reaches the opposite
> backrank --> how does it work, execute move then choose ? or do both in the
> command line (in this case it is in the pawn class that it happens)
>
> --> how to actually do that ?
>
> dans la fonction launch_game, je mets un trigger au moment du execute move.
> - dans les fonctions de la class Board j'ajoute une fonction qui s'appelle
>   `_is_backrank_pawn_move`.
> - je fais appel à cette fonction dans un if/else statement dans le launch_game
>   au niveau de la fonction execute_move, et ce trigger demandera alors dans le
>   terminal quel piece on veut faire apparaitre à la place du pion.
> - Autre idée, executer le move et ensuite demander le changement ? à voir au
>   niveau de l'affichage plus tard pour faire un affichage persistent de
>   l'échiquier

---

## Idées pour la suite (« FINISHED THE GAME »)

> Let's see the future of the app,
> - front end ?
> - clock
> - possibility to import a game directly
> - a some point introducing the stalemate by unsufficient material. and the one
>   when someones clocks goes to 0 but the opponent did not have enough material
>   to mate.
> - possibility to import stockfish ?
> - server to play online ? --> later on

Ces pistes sont reprises et ordonnancées dans [`roadmap.md`](./roadmap.md).

---

## TODO — vérification des pats

> vérifier la détection des pats avec le pat en 10 coups --> vérification pour des
> pats avec pions et dame contre pions et rois. à voir vérifier les cas
> particuliers ou des pièces comme des cavaliers sont cloués.
>
> --> faire une fonction `init_pat()` dans chess_board avec la key
> "fastest_stalemate". Penser à introduire surement une variable pour dire si
> c'est trait aux blancs ou noirs et voir peut être le numéro du coup auquel on
> reprend.
>
> Cette idée de création de parties revient à regarder plus ou moins comment à
> l'avenir je pourrais upload une game. Se baser sur les formats de fichiers de
> chess.com par exemple.

Cette intuition est exactement celle retenue en §4.2 du roadmap : parties de
référence rejouées de bout en bout, et format PGN comme format pivot.

---

## Résolu

> - remarque : pas de détection des échecs en utilisant les mêmes fonctions
>   check_lines/check_diags/check_horses qui pourtant semble bien bloquer les
>   mouvements du roi dans certains cas. Ensuite problème entre un échec avec la
>   dame ou avec un fou
>
>   ---> réglé, je vérifiais `row+dr` out of `range(8)` alors que ça devait être
>   `row`, de même pour `dc`...
>
> - pb au moment de bloquer un échec -- copy_board etc ---> DEEPCOPY

---

## Problème du checkmate

> introduce the checkmate detection --> j'ai envie de réutiliser les fonctions de
> move_utility sauf que je ne suis pas sur de la partie avec le roi dans les
> "elif" --> donc à vérifier
>
> soucis si on fait une attaque à la découverte, le attacker n'est pas la
> dernière pièce à avoir bougé..
>
> s'il y a double échec comme on gère ça --> on ne regarde que les moves du roi.
>
> IDÉE --> garder une trace de qui attaque le roi suite à un échec afin de perdre
> moins de temps sur la vérif du checkmate.
>
> ----> à revérifier mais il faudrait modifier check_diags etc.... -> bien
> repenser ces fonctions qui sont souvent utilisées pour inclure les mouvements du
> roi // les check // checkmate.
>
> -----> localiser directement l'attaquant d'un échec permettrait de moins perdre
> de temps sur les vérifs d'échecs et mat.
>
> I suppose that if a double check occurs, moving the king is the only move
> because you cannot block to att the same time or you cannot eat one while
> blocking the other as there is no combinaison that allow this

> PB CHECKMATE - il semble que ça ne soit pas les bonnes fonctions que j'utilise
> pour voir si il y a checkmate ou pas. en gros je regarde les inbetween square et
> je regarde si on peut les bloquer or avec les pions il y a confusion entre le
> fait de pouvoir manger avec un pion ou alors bloquer en faisant avancer un pion.
>
> Moi je veux savoir est ce qu'un pion peut aller ou non sur une des cases entre
> l'attaquant et le roi. Dans les diagonales il y a une confusion sur le fait
> qu'on veut retourner False si on peut avancer un pion ou pas à la case
> souhaitée et non pas si la case "peut être mangée" c'est la subtilité avec
> `_is_in_check()` donc à corriger juste dans ce cas de figure. ---> de même via
> les lignes

Ce fil de réflexion est précisément ce que résout le générateur de coups légaux
(§4.0 du roadmap) : plus de raisonnement par cas « fuir / manger / bloquer ».
