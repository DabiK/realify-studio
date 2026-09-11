import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function PostSheet({ pack, busy, act, notify, onPublish }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [sharing, setSharing] = useState(false);
  useEffect(() => {
    setForm(pack.post);
    setEditing(false);
  }, [pack.id, JSON.stringify(pack.post)]);
  const ready = pack.status === "ready" && pack.post;
  const share = async () => {
    if (!navigator.share || !navigator.canShare)
      return notify(
        "Le partage de fichiers dépend du navigateur et de HTTPS. Utilisez les téléchargements individuels ou le ZIP.",
      );
    setSharing(true);
    try {
      const files = await Promise.all(
        pack.slots.map(
          async (s, i) =>
            new File(
              [await (await fetch(media(s.active))).blob()],
              `${String(i + 1).padStart(2, "0")}_${s.key}.png`,
              { type: "image/png" },
            ),
        ),
      );
      if (!navigator.canShare({ files }))
        return notify(
          "Ces fichiers ne peuvent pas être partagés ici. Utilisez le ZIP ou les images individuelles.",
        );
      await navigator.share({ files, title: pack.title });
    } catch (e) {
      if (e.name !== "AbortError")
        notify("Le partage a échoué. Les téléchargements restent disponibles.");
    } finally {
      setSharing(false);
    }
  };
  return (
    <section className="post-sheet">
      <div className="section-line">
        <h2>Votre fiche TikTok</h2>
        {pack.post && (
          <button className="text-button" onClick={() => setEditing(!editing)}>
            <Icon name="edit" size={15} />
            {editing ? "Annuler" : "Modifier"}
          </button>
        )}
      </div>
      {!pack.post ? (
        <div className="sheet-pending">
          <Icon name="spark" />
          <p>
            Le titre, la description et les hashtags seront préparés à partir
            des images de ce post.
          </p>
        </div>
      ) : editing ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            act(async () => {
              await api(`/packs/${pack.id}/metadata`, form);
              setEditing(false);
              notify("Fiche mise à jour.");
            });
          }}
        >
          <label>
            Titre
            <input
              value={form.title}
              maxLength={120}
              required
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label>
            Description
            <textarea
              rows={5}
              value={form.description}
              maxLength={1800}
              required
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
            />
          </label>
          <label>
            Hashtags (1 à 5)
            <input
              value={form.hashtags.join(" ")}
              onChange={(e) =>
                setForm({ ...form, hashtags: e.target.value.split(/\s+/) })
              }
            />
          </label>
          <button className="secondary" disabled={busy}>
            Enregistrer
          </button>
        </form>
      ) : (
        <>
          <div className="copy-block">
            <div>
              <span className="eyebrow">TITRE DU POST</span>
              <button
                aria-label="Copier le titre"
                onClick={() => copy(pack.post.title, notify)}
              >
                <Icon name="copy" size={16} />
              </button>
            </div>
            <h3>{pack.post.title}</h3>
          </div>
          <div className="copy-block">
            <div>
              <span className="eyebrow">DESCRIPTION</span>
              <button
                aria-label="Copier la description"
                onClick={() => copy(pack.post.description, notify)}
              >
                <Icon name="copy" size={16} />
              </button>
            </div>
            <p className="caption">{pack.post.description}</p>
          </div>
          <div className="hashtags">
            {pack.post.hashtags.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
          <button
            className="text-button"
            onClick={() => copy(pack.caption, notify)}
          >
            <Icon name="copy" size={16} />
            Copier description + hashtags
          </button>
        </>
      )}
      <details className="upload-notes">
        <summary>À garder en tête pour TikTok</summary>
        <p>
          Choisissez le son dans TikTok et vérifiez l’ordre des images. Pour ces
          scènes réalistes créées par IA, activez l’étiquette adaptée lors de la
          publication.
        </p>
        <a
          href="https://support.tiktok.com/en/using-tiktok/creating-videos/ai-generated-content?authuser=0"
          target="_blank"
          rel="noreferrer"
        >
          Conseils TikTok sur les contenus IA ↗
        </a>
      </details>
      <div className="export-actions">
        {ready ? (
          <>
            <a className="primary" href={`/api/packs/${pack.id}/download`}>
              <Icon name="down" />
              Télécharger le post
            </a>
            <button className="secondary" disabled={sharing} onClick={share}>
              <Icon name="share" />
              {sharing ? "Préparation…" : "Partager les images"}
            </button>
          </>
        ) : (
          <button className="primary" disabled>
            <Icon name="down" />
            Le pack arrive bientôt
          </button>
        )}
      </div>
      <small className="download-note">
        ZIP : {pack.slots.length} images ordonnées + fiche du post. Sur
        téléphone, vous pouvez aussi télécharger chaque image séparément.
      </small>
      {ready && !pack.published_at && (
        <button
          className="published-button"
          disabled={busy}
          onClick={onPublish}
        >
          <Icon name="check" />
          Je l’ai publié sur TikTok
        </button>
      )}
      {pack.published_at && (
        <p className="published-line">
          <Icon name="check" />
          Marqué publié le {date(pack.published_at)}
          {pack.publication_url && (
            <a href={pack.publication_url} target="_blank" rel="noreferrer">
              Voir le post ↗
            </a>
          )}
        </p>
      )}
    </section>
  );
}
