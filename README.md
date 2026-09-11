# Studio / Realify

Un cockpit React pour préparer le prochain post, générer ses images avec Codex, donner un retour, retoucher une seule image et emporter le tout avec une fiche TikTok.

**Desktop et mobile, plusieurs univers, abonnement Codex uniquement.** Realify AI est préconfiguré avec sa DA One Piece et l’analyse des exports TikTok. Les autres projets ont leur propre style, sujets et références. Pas d’A/B testing ; pas de publication automatique sur TikTok.

## Démarrer sur le Mac

Prérequis : Node 22.12+, Python 3.11+, Codex CLI connecté avec ChatGPT et disposant du skill/outil natif de génération d’images. Testé localement avec Codex CLI 0.154.0. Une clé d’API n’est pas nécessaire et n’est pas utilisée.

```sh
npm ci
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
npm run build
python3 server.py
```

Ouvrir **http://localhost:8787**. Le code privé est créé dans `runtime/access-code` ; le lire localement pour se connecter. Aucun compte supplémentaire à créer. Garder le serveur et le Mac actifs pendant les générations.

Pour le téléphone sur le même réseau : `python3 server.py --host 0.0.0.0`, puis ouvrir `http://<adresse-LAN-du-Mac>:8787`. L’accès reste protégé par le même code. Pour accéder à distance et utiliser pleinement le partage natif, prévoir HTTPS ou un réseau privé ; le serveur local n’est pas un déploiement Internet.

## Utilisation

1. **Préparer mon prochain post** : le studio choisit une direction, génère cinq images et rédige titre, description et hashtags.
2. **Cliquer une image** : donner une consigne ou ajouter un texte exact. Chaque version reste disponible et restaurable.
3. **Garder un retour** : transmettre ses préférences aux futures créations du même univers.
4. **Télécharger le post** : ZIP avec images ordonnées, `caption.txt`, `post.json` et manifeste ; téléchargement individuel ou partage de fichiers également proposé.
5. **Je l’ai publié sur TikTok** : archiver localement la publication et préparer automatiquement la suivante si aucun brouillon n’attend. Cette automatisation se désactive dans Direction créative.

« Nouvel univers » crée un projet indépendant. Ajouter des références dans Direction créative. Le modèle Codex et la génération restent derrière l’interface ; aucun prompt obligatoire.

## Ce qui est dans le dépôt

- [Analyse de la chaîne et DA](docs/CHANNEL.md), calculs reproductibles dans `scripts/analyze.py` et exports privés dans `data/source/`.
- [Cadrage produit à jour](docs/PRODUCT.md) et [architecture / migration VPS](docs/ARCHITECTURE.md).
- React dans `web/`, API dans `server.py`, file persistante et génération dans `studio.py`.
- Skill générique `studio-producer` dans `.agents/skills/`, recopié dans les espaces de travail des jobs.
- [Validation et limites](docs/VALIDATION.md).

Les archives lourdes et les images nouvellement générées restent hors Git. Sur un clone neuf, la collection est vide ; les données analytiques et références initiales sont disponibles. Sauvegarder `runtime/` séparément pour migrer les posts.

## Développement et vérifications

```sh
# Dans un terminal : API avec worker
python3 server.py
# Dans un autre : React avec rechargement
npm run dev

# Vérifications sans appeler Codex ni consommer de génération
npm test
npm run build
npx playwright install chromium
npm run test:ui

# Recalcul exact des analytics
python3 scripts/analyze.py
```

Les tests navigateur lancent une base temporaire et un provider explicitement synthétique, jamais le compte Codex réel. Les erreurs de génération sont visibles ; les relances sont volontaires, les versions conservées. Plafond local par défaut : 40 demandes d’images sur 24 h. Voir les variables de configuration dans l’architecture.

L’ajout de texte dépend du rendu du moteur image et mérite une relecture. Les captions et hashtags sont adaptés au contenu, sans garantie de portée ni prétention de connaître les tendances du jour. Le déploiement VPS est documenté, pas encore effectué.

Pilotage par agent : voir [la CLI Hermes](docs/AGENT-CLI.md). Objectif actif et tâches restantes : [TODO.md](TODO.md).

## Cockpit piloté par agents

L’app sert à parcourir les posts, regarder les carrousels en grand, donner du feedback et télécharger. Les agents peuvent piloter les mêmes opérations avec `python3 cli.py capabilities`, `inbox` et `command --file demande.json`. Un `request_id` stable protège des doublons lors des reprises.

Les séries gardent leur plan et leur continuité d’un épisode à l’autre ; les images précédentes accompagnent la génération de la suite. Le formulaire propose trois épisodes, le contrat agent accepte des plans de 2 à 12 épisodes. Voir [le contrat agent](docs/AGENT-CLI.md), [l’architecture](docs/ARCHITECTURE.md), [les choix TikTok sourcés](docs/TIKTOK-RESEARCH.md) et [l’avancement](TODO.md).
