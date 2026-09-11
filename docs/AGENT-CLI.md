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
