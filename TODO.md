# Goal — cockpit TikTok piloté par agents

Demandes du 11 septembre 2026. Budget utilisateur : travailler jusqu’à environ **73 % restants du quota hebdomadaire Codex**, avec relevés périodiques. Ce seuil est une limite de travail, pas une cible de consommation inutile.

- [x] Direction photo : caméra invisible, gestes naturels, lumière motivée, références d’identité, contrôle des sorties.
- [x] Reprendre le récit Nami / Robin / Hancock en cinq images, corriger la manche et Hancock, conserver les versions et exporter la fiche.
- [x] Séries de 2 à 12 épisodes : plan, continuité, références de l’épisode précédent, numérotation et blocage des suites prématurées.
- [x] Rattacher un post existant au premier épisode et permettre aux agents de modifier seulement le plan des épisodes futurs.
- [x] Contrat agent partagé CLI/API, découverte des actions, boîte de réception, résolution des feedbacks et requêtes idempotentes.
- [x] Bibliothèque visuelle, recherche, filtres, grand lecteur, navigation clavier/tactile, accès rapide au feedback et aux téléchargements.
- [x] Séparer dépôt SQLite, règles de validation, commandes narratives et worker ; répartir React en composants/vues.
- [x] Recherche TikTok documentée et traduite en choix de produit sans fausse promesse de viralité.
- [x] Tests métier et UI (28 backend, 6 navigateur au dernier contrôle), inspection desktop/mobile.
- [x] Contrôler la production réelle des épisodes 2 et 3 : les quinze images de la série sont inspectées et disponibles.
- [x] Vérification finale des exports, documentation à jour et push privé.

## État réel

Série `937a277036ca42dfb34afae7f422deb5` : **L’île aux trois anneaux**.
Épisode 1 `8c4f87da9a7b40938311a06e881d4130` : prêt, cinq images inspectées, export CLI réalisé.
Épisode 2 `10d579911e1d44fea79963f2a791e54d` : prêt, cinq images inspectées et exportées.
Épisode 3 `60dfd97f13254304bb964aef2cdda02e` : prêt, cinq images inspectées et exportées ; conclusion de la série, pas de quatrième épisode prévu.

Dernier relevé direct : 75 % restants, 11 septembre 2026 à 01:26 UTC. Le périmètre est terminé avant le seuil de 73 % ; aucune génération supplémentaire n’est lancée pour consommer artificiellement la marge. Vérifier avec `python3 scripts/weekly_quota.py --live` avant un nouveau batch. Le plafond local facultatif est désactivé par défaut (`STUDIO_DAILY_IMAGES=0`) afin que les essais de cette nuit ne bloquent pas les prochaines demandes. Une valeur positive est testée et respectée. Ce réglage ne change pas les limites Codex.

Serveur détaché sur 8787 ; pas de LaunchAgent installé. Le Mac doit rester éveillé. Hermes n’est pas installé sur ce Mac : le contrat est prêt et testé, le raccordement depuis son environnement n’est pas présenté comme réalisé. Pas d’A/B testing, de fournisseur API payant, de reset de quota ni de publication automatique TikTok.

Intégrale locale vérifiée : `runtime/exports/ile-aux-trois-anneaux-integrale.zip` (15 PNG identiques aux versions actives, 3 fiches et légendes, mémoire de série). Les épisodes se téléchargent aussi séparément dans l’app. Les observations de qualité visuelle restent consignées dans docs/VALIDATION.md ; le créateur garde son jugement final.
