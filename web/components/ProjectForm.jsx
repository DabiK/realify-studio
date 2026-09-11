import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function ProjectForm({ onClose, busy, onCreate }) {
  const [form, setForm] = useState({
    name: "",
    universe: "",
    direction: "",
    subjects: "",
    ratio: "2:3",
  });
  return (
    <Modal title="Un nouvel univers" onClose={onClose}>
      <form
        className="project-form"
        onSubmit={(e) => {
          e.preventDefault();
          onCreate({
            ...form,
            subjects: form.subjects
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
          });
        }}
      >
        <p>
          Une autre chaîne, une collection de produits, des paysages… Chaque
          projet garde sa propre direction et ses retours.
        </p>
        {[
          ["name", "Nom du projet", "Atelier botanique"],
          [
            "universe",
            "Univers / type d’images",
            "Photographie de plantes et intérieurs",
          ],
          [
            "subjects",
            "Sujets récurrents, séparés par des virgules",
            "Monstera, cactus, orchidée",
          ],
        ].map(([key, label, placeholder]) => (
          <label key={key}>
            {label}
            <input
              value={form[key]}
              maxLength={key === "subjects" ? 1500 : 150}
              required
              placeholder={placeholder}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </label>
        ))}
        <label>
          Direction artistique
          <textarea
            value={form.direction}
            rows={4}
            maxLength={3000}
            required
            placeholder="Lumière douce du matin, murs crème, photographie éditoriale, détails naturels…"
            onChange={(e) => setForm({ ...form, direction: e.target.value })}
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
        <button className="primary" disabled={busy}>
          Créer cet univers
          <Icon name="arrow" />
        </button>
      </form>
    </Modal>
  );
}
