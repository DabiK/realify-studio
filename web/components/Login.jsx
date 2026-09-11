import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function Login({ onLogin }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const connect = async (value) => {
    setBusy(true);
    setError("");
    try {
      await api("/login", { code: value });
      onLogin();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    const value = new URLSearchParams(location.hash.slice(1)).get("code");
    if (value) {
      history.replaceState(null, "", location.pathname);
      connect(value);
    }
  }, []);
  return (
    <main className="login">
      <div className="login-art">
        <div className="orbit o1" />
        <div className="orbit o2" />
        <span className="wordmark">
          studio<span> /</span>
        </span>
        <div>
          <p className="eyebrow">MOINS DE FRICTION. PLUS DE CRÉATION.</p>
          <h1>
            Vos idées.
            <br />
            <em>
              Leur prochain
              <br />
              chapitre.
            </em>
          </h1>
        </div>
        <small>Un atelier privé, pour tous vos univers.</small>
      </div>
      <form
        className="login-form"
        onSubmit={(e) => {
          e.preventDefault();
          connect(code);
        }}
      >
        <span className="eyebrow">VOTRE ESPACE DE CRÉATION</span>
        <h2>Bienvenue au studio.</h2>
        <p>
          Retrouvez vos images, donnez votre avis et emportez votre prochain
          post.
        </p>
        <label>
          Code d’accès
          <input
            type="password"
            autoComplete="current-password"
            autoFocus
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
          />
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy}>
          {busy ? "Connexion…" : "Entrer dans le studio"}
          <Icon name="arrow" />
        </button>
        <small>
          Votre code se trouve sur la machine du studio, dans{" "}
          <code>runtime/access-code</code>.
        </small>
      </form>
    </main>
  );
}
