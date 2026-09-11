import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function Feedback({ pack, busy, act, notify }) {
  const [value, setValue] = useState("");
  useEffect(() => setValue(""), [pack.id]);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        act(async () => {
          await api(`/packs/${pack.id}/feedback`, { text: value });
          setValue("");
          notify("Retour conservé pour les prochains posts.");
        });
      }}
    >
      <label className="sr-only" htmlFor="feedback">
        Votre retour
      </label>
      <textarea
        id="feedback"
        placeholder="J’aime cette ambiance, mais je voudrais…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        maxLength={1500}
        required
        rows={3}
      />
      <button disabled={busy || !value.trim()} className="secondary">
        Garder ce retour
        <Icon name="arrow" size={16} />
      </button>
    </form>
  );
}
