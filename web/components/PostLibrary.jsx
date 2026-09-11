import React, { useState } from "react";
import { media, status, date } from "../lib";

export default function PostLibrary({ packs, selected, onSelect }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const filtered = packs.filter(
    (p) =>
      `${p.title} ${p.slots.map((s) => s.subject).join(" ")}`
        .toLocaleLowerCase()
        .includes(query.toLocaleLowerCase()) &&
      (filter === "all" ||
        (filter === "published"
          ? p.published_at
          : filter === "ready"
            ? p.status === "ready" && !p.published_at
            : filter === "review"
              ? !p.published_at && p.slots.some((s) => s.active)
              : ["queued", "running", "failed"].includes(p.status))),
  );
  return (
    <section className="post-library" aria-label="Bibliothèque des posts">
      <div className="library-tools">
        <label className="search-posts">
          <span>Retrouver un post</span>
          <input
            type="search"
            placeholder="Titre, personnage…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <div className="filter-tabs" aria-label="Filtrer les posts">
          {[
            ["all", "Tous"],
            ["review", "À regarder"],
            ["ready", "Prêts"],
            ["working", "En préparation"],
            ["published", "Publiés"],
          ].map(([id, label]) => (
            <button
              key={id}
              aria-pressed={filter === id}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="library-grid">
        {filtered.map((p) => (
          <button
            key={p.id}
            className={`post-tile ${p.id === selected ? "selected" : ""}`}
            aria-pressed={p.id === selected}
            onClick={() => onSelect(p.id)}
          >
            <div className="tile-art">
              {p.slots[0]?.active ? (
                <img src={media(p.slots[0].active)} alt="" loading="lazy" />
              ) : (
                <span className="tile-wait">Images en préparation</span>
              )}
              <span className={`tag ${p.status}`}>
                {p.published_at ? "Publié" : status[p.status]}
              </span>
              <span className="tile-count">
                {p.slots.filter((s) => s.active).length}/{p.slots.length}
              </span>
            </div>
            <div className="tile-copy">
              <small>
                {p.episode_number ? `ÉPISODE ${p.episode_number} · ` : ""}
                {date(p.created)}
              </small>
              <h3>{p.title}</h3>
              <div className="tile-film">
                {p.slots
                  .slice(1)
                  .map((s) =>
                    s.active ? (
                      <img
                        key={s.key}
                        src={media(s.active)}
                        alt=""
                        loading="lazy"
                      />
                    ) : (
                      <span key={s.key} />
                    ),
                  )}
              </div>
            </div>
          </button>
        ))}
      </div>
      {!filtered.length && (
        <p className="empty-filter">Aucun post pour ce filtre.</p>
      )}
    </section>
  );
}
