# Happy-League - Ultimate Québec

## Historique
Ce générateur d'horaires a été développé par Alexandre Lacoste, un membre actif de la communauté du ultimate
à Québec durant les années qu'il était ici pour ses études doctorales en intelligence artificielle. Comme il 
avait plusieurs équipes dans la ligue du dimanche, et qu'il détestait perdre une grande partie de sa journée à 
attendre son prochain match, il a développé le générateur durant ses temps libres.

Le générateur avait évidemment comme but de sauver du temps à la directrice générale de l'époque (qui fabriquait 
les horaires manuellement dans Excel), mais l'optimisation des horaires avait également comme but de permettre 
aux joueurs d'être dans plusieurs équipes, de sorte que leurs matchs seraient rapprochés (et ne seraient jamais
en même temps), lorsque possible. Cette contrainte a perdu un peu de sens depuis que nous ne jouons plus dans un 
seul stade. De nos jours, il serait pratiquement impossible de faire cette optimisation tout en respectant les 
contraintes d'uniformité.

Suite au départ d'Alexandre en Californie, Jean-Francis Roy a repris son projet. Il a rendu l'interface un peu
plus conviviale (pour l'époque), et a converti le code de Python 2 vers Python 3. Il n'a cependant pas participé
significativement à la conception. 

Le générateur a été hébergé pendant plusieurs années sur une instance EC2 dans amazon AWS, mais a maintenant été convertie en application locale.


## Implémentation actuelle
Le générateur d'horaires a comme entrée un fichier Excel (une demande du "client" de l'époque). Ce fichier contient
plusieurs tabs, pour configurer les équipes, les stades, les plages horaires et les contraintes utilisateur, qui 
s'ajoutent aux contraintes natives du générateur.

Le générateur est implémenté en Python, dans un "style" assez "libre" (il fait ce qu'il a à faire, mais le code est
difficile à lire). La méthode d'optimisation sélectionnée à l'époque est le _simulated annealing_, qui permet de faire 
une recherche de l'horaire optimal de manière stochastique. Chaque contrainte non respectée est associée à un coût, et 
l'optimiseur a pour mission de minimiser le coût associé à un horaire. L'optimisation s'exécute pendant un certain
temps, puis l'horaire avec le coût minimal est retourné.

## Les contraintes
Le générateur a des contraintes natives, dont le coût est très élevé si elles ne sont pas respectées, et des contraintes 
qui peuvent être ajoutées par l'utilisateur. 

Pour chaque division de `n` équipes, chaque équipe doit jouer un match contre les `n-1` autres équipes (round-robin).
Ce sont donc les matchs à placer sur l'horaire. L'horaire contient des plages horaires à certains stades, dans
lesquelles les matchs sont distribués.

Voici une liste (probablement non-exhaustive) des "contraintes" (je rappelle que chaque contrainte pourrait ne pas être 
respectée, mais un coût est associé à ce non-respect):

* Contrainte intégrée: Chaque équipe doit jouer 1 match par date.
* Contrainte optionnelle: On peut associer un coût au fait qu'une équipe joue sur un terrain ou une heure en
particulier. Cette contrainte est utilisée par le coordonnateur.
* Contrainte optionnelle: On peut associer un coût au fait que deux équipes jouent en même temps. Un coût additionnel
est accordé si l'équipe joue trop "loin" (en temps ou en terme de stade) de l'autre équipe. Cette contrainte n'est 
plus nécessaire de nos jours car la ligue ne désire pas avoir à gérer les joueurs qui ont choisi de faire partie de 
plusieurs équipes.
* Contrainte d'uniformité: Cette contrainte donne une pénalité lorsque certaines équipes ont trop de matchs dans une
plage horaire ou un stade, par rapport aux autres équipes de la ligue. Cette contrainte est très importante aux yeux de 
l'administration de la ligue.

## Recommandations

De nos jours, la génération d'horaires est un problème bien connu. Bien que ce soit un problème intrinsèquement
difficile et un domaine de recherche actif, les contraintes pour une ligne d'ultimate sont plutôt simples (nous n'avons 
pas de contraintes de matchs à l'étranger, de fêtes religieuses diverses, de revenus publicitaires télévisuels, etc.). 
La famille des solveurs généralement utilisée est la programmation par contraintes. Il existe des dizaines de librairies 
pour ce faire, notamment Google OR-Tools (C++, JAVA, Python, .NET) ou Choco (JAVA).

https://en.wikipedia.org/wiki/Constraint_programming#Constraint_programming

Si des changements devaient être apportés au générateur, je recommanderais fortement d'utiliser une librairie de 
programmation par contraintes. Le code serait plus facile à lire et à maintenir, et la génération d'horaires serait 
probablement plus rapide et plus efficace. Notons également que la programmation par contraintes est maintenant
enseignée dans un cours optionnel au baccalauréat en informatique à l'Université Laval: il pourrait être une bonne idée,
de tenter un partenariat avec le professeur et des étudiants - un nouveau générateur pourrait être développé comme
projet de session.

## Installation et exécution
L'exécution du générateur d'horaires requiert un environnement de programmation Python, avec [poetry](https://python-poetry.org/).

```
cd /path/to/happy-league
poetry install
poetry run src/happy_league
```

## Packaging en application locale
Le générateur peut être empaqueté en une application locale (Windows, MacOS, etc.) en utilisant _PyInstaller_. 

Pour créer une application Windows:
```
cd /path/to/happy-league
poetry install
poetry run pyinstaller happy_league.spec
```

Pour créer une application Mac OS:
```
cd /path/to/happy-league
poetry install
poetry run pyinstaller happy_league_macos.spec
```

L'exécutable résultant sera créé dans le dossier `dist/`.
