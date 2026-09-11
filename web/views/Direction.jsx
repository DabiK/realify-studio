import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function Direction({ project, act, notify, archives }) {
  const [form, setForm] = useState({
    ...project,
    subjects: project.subjects.join(", "),
  });
  useEffect(
    () => setForm({ ...project, subjects: project.subjects.join(", ") }),
    [project.id],
  );
  const upload = async (file) => {
    if (!file) return;
    if (file.size > 8 * 1024 * 1024)
      return notify("Utiliser une image de moins de 8 Mo.");
    const reader = new FileReader();
    reader.onload = () =>
      act(async () => {
        await api(`/projects/${project.id}/reference`, {
          image: reader.result.split(",")[1],
        });
        notify("Référence ajoutée pour les prochaines créations.");
      });
    reader.readAsDataURL(file);
  };
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">LA MÉMOIRE DE VOTRE UNIVERS</p>
          <h1>
            Une signature.
            <br />
            <em>Jamais une formule.</em>
          </h1>
          <p>Ce que le studio garde en tête, à chaque nouvelle création.</p>
        </div>
      </div>
      <div className="direction-layout">
        <section className="post-sheet">
          <h2>{project.name}</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              act(async () => {
                await api(`/projects/${project.id}/update`, {
                  ...form,
                  subjects: form.subjects
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                });
                notify("Direction artistique enregistrée.");
              });
            }}
          >
            <label>
              Univers
              <input
                value={form.universe}
                maxLength={160}
                required
                onChange={(e) => setForm({ ...form, universe: e.target.value })}
              />
            </label>
            <label>
              Direction artistique
              <textarea
                rows={7}
                value={form.direction}
                maxLength={3000}
                required
                onChange={(e) =>
                  setForm({ ...form, direction: e.target.value })
                }
              />
            </label>
            <label>
              Sujets récurrents
              <input
                value={form.subjects}
                onChange={(e) => setForm({ ...form, subjects: e.target.value })}
                required
              />
            </label>
            <label>
              Format
              <select
                aria-label="Format"
                value={form.ratio}
                onChange={(e) => setForm({ ...form, ratio: e.target.value })}
              >
                <option value="2:3">Portrait · 2:3</option>
                <option value="1:1">Carré · 1:1</option>
                <option value="3:2">Paysage · 3:2</option>
              </select>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.auto_next}
                onChange={(e) =>
                  setForm({ ...form, auto_next: e.target.checked })
                }
              />
              Préparer le prochain post quand je marque le précédent publié
            </label>
            <button className="primary">
              Enregistrer ma direction
              <Icon name="check" />
            </button>
          </form>
        </section>
        <section className="references">
          <h2>Votre matière première</h2>
          <p>
            Des références visuelles pour donner le ton. Elles restent propres à
            cet univers.
          </p>
          <div className="reference-grid">
            {project.id === "realify" &&
              Object.entries(archives).map(([name, value]) => (
                <img
                  key={name}
                  src={`data:image/jpeg;base64,${value}`}
                  alt={`Archive Realify ${name}`}
                />
              ))}
            {project.reference_files.map((file) => (
              <img key={file} src={media(file)} alt="Référence du projet" />
            ))}
          </div>
          <label className="upload">
            <Icon name="plus" />
            Ajouter une référence
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => {
                upload(e.target.files[0]);
                e.target.value = "";
              }}
            />
          </label>
          <small>Jusqu’à 8 références personnelles · PNG, JPEG, WebP</small>
          {project.id === "realify" && (
            <div className="note">
              <strong>La mémoire Realify est déjà intégrée.</strong>
              <p>
                Personnages reconnaissables, textures photographiques, portraits
                cinéma et coulisses fictives. Vos archives servent de référence,
                pas de contenu nouvellement généré.
              </p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
