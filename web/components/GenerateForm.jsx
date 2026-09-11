import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function GenerateForm({ project, onClose, busy, onGenerate }) {
  const [notes, setNotes] = useState("");
  return (
    <Modal title="Une idée pour la suite ?" onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onGenerate("auto", notes);
        }}
      >
        <p>
          Donnez simplement une direction. Le studio s’occupe des scènes, des
          images et de la fiche pour {project.name}.
        </p>
        <label>
          Votre idée (facultatif)
          <textarea
            rows={5}
            value={notes}
            maxLength={2000}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Un post plus lumineux, sur un plateau en plein air…"
          />
        </label>
        <button className="primary" disabled={busy}>
          Préparer ce nouveau post
          <Icon name="spark" />
        </button>
      </form>
    </Modal>
  );
}
