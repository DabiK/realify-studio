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
- [x] Tests métier et UI (22 backend, 6 navigateur au dernier contrôle), inspection desktop/mobile.
- [ ] Contrôler la production réelle de l’épisode 2 et, si le quota le permet, terminer le dernier épisode.
- [ ] Vérification finale des exports, documentation à jour et push privé.

## État réel

Série `937a277036ca42dfb34afae7f422deb5` : **L’île aux trois anneaux**.
Épisode 1 `8c4f87da9a7b40938311a06e881d4130` : prêt, cinq images inspectées, export CLI réalisé.
Épisode 2 `10d579911e1d44fea79963f2a791e54d` : job `10e28014455d42658bb68b7267baf261` lancé réellement par `cli.py command`.

Dernier relevé direct : 76 % restants, 11 septembre 2026 à 01:04 UTC. Vérifier avec `python3 scripts/weekly_quota.py --live` avant un nouveau batch. Le plafond local est de 40 slots/24 h ; il est distinct du quota Codex et a été ajusté pour les reprises et épisodes.

Serveur détaché sur 8787 ; pas de LaunchAgent installé. Le Mac doit rester éveillé. Hermes n’est pas installé sur ce Mac : le contrat est prêt et testé, le raccordement depuis son environnement n’est pas présenté comme réalisé. Pas d’A/B testing, de fournisseur API payant, de reset de quota ni de publication automatique TikTok.
