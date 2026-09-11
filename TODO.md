# Objectif actif — production photo et accès agent

Demandes utilisateur du 11 septembre 2026. Ce fichier est la mémoire de travail ; les cases cochées décrivent du travail vérifié.

- [x] Revoir le producteur : scènes vécues, caméra invisible, regards dirigés vers l’action, lumière motivée, variété des plans, références d’identité distinctes des poses et tenues.
- [x] Transmettre cette direction durablement à Realify sans imposer One Piece aux autres projets.
- [x] Préparer un découpage consultable avant génération et contrôler la continuité entre images.
- [x] Fournir une CLI JSON pour Hermes : lancer une image ou un batch, suivre les jobs, corriger, reprendre et récupérer les fichiers. Partager Store et la file de l’app ; conserver un worker unique.
- [x] Tester le contrat agent, documenter l’usage local et via SSH sur VPS. MCP facultatif : la CLI répond au besoin initial.
- [ ] Reprendre le post Nami / Robin / Hancock avec la nouvelle direction et inspecter les vrais rendus. Conserver les versions précédentes.
- [x] Pousser les changements sur le dépôt privé et préciser les limites de validation.

Contraintes : abonnement Codex uniquement ; pas d’A/B testing ; pas de publication automatique sur TikTok. Hermes n’est pas présenté comme connecté tant qu’un appel depuis son environnement n’a pas été vérifié.

Avancement : 14 tests backend passent, dont un parcours CLI avec fournisseur de test. Skill validé. Nouvelle couverture Nami générée réellement via la CLI et inspectée : cadrage par la porte, regard vers les mains, action lisible et lumière du hublot. Défaut de tatouage imprimé sur la manche corrigé ; job `ebed91d6f3384914a6b53cbe7d40e596` terminé et image finale inspectée. Trois versions de couverture conservées. Le serveur a été redémarré sans job actif et utilise le nouveau code Python. Les versions précédentes sont conservées.

À poursuivre : refaire Robin et les trois scènes manquantes selon [le découpage](docs/HEROINES-STORY.md). Le plafond local de 24 slots demandés / 24 h est atteint avec la dernière correction ; ne pas redemander les mêmes images en boucle. La disponibilité réelle de Codex reste distincte de ce plafond local. Hermes n’est pas installé sur ce Mac (`command -v hermes` absent, pas de dossier `~/.hermes`) ; son raccordement distant n’est pas prouvé, le contrat CLI est documenté et testé.
