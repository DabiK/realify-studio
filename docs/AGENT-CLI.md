# Piloter Studio depuis Hermes

La CLI Python est un adaptateur local du même `Store` que l’API React. Elle dépose des jobs dans SQLite ; elle ne lance ni worker supplémentaire ni fournisseur image. Le serveur Studio doit fonctionner pour traiter les demandes. Un batch contient 1 à 5 images dans un post ; plusieurs posts se demandent séparément. Aucun MCP n’est nécessaire pour ce contrat initial.

Depuis le dossier du dépôt :

```sh
python3 cli.py projects
python3 cli.py generate --project realify --count 1 --subject 'Nami' --notes-file /chemin/brief.txt
python3 cli.py generate --project realify --count 5 --subject 'Nami' --subject 'Nico Robin' --subject 'Boa Hancock' --notes-file /chemin/brief.txt
python3 cli.py status PACK_ID
python3 cli.py jobs
python3 cli.py correct PACK_ID --slot cover --instruction-file /chemin/correction.txt
python3 cli.py retry JOB_ID
python3 cli.py export PACK_ID --output /chemin/nouveau-dossier
```

`generate` retourne `result.pack.id` et `result.jobs`. Succès : `{"ok":true,"result":...}` sur stdout, code 0. Erreur métier ou fichier : `{"ok":false,"error":"..."}`, code 1. Erreur de syntaxe CLI : aide argparse sur stderr, code 2. Statut job : queued, running, completed, failed. `status` fournit les versions et les chemins relatifs des images ; `export` fournit les chemins absolus copiés et la fiche JSON. L’export exige toutes les images et la fiche et refuse d’écraser un dossier existant.

Hermes doit conserver les identifiants retournés puis consulter `status` à intervalle raisonnable. Après un timeout client, consulter `jobs` avant de renvoyer une demande : `generate` n’est pas idempotent. Ne pas relancer automatiquement un refus de sécurité ou une erreur de quota. `retry` ne reprend que les sorties manquantes du job en échec ; `correct` conserve la version originale.

Les notes UTF-8 (2 000 caractères max) et corrections (1 500 max) passent par fichiers. Utiliser une liste d’arguments de processus, sans interpolation shell de contenu généré. Le budget local partagé compte toutes les demandes, UI et CLI. La CLI utilise les droits filesystem du compte local ; elle ne requiert pas le code d’accès navigateur et n’expose pas de service réseau.

`--runtime /chemin/runtime` avant la sous-commande, ou `STUDIO_RUNTIME`, sélectionne le même volume que le serveur. Par défaut : `runtime` du dépôt. Sur VPS, installer le dépôt et ses dépendances, connecter Codex avec l’abonnement, puis exécuter la CLI sur l’hôte via SSH ou depuis Hermes installé sur cet hôte. Ne pas partager SQLite via un filesystem réseau. La connexion SSH/Hermes effective dépend de son environnement et n’a pas été testée ici.

## Contrat agent v1 et séries

La commande recommandée est désormais `python3 cli.py command --file demande.json`. Le contrat de découverte est fourni par `python3 cli.py capabilities` et [agent-contract.json](agent-contract.json). L’API authentifiée offre le même service via `POST /api/commands` ; aucune connexion TikTok n’est impliquée.

```json
{"action":"story.create","request_id":"hermes-histoire-2026-001","data":{"project_id":"realify","title":"Le secret du phare","premise":"Trois voyageurs suivent une lumière qui ne devrait plus exister.","subjects":["Nami","Nico Robin","Boa Hancock"],"continuity":"Même bateau et boussole turquoise.","outline":[{"title":"Le signal","beat":"Découvrir le phare allumé et décider de s’en approcher.","ending":"Une silhouette apparaît à la fenêtre."},{"title":"La gardienne","beat":"Retrouver la gardienne isolée et l’aider à réparer sa lanterne.","ending":"Le phare guide à nouveau les bateaux."}]}}
```

Puis envoyer `story.next` avec `data.story_id` et un nouvel identifiant stable par épisode. La création de série ne consomme aucune génération. `story.attach` rattache un post complet comme premier épisode d’une série vide, sans changer ses images. `story.next` exige les épisodes précédents complets ; un épisode défaillant doit être repris, pas sauté. La mémoire transmise contient le plan, les règles de continuité, les fiches et retours précédents, et la première/dernière image du précédent épisode.

**Idempotence :** conserver exactement le même `request_id`, action et contenu après une perte de réponse. Le résultat initial est rejoué sans nouvelle mutation, y compris après la fin d’une retouche. Un identifiant réutilisé pour un autre contenu est refusé. Résultat et mutation sont enregistrés dans la même transaction SQLite. Cette garantie concerne `command` et `/api/commands`, ainsi que les routes de création auxquelles un identifiant est fourni ; les anciens raccourcis `generate`, `correct` et `retry` restent disponibles mais ne portent pas de reçu de requête.

**Boucle agent :** lire `inbox` → choisir un post ou un retour → `pack.correct` / `pack.metadata` / `story.next` → suivre `jobs` et `status` → inspecter l’image → `feedback.resolve` avec le `feedback_id` et une explication de la suite donnée → exporter. Résoudre un feedback conserve son texte ; cela ne signifie pas que l’utilisateur a approuvé le rendu. Les anciens retours sans identifiant restent de la mémoire éditoriale. Aucune commande ne publie sur TikTok ; le marquage de publication reste une action locale explicite dans l’app.

`python3 scripts/weekly_quota.py --live` consulte uniquement les limites de compte via Codex app-server, sans lancer de tour de modèle ni consommer de crédit de réinitialisation. Sans `--live`, la commande lit le dernier relevé des journaux locaux ; vérifier son horodatage. Le pourcentage hebdomadaire n’est pas le plafond de demandes d’images du studio. [Documentation officielle Codex App Server](https://developers.openai.com/codex/app-server).

`story.update` permet de changer titre, prémisse, personnages, continuité et épisodes futurs. Le plan des épisodes déjà créés est immuable ; toute tentative de le réécrire est refusée. Les briefs des épisodes en cours sont des snapshots et ne changent pas au milieu d’une génération.
