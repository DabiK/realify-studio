import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function PublishForm({ busy, onClose, onPublish, autoNext }) {
  const [url, setUrl] = useState("");
  return (
    <Modal title="Un post de plus dans votre histoire." onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onPublish(url);
        }}
      >
        <p>
          Vous avez publié ce post sur TikTok ? Marquez-le ici pour garder le
          fil.
          {autoNext &&
            " Le studio préparera automatiquement le suivant si aucun autre post n’attend."}
        </p>
        <label>
          Lien TikTok (facultatif)
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.tiktok.com/@…/video/…"
          />
        </label>
        <button className="primary" disabled={busy}>
          <Icon name="check" />
          Marquer comme publié
        </button>
        <small>Cette action ne publie rien sur TikTok.</small>
      </form>
    </Modal>
  );
}
