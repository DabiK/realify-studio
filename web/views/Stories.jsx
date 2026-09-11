import React, { useState, useRef } from "react";
import { api, media, status, requestId } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function Stories({
  project,
  stories,
  packs,
  act,
  busy,
  notify,
  onOpen,
}) {
  const creationId = useRef(requestId());
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ title: "", premise: "", continuity: "" });
  return (
    <section className="stories-view">
      <div className="page-heading">
        <div>
          <p className="eyebrow">UN UNIVERS. PLUSIEURS CHAPITRES.</p>
          <h1>
            Les histoires
            <br />
            <em>qui continuent.</em>
          </h1>
          <p>
            Les personnages restent. Chaque épisode fait avancer l’histoire.
          </p>
        </div>
        <button className="primary" onClick={() => setCreating(true)}>
          <Icon name="plus" />
          Nouvelle série
        </button>
      </div>
      {!stories.length && (
        <div className="story-empty">
          <span>01 → 02 → 03</span>
          <h2>Une idée peut vivre plus d’un post.</h2>
          <p>
            Définissez une histoire. Le studio garde son fil, ses personnages et
            vos retours pour préparer chaque suite.
          </p>
        </div>
      )}
      {stories.map((story) => (
        <article className="story-card" key={story.id}>
          <div className="section-line">
            <div>
              <span className="eyebrow">
                {story.episodes.length} / {story.outline.length} ÉPISODES
                PRÉPARÉS
              </span>
              <h2>{story.title}</h2>
            </div>
            <button
              className="secondary"
              disabled={
                busy ||
                story.episodes.length >= story.outline.length ||
                story.episodes.some(
                  (id) => packs.find((p) => p.id === id)?.status !== "ready",
                )
              }
              onClick={() =>
                act(async () => {
                  const p = await api(`/stories/${story.id}/next`, {
                    request_id: `episode-${story.id}-${story.episodes.length + 1}`,
                  });
                  notify("L’épisode est en préparation.");
                  onOpen(p.id);
                })
              }
            >
              {story.episodes.length >= story.outline.length
                ? "Série complète"
                : story.episodes.length
                  ? "Préparer la suite"
                  : "Préparer l’épisode 1"}
              <Icon name="arrow" />
            </button>
          </div>
          <p>{story.premise}</p>
          <div className="episode-grid">
            {story.outline.map((ep, i) => {
              const pack = packs.find((p) => p.id === story.episodes[i]);
              return (
                <div className="episode-card" key={i}>
                  <span className="episode-number">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {pack?.slots[0]?.active && (
                    <img src={media(pack.slots[0].active)} alt="" />
                  )}
                  <h3>{ep.title}</h3>
                  <p>{ep.beat}</p>
                  <details>
                    <summary>Fin de l’épisode</summary>
                    <p>{ep.ending}</p>
                  </details>
                  {pack ? (
                    <button
                      className="text-button"
                      onClick={() => onOpen(pack.id)}
                    >
                      Ouvrir · {status[pack.status]} ↗
                    </button>
                  ) : (
                    <small>À venir</small>
                  )}
                </div>
              );
            })}
          </div>
          <details>
            <summary>La mémoire de cette série</summary>
            <p>
              {story.continuity ||
                "Les images et les fiches précédentes accompagneront chaque épisode."}
            </p>
            <p>{story.subjects.join(" · ")}</p>
          </details>
        </article>
      ))}
      {creating && (
        <Modal title="Créer une série" onClose={() => setCreating(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                await api("/stories", {
                  project_id: project.id,
                  ...form,
                  request_id: creationId.current,
                });
                setCreating(false);
                creationId.current = requestId();
                setForm({ title: "", premise: "", continuity: "" });
                notify("Série créée : trois épisodes, prêts à développer.");
              });
            }}
          >
            <label>
              Nom de la série
              <input
                required
                maxLength={120}
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </label>
            <label>
              L’histoire en quelques mots
              <textarea
                required
                maxLength={2000}
                rows={4}
                value={form.premise}
                onChange={(e) => setForm({ ...form, premise: e.target.value })}
              />
            </label>
            <label>
              Ce qui doit rester cohérent
              <textarea
                maxLength={3000}
                rows={3}
                placeholder="Personnages, lieux, tenues, objet clé…"
                value={form.continuity}
                onChange={(e) =>
                  setForm({ ...form, continuity: e.target.value })
                }
              />
            </label>
            <p className="muted">
              Trois épisodes pour commencer : découverte, épreuve, résolution.
              Créer la série ne lance pas d’images.
            </p>
            <button className="primary" disabled={busy}>
              Créer la série
            </button>
          </form>
        </Modal>
      )}
    </section>
  );
}
