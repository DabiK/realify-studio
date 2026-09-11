import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function ImageEditor({
  slot,
  pack,
  busy,
  onClose,
  onCorrect,
  onRestore,
}) {
  const [mode, setMode] = useState("edit");
  const [instruction, setInstruction] = useState("");
  const [overlay, setOverlay] = useState("");
  const [position, setPosition] = useState("en bas");
  return (
    <Modal title={slot.subject} onClose={onClose} wide>
      <div className="image-editor">
        <div className="editor-preview">
          <img src={media(slot.active)} alt={slot.subject} />
        </div>
        <div className="editor-controls">
          <p className="eyebrow">UN DÉTAIL, PAS TOUT RECOMMENCER</p>
          <h3>
            Gardez ce qui
            <br />
            <em>vous plaît.</em>
          </h3>
          <div className="segmented">
            <button
              className={mode === "edit" ? "selected" : ""}
              onClick={() => setMode("edit")}
            >
              Retoucher
            </button>
            <button
              className={mode === "text" ? "selected" : ""}
              onClick={() => setMode("text")}
            >
              Ajouter du texte
            </button>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              onCorrect(
                mode === "edit"
                  ? instruction
                  : `Ajouter uniquement le texte exact ${JSON.stringify(overlay)} ${position}, en capitales blanches lisibles avec ombre subtile, sans couvrir le visage. Garder la photographie, les couleurs et tous les autres éléments inchangés. Vérifier l’orthographe exacte.`,
              );
            }}
          >
            {mode === "edit" ? (
              <label>
                Votre consigne
                <textarea
                  autoFocus
                  rows={5}
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  maxLength={1200}
                  placeholder="Éclaircis le visage, garde le décor et les vêtements."
                  required
                />
              </label>
            ) : (
              <>
                <label>
                  Texte exact
                  <input
                    value={overlay}
                    maxLength={160}
                    onChange={(e) => setOverlay(e.target.value)}
                    placeholder="DOFLAMINGO"
                    required
                  />
                </label>
                <label>
                  Position
                  <select
                    aria-label="Position"
                    value={position}
                    onChange={(e) => setPosition(e.target.value)}
                  >
                    <option>en bas</option>
                    <option>en haut</option>
                    <option>au centre</option>
                  </select>
                </label>
              </>
            )}
            <button className="primary" disabled={busy}>
              <Icon name="spark" />
              {busy ? "Génération déjà en cours" : "Créer une nouvelle version"}
            </button>
            <small>
              Cette image seule sera retravaillée. L’original reste disponible.
            </small>
          </form>
          <div className="version-list">
            <h4>
              Historique · {slot.versions.length} version
              {slot.versions.length > 1 ? "s" : ""}
            </h4>
            {[...slot.versions].reverse().map((v, i) => (
              <div key={v.file}>
                <span>
                  Version {slot.versions.length - i}
                  <small>{v.instruction || "Génération originale"}</small>
                </span>
                {v.file === slot.active ? (
                  <span className="tag">Actuelle</span>
                ) : (
                  <button disabled={busy} onClick={() => onRestore(v.file)}>
                    Restaurer
                  </button>
                )}
              </div>
            ))}
          </div>
          <a className="text-button" href={`${media(slot.active)}?download=1`}>
            <Icon name="down" />
            Télécharger cette image
          </a>
        </div>
      </div>
    </Modal>
  );
}
