import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status, copy } from "../lib";
import { Icon, Modal } from "../components/ui";
export default function Analytics({ project }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (project.id !== "realify") return;
    const c = new AbortController();
    api("/analytics", undefined, c.signal)
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => c.abort();
  }, [project.id]);
  if (project.id !== "realify")
    return (
      <div className="empty-analysis">
        <Icon name="chart" size={38} />
        <h1>Une histoire à écrire.</h1>
        <p>
          Ce projet n’a pas encore d’analytics importées. Ses créations
          utiliseront votre direction artistique et vos retours, sans lui
          appliquer les chiffres de Realify.
        </p>
      </div>
    );
  if (!data) return <p>{error || "Lecture de vos résultats…"}</p>;
  const months = Object.entries(data.monthly);
  const max = Math.max(...months.map(([, v]) => v["Video Views"]));
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">REALIFY AI / EXPORT DU 11 SEPTEMBRE 2026</p>
          <h1>
            Ce que vos images
            <br />
            <em>nous ont appris.</em>
          </h1>
          <p>
            Des repères pour créer la suite. Des observations, pas des
            promesses.
          </p>
        </div>
        <span className="tag">DONNÉES IMPORTÉES</span>
      </div>
      <div className="stats-grid">
        {[
          ["Vues sur la période", data.totals["Video Views"]],
          ["Abonnés au 10 sept.", data.followers.current],
          ["Partages", data.totals.Shares],
          ["Publications dans l’export", data.posts.length],
        ].map(([label, value]) => (
          <div className="stat" key={label}>
            <span>{label}</span>
            <strong>{fmt(value)}</strong>
          </div>
        ))}
      </div>
      <div className="analytics-grid">
        <section className="chart-card">
          <div className="section-line">
            <h2>Le moment où tout a changé</h2>
            <span>Vues / mois</span>
          </div>
          <div
            className="bar-chart"
            role="img"
            aria-label="Pic de 2,71 millions de vues en octobre 2025, suivi d’une baisse progressive"
          >
            {months.map(([month, v]) => (
              <div
                key={month}
                title={`${month} : ${v["Video Views"].toLocaleString("fr-FR")} vues`}
              >
                <span
                  style={{
                    height: `${Math.max((v["Video Views"] / max) * 100, 1)}%`,
                  }}
                  className={month === "2025-10" ? "highlight" : ""}
                />
                <small>{month.slice(5)}</small>
              </div>
            ))}
          </div>
          <p>
            Le 2–16 octobre concentre <strong>69,6 % des vues</strong> de la
            période. Septembre 2025 et septembre 2026 couvrent des mois
            partiels.
          </p>
        </section>
        <section className="insight-card">
          <Icon name="spark" />
          <p className="eyebrow">LE REPÈRE ÉDITORIAL</p>
          <h2>
            Le spectaculaire
            <br />
            et le <em>spontané.</em>
          </h2>
          <p>
            1,8 M de vues pour les grands méchants. 7,49 % d’interactions pour
            les coulisses Part 3. Deux directions pour alimenter les prochains
            posts.
          </p>
          <small>
            Le format exact du post à 719 k vues reste à identifier.
          </small>
        </section>
      </div>
      <div className="section-line">
        <h2>Les publications qui donnent le ton</h2>
        <span>Compteurs « Total » de 15 posts exportés</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Publication</th>
              <th>Vues</th>
              <th>Interactions / vues</th>
              <th>Partages</th>
            </tr>
          </thead>
          <tbody>
            {data.posts.map((p, i) => (
              <tr key={p.id}>
                <td>
                  <span className="rank">{String(i + 1).padStart(2, "0")}</span>
                  <a href={p.url} target="_blank" rel="noreferrer">
                    {p.title}
                    <small>
                      {p.family} · {p.post_date_label}
                    </small>
                  </a>
                </td>
                <td>{fmt(p.views)}</td>
                <td>{p.interaction_rate.toFixed(2)} %</td>
                <td>{fmt(p.shares)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="audience-grid">
        <section className="post-sheet">
          <h2>Un public international</h2>
          <p>
            81 % masculin · France : 14,2 %. Le reste de l’audience se répartit
            dans de nombreux pays.
          </p>
          {Object.entries(data.followers.territories)
            .slice(0, 5)
            .map(([country, value]) => (
              <div className="territory" key={country}>
                <span>{country}</span>
                <div>
                  <span style={{ width: `${value * 5}%` }} />
                </div>
                <strong>{value} %</strong>
              </div>
            ))}
        </section>
        <section className="post-sheet">
          <h2>Les limites qui comptent</h2>
          <p>
            Pas de rétention ni d’abonnements par publication. Les formats sont
            classés à partir des captions, et les pics quotidiens ne sont pas
            attribués à un post.
          </p>
          <p>
            L’activité des abonnés culmine aux heures 15–17 de l’export, mais
            son fuseau n’est pas précisé.
          </p>
          <details>
            <summary>Voir la méthode et les réserves</summary>
            {data.caveats.map((c) => (
              <p key={c}>{c}</p>
            ))}
            <p>{data.viewers.note}</p>
            <p>{data.provenance.year_inference}</p>
            <p>{data.provenance.post_scope}</p>
          </details>
        </section>
      </div>
    </>
  );
}
