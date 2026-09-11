# Validation — 11 septembre 2026

## Test réel de génération sur le Mac

Codex CLI 0.154.0, authentification ChatGPT existante, fonctionnalité `image_generation` active. Aucun appel à une API image payante ni clé API.

1. **Probe natif** : génération d’un portrait Doflamingo 1024×1536 par `codex exec` en arrière-plan. Fichier produit et ouvert pour inspection.
2. **Post complet** : cinq images natives 1024×1536 (Doflamingo, Kaido, Crocodile, Big Mom, Rob Lucci), fiche JSON title/description/hashtags, import dans le stockage de l’app. Images ouvertes en planche de contrôle. Titre proposé : « One Piece : audience au palais des monstres ».
3. **Édition réelle** : ajout exact de « DOFLAMINGO » en bas de la couverture via le même worker. Nouvelle version 1024×1536 inspectée ; texte correct et personnage conservé. Quatre autres slots inchangés ; couverture originale toujours présente.
4. **Relecture éditoriale** : la première description attribuait à Kaido une action non visible. Elle a été corrigée via le stockage de fiche. Les retours à la ligne littéraux sont désormais normalisés par la validation. La fiche est éditable dans l’app ; cette relecture humaine reste utile.

Les images et journaux réels sont dans `runtime/` sur le Mac, exclus de Git. Un clone neuf ne contient pas ces posts générés. Les références photographiques du dépôt proviennent des archives et sont explicitement décrites comme références.

## Vérifications automatisées

`npm test` : **12 tests réussis**. Totaux analytics et scope de dates, génération, retouche d’un seul slot, restauration, conservation des autres fichiers, import partiel et reprise ciblée, reprise d’une fiche sans images supplémentaires, séparation des projets, feedback transmis, publication locale idempotente et prochain post, désactivation de l’auto-next, récupération après interruption, refus des fichiers invalides, authentification, origine HTTP, téléchargement ZIP et déconnexion.

`npm run test:ui` : **4 parcours Playwright réussis**. Formats desktop / tablette / mobile (1440, 768, 390 px) sans débordement horizontal, lecture des analytics, téléchargement, persistance d’un feedback et d’une fiche modifiée, création d’un univers distinct, sauvegarde de sa direction, édition texte limitée à une image. Les tests utilisent un provider synthétique dans une base temporaire, sans démarrer de génération Codex.

`npm run build` : build React/Vite réussi. Inspection des captures de l’app réelle sur desktop et petit écran ; aucun événement `pageerror` au chargement. Skill `studio-producer` validé par le validateur de skills.

## Limites de la vérification

Pas de déploiement VPS effectué. Pas de test physique sur iPhone/Android : les petits écrans ont été vérifiés dans Chromium. Le partage de plusieurs images vers Photos/TikTok dépend du navigateur et de HTTPS ; le ZIP et les liens individuels sont disponibles. Pas de connexion ou publication TikTok effectuée.

Le chemin natif Codex est vérifié sur ce Mac ; sa disponibilité doit être retestée sur le futur VPS. Les projets génériques sont vérifiés fonctionnellement avec des fixtures ; le lot réel de validation est One Piece. La qualité graphique et la justesse des textes ne sont pas prouvées par les tests de fichiers.

## Révision photo et interface agent

14 tests backend passent. Une correction de la couverture du post `8c4f87da9a7b40938311a06e881d4130` a été déclenchée réellement par `cli.py`, consommée par le serveur et importée comme nouvelle version. La retouche finale `ebed91d6f3384914a6b53cbe7d40e596` est terminée ; image 1024×1536 inspectée, regard vers les mains, cadrage par la porte, lumière du hublot, manche corrigée sans emblème. Les trois versions existent encore. Cela valide le trajet CLI → file → Codex → stockage ; le batch via CLI et l’export ont été testés avec un provider synthétique. Hermes lui-même n’est pas installé ici. Le post féminin complet reste inachevé ; voir TODO.md.

## Cockpit agent et séries

- 24 tests backend : épisode suivant et références, isolation des univers, concurrence/idempotence, attachement d’un post, mise à jour du plan futur, feedback résolu sans suppression, authentification du contrat HTTP, progression reçue distincte de validation.
- 6 tests navigateur : anciennes fonctions préservées, filtres, navigation du lecteur, création de série et rechargement. Inspection de l’app réelle à 1440 et 390 px : aucun débordement ni erreur JavaScript constaté sur les vues posts/séries.
- Épisode 1 réel complet : `8c4f87da9a7b40938311a06e881d4130`, cinq images natives inspectées ; manche et identité/accessoires de Hancock retouchés ; export `runtime/exports/heroines-final`. La qualité est jugée visuellement, pas certifiée par un score automatique.
- Série réelle `937a277036ca42dfb34afae7f422deb5`, plan de trois épisodes et premier épisode rattaché sans modification des fichiers.
- Raccordement Hermes distant non testé ; CLI réelle testée pour correction/export et lancement d’épisode. Les tests de concurrence n’utilisent pas de quota image.
