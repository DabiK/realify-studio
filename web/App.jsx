import PostLibrary from "./components/PostLibrary";
import CarouselViewer from "./components/CarouselViewer";
import Stories from "./views/Stories";
import React, { useEffect, useRef, useState } from "react";
import { api, fmt, date, media, status } from "./lib";
import { Icon } from "./components/ui";
import Login from "./components/Login";
import Feedback from "./components/Feedback";
import PostSheet from "./components/PostSheet";
import ImageEditor from "./components/ImageEditor";
import ProjectForm from "./components/ProjectForm";
import GenerateForm from "./components/GenerateForm";
import PublishForm from "./components/PublishForm";
import Direction from "./views/Direction";
import Analytics from "./views/Analytics";
export default function App() {
  const [auth, setAuth] = useState(null);
  const [state, setState] = useState(null);
  const [projectId, setProjectId] = useState(
    localStorage.getItem("studio-project") || "realify",
  );
  const [tab, setTab] = useState("posts");
  const [packId, setPackId] = useState(
    localStorage.getItem("studio-pack") || null,
  );
  useEffect(() => {
    if (packId) localStorage.setItem("studio-pack", packId);
  }, [packId]);
  const [modal, setModal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const [loadError, setLoadError] = useState("");
  const [archives, setArchives] = useState({});
  const toastTimer = useRef();
  function notify(message) {
    setToast(message);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 6500);
  }
  const refresh = async (signal) => {
    const next = await api("/state", undefined, signal);
    setState(next);
    setLoadError("");
    return next;
  };
  useEffect(() => {
    api("/session")
      .then((r) => setAuth(r.authenticated))
      .catch((e) => setLoadError(e.message));
  }, []);
  useEffect(() => {
    if (!auth) return;
    const controller = new AbortController();
    let alive = true;
    let timer;
    const poll = async () => {
      try {
        await refresh(controller.signal);
      } catch (e) {
        if (alive) setLoadError(e.message);
      } finally {
        if (alive) timer = setTimeout(poll, 4000);
      }
    };
    poll();
    return () => {
      alive = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [auth]);
  useEffect(() => {
    if (!auth) return;
    let alive = true;
    Promise.all(
      ["doflamingo.jpg", "ace.jpg", "kaido.jpg"].map(async (name) => [
        name,
        (await api("/reference", { name })).image,
      ]),
    )
      .then((items) => {
        if (alive) setArchives(Object.fromEntries(items));
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [auth]);
  const act = async (work) => {
    setBusy(true);
    try {
      const result = await work();
      await refresh();
      return result;
    } catch (e) {
      notify(e.message);
    } finally {
      setBusy(false);
    }
  };
  const generate = (concept = "auto", notes = "") =>
    act(async () => {
      const p = await api("/packs", {
        project_id: projectId,
        concept_id: concept,
        notes,
      });
      setPackId(p.id);
      setTab("posts");
      setModal(null);
      notify(
        "Le studio prépare vos images et votre fiche TikTok. Vous pouvez fermer cette page.",
      );
    });
  const selectProject = (id) => {
    setProjectId(id);
    localStorage.setItem("studio-project", id);
    setPackId(null);
    setTab("posts");
  };
  if (auth === null)
    return (
      <div className="boot">
        <span className="wordmark">studio /</span>
        <p>{loadError || "Ouverture de votre atelier…"}</p>
        {loadError && (
          <button onClick={() => location.reload()}>Réessayer</button>
        )}
      </div>
    );
  if (!auth) return <Login onLogin={() => setAuth(true)} />;
  if (!state)
    return (
      <div className="boot">
        <span className="wordmark">studio /</span>
        <p>{loadError || "Chargement des projets…"}</p>
      </div>
    );
  const project =
    state.projects.find((p) => p.id === projectId) || state.projects[0];
  const packs = state.packs.filter((p) => p.project_id === project.id);
  const pack =
    packs.find((p) => p.id === packId) ||
    packs.find((p) => !p.published_at) ||
    packs[0];
  const jobs = state.jobs.filter((j) => packs.some((p) => p.id === j.pack_id));
  const working = jobs.filter((j) => ["running", "queued"].includes(j.state));
  const chosenJobs = pack ? jobs.filter((j) => j.pack_id === pack.id) : [];
  const activeJob = chosenJobs.find((j) =>
    ["running", "queued"].includes(j.state),
  );
  const latestFailed = chosenJobs[0]?.state === "failed" ? chosenJobs[0] : null;
  const reference = (name) =>
    archives[name] ? `data:image/jpeg;base64,${archives[name]}` : undefined;
  const selectedSlot =
    modal?.type === "image" && pack?.slots.find((s) => s.key === modal.slot);
  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          href="#"
          className="wordmark"
          onClick={(e) => {
            e.preventDefault();
            setTab("posts");
          }}
        >
          studio<span> /</span>
        </a>
        <span className="sidebar-label">VOTRE ESPACE</span>
        <div className="project-switch">
          <span className="project-avatar">{project.name.slice(0, 1)}</span>
          <select
            aria-label="Projet actif"
            value={project.id}
            onChange={(e) => selectProject(e.target.value)}
          >
            {state.projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
        <nav>
          {[
            ["posts", "grid", "Mes posts"],
            ["stories", "layers", "Les séries"],
            ["analysis", "chart", "Les enseignements"],
            ["direction", "layers", "Direction créative"],
          ].map(([id, icon, label]) => (
            <button
              key={id}
              className={tab === id ? "nav-item active" : "nav-item"}
              onClick={() => setTab(id)}
            >
              <Icon name={icon} />
              {label}
              {id === "posts" && <span>{packs.length}</span>}
            </button>
          ))}
        </nav>
        <button
          className="new-project"
          onClick={() => setModal({ type: "project" })}
        >
          <Icon name="plus" />
          Nouvel univers
        </button>
        <div className="sidebar-note">
          <span className="live-dot" />
          Votre atelier tourne en fond.
          <p>
            Les bonnes idées restent.
            <br />
            Les tâches répétitives s’effacent.
          </p>
        </div>
        <button
          className="nav-item logout"
          onClick={async () => {
            await api("/logout", {});
            setAuth(false);
            setState(null);
          }}
        >
          <Icon name="logout" />
          Déconnexion
        </button>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <span className="muted">Votre atelier</span>
            <span className="slash">/</span>
            {project.name}
          </div>
          <span className="engine">
            <span className={working.length ? "live-dot pulse" : "live-dot"} />
            {working.length
              ? `${working.length} création${working.length > 1 ? "s" : ""} en cours`
              : "À votre rythme"}
          </span>
        </header>
        <main className="content">
          {loadError && (
            <div role="alert" className="error connection-error">
              {loadError} Les données affichées peuvent être anciennes.
            </div>
          )}
          {tab === "posts" && (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">
                    L’ATELIER / {project.universe.toUpperCase()}
                  </p>
                  <h1>
                    Votre prochain post,
                    <br />
                    <em>sans partir de zéro.</em>
                  </h1>
                  <p>
                    Les images, les mots, la suite. Vous gardez le dernier
                    regard.
                  </p>
                </div>
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => generate()}
                >
                  <Icon name="spark" />
                  Préparer mon prochain post
                </button>
              </div>
              <PostLibrary
                packs={packs}
                selected={pack?.id}
                onSelect={(id) => {
                  setPackId(id);
                  requestAnimationFrame(() =>
                    document
                      .querySelector(".post-board")
                      ?.scrollIntoView({ behavior: "smooth", block: "start" }),
                  );
                }}
              />
              <div className="section-line">
                <h2>
                  {pack && !pack.published_at
                    ? "Sur votre table de travail"
                    : "Votre collection"}
                </h2>
                <span>
                  {
                    packs.filter((p) => p.status === "ready" && !p.published_at)
                      .length
                  }{" "}
                  prêt · {working.length} en préparation
                </span>
              </div>
              {pack ? (
                <>
                  <section className="post-board">
                    <div className="board-heading">
                      <div className="tags">
                        <span
                          className={`tag ${pack.published_at ? "published" : pack.status}`}
                        >
                          {pack.published_at ? "Publié" : status[pack.status]}
                        </span>
                        <span className="muted">
                          {date(pack.created)} · {pack.slots.length} images ·{" "}
                          {pack.ratio}
                        </span>
                      </div>
                      <div className="board-title">
                        <h2>{pack.title}</h2>
                        <span className="post-index">
                          N°{" "}
                          {String(packs.length - packs.indexOf(pack)).padStart(
                            2,
                            "0",
                          )}
                        </span>
                      </div>
                      {activeJob && (
                        <div className="progress">
                          <span className="spinner" />
                          <div>
                            <strong>
                              {activeJob.correction
                                ? "Votre retouche prend forme."
                                : "Le studio prépare votre post."}
                            </strong>
                            <p>
                              {activeJob.state === "queued"
                                ? "Il attend son tour. Les travaux passent un par un."
                                : "La génération peut prendre plusieurs minutes. Vous pouvez revenir plus tard."}
                            </p>
                          </div>
                        </div>
                      )}
                      {latestFailed && (
                        <div role="alert" className="failure">
                          <p>{latestFailed.message}</p>
                          <button
                            disabled={busy}
                            onClick={() =>
                              act(async () => {
                                await api(`/jobs/${latestFailed.id}/retry`, {});
                                notify(
                                  "La préparation reprend, en conservant les images déjà reçues.",
                                );
                              })
                            }
                          >
                            Reprendre la génération
                            <Icon name="arrow" />
                          </button>
                        </div>
                      )}
                    </div>
                    <CarouselViewer
                      key={pack.id}
                      pack={pack}
                      onEdit={(slot) => setModal({ type: "image", slot })}
                    />
                    <div className="board-footer">
                      <span>
                        <Icon name="edit" size={16} />
                        Un détail à changer ? Cliquez sur l’image.
                      </span>
                      <button
                        className="text-button"
                        onClick={() => setModal({ type: "generate" })}
                      >
                        Donner une idée au studio
                        <Icon name="arrow" size={16} />
                      </button>
                    </div>
                  </section>
                  <div className="post-bottom">
                    <PostSheet
                      pack={pack}
                      busy={busy}
                      act={act}
                      notify={notify}
                      onPublish={() => setModal({ type: "publish" })}
                    />
                    <section className="feedback-card">
                      <div className="section-icon">
                        <Icon name="message" />
                      </div>
                      <p className="eyebrow">VOTRE REGARD FAIT LA DIFFÉRENCE</p>
                      <h2>
                        Le studio apprend
                        <br />
                        <em>vos préférences.</em>
                      </h2>
                      <p>
                        Plus cinématographique, moins sombre, un autre style…
                        Votre retour accompagne les prochains posts de cet
                        univers.
                      </p>
                      <Feedback
                        pack={pack}
                        busy={busy}
                        act={act}
                        notify={notify}
                      />
                      {pack.feedback.length > 0 && (
                        <details>
                          <summary>
                            {pack.feedback.length} retour
                            {pack.feedback.length > 1 ? "s" : ""} conservé
                            {pack.feedback.length > 1 ? "s" : ""}
                          </summary>
                          {pack.feedback.slice(-4).map((f, i) => (
                            <p className="feedback-history" key={i}>
                              {f.text}
                              {f.resolution && (
                                <small className="agent-resolution">
                                  Suite donnée : {f.resolution}
                                </small>
                              )}
                            </p>
                          ))}
                        </details>
                      )}
                    </section>
                  </div>
                </>
              ) : (
                <section className="empty-studio">
                  <div className="empty-copy">
                    <span className="tag">TOUT COMMENCE ICI</span>
                    <h2>
                      Une direction.
                      <br />
                      <em>Des images qui vous ressemblent.</em>
                    </h2>
                    <p>
                      Le studio prépare un carrousel de cinq images et sa fiche
                      TikTok. Vous choisissez ce qui mérite d’être publié.
                    </p>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => generate()}
                    >
                      Lancer mon premier post
                      <Icon name="arrow" />
                    </button>
                  </div>
                  {project.id === "realify" ? (
                    <div className="archive-fan">
                      {["kaido.jpg", "doflamingo.jpg", "ace.jpg"].map(
                        (name, i) => (
                          <img
                            key={name}
                            className={`fan-${i}`}
                            src={reference(name)}
                            alt="Référence issue des archives Realify"
                          />
                        ),
                      )}
                      <span>VOTRE DA · ARCHIVES DE RÉFÉRENCE</span>
                    </div>
                  ) : (
                    <div className="abstract-stack">
                      <div />
                      <div />
                      <div />
                      <span>{project.universe}</span>
                    </div>
                  )}
                </section>
              )}
            </>
          )}
          {tab === "stories" && (
            <Stories
              project={project}
              stories={(state.stories || []).filter(
                (s) => s.project_id === project.id,
              )}
              packs={packs}
              act={act}
              busy={busy}
              notify={notify}
              onOpen={(id) => {
                setPackId(id);
                setTab("posts");
              }}
            />
          )}
          {tab === "analysis" && <Analytics project={project} />}
          {tab === "direction" && (
            <Direction
              project={project}
              act={act}
              notify={notify}
              archives={archives}
            />
          )}
          {tab === "posts" && pack && (
            <div className="review-dock">
              <button
                className="primary"
                onClick={() =>
                  document
                    .getElementById("feedback-panel")
                    ?.scrollIntoView({ behavior: "smooth", block: "center" })
                }
              >
                <Icon name="message" />
                Donner mon avis
              </button>
              {pack.status === "ready" && (
                <a
                  className="secondary"
                  href={`/api/packs/${pack.id}/download`}
                >
                  <Icon name="down" />
                  Emporter le post
                </a>
              )}
            </div>
          )}
          <footer className="page-footer">
            <span>studio /</span>
            <span>Votre créativité. Un peu plus de liberté.</span>
          </footer>
        </main>
      </div>
      {toast && (
        <div role="status" className="toast">
          {toast}
          <button
            aria-label="Fermer la notification"
            onClick={() => setToast("")}
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
      {modal?.type === "project" && (
        <ProjectForm
          onClose={() => setModal(null)}
          busy={busy}
          onCreate={(data) =>
            act(async () => {
              const p = await api("/projects", data);
              selectProject(p.id);
              setModal(null);
              notify("Votre nouvel univers est prêt.");
            })
          }
        />
      )}
      {modal?.type === "generate" && (
        <GenerateForm
          project={project}
          onClose={() => setModal(null)}
          busy={busy}
          onGenerate={generate}
        />
      )}
      {selectedSlot && (
        <ImageEditor
          slot={selectedSlot}
          pack={pack}
          busy={busy || !!activeJob}
          onClose={() => setModal(null)}
          onCorrect={(instruction) =>
            act(async () => {
              await api(`/packs/${pack.id}/correct`, {
                slot: selectedSlot.key,
                instruction,
              });
              setModal(null);
              notify("Retouche lancée. La version actuelle est conservée.");
            })
          }
          onRestore={(file) =>
            act(async () => {
              await api(`/packs/${pack.id}/restore`, {
                slot: selectedSlot.key,
                file,
              });
              notify("Version restaurée.");
            })
          }
        />
      )}
      {modal?.type === "publish" && (
        <PublishForm
          busy={busy}
          onClose={() => setModal(null)}
          autoNext={project.auto_next}
          onPublish={(url) =>
            act(async () => {
              const r = await api(`/packs/${pack.id}/publish`, { url });
              if (r.next) setPackId(r.next.id);
              setModal(null);
              notify(
                r.next_error
                  ? `Post marqué publié. ${r.next_error}`
                  : r.next
                    ? "Post marqué publié. Le suivant est déjà en préparation."
                    : "Post marqué publié.",
              );
            })
          }
        />
      )}
    </div>
  );
}
