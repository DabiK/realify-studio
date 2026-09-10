import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const fmt = (n) => new Intl.NumberFormat('fr-FR', { notation: n >= 10000 ? 'compact' : 'standard', maximumFractionDigits: 1 }).format(n);
const date = (n) => new Date(n * 1000).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
const media = (file) => `/media/${file}`;
const status = { ready: 'Prêt à emporter', queued: 'Dans la file', running: 'Création en cours', failed: 'À reprendre' };
async function api(path, body, signal) {
  const response = await fetch(`/api${path}`, { method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', signal,
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'La connexion a échoué.');
  return data;
}

function Icon({ name, size = 19 }) {
  const paths = {
    plus: <path d="M12 5v14M5 12h14" />, arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    chart: <><path d="M4 4v16h16M8 15l4-5 4 2 4-7" /></>, layers: <><path d="m12 3 10 5-10 5L2 8Zm-9 10 9 5 9-5m-18 5 9 5 9-5" /></>,
    down: <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" />, check: <path d="m5 12 4 4L19 6" />,
    edit: <><path d="m15 4 5 5M4 20l5-1L20 8a3.5 3.5 0 0 0-5-5L4 14Z" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />, copy: <><rect x="8" y="8" width="12" height="12" rx="2" /><path d="M15 8V4H4v11h4" /></>,
    spark: <path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5ZM20 2v4m-2-2h4" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    share: <><path d="M12 16V3m-4 4 4-4 4 4M6 10H3v11h18V10h-3" /></>,
    message: <path d="M21 15a3 3 0 0 1-3 3H9l-6 4V5a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3Z" />,
    logout: <path d="M9 4H3v16h6m5-13 5 5-5 5m-6-5h11" />,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.spark}</svg>;
}

function Modal({ title, children, onClose, wide = false }) {
  const ref = useRef();
  useEffect(() => { ref.current.showModal(); }, []);
  return <dialog ref={ref} className={wide ? 'modal wide' : 'modal'} onCancel={onClose} onClick={e => { if (e.target === ref.current) onClose(); }}>
    <div className="modal-head"><h2>{title}</h2><button className="icon-button" aria-label="Fermer" onClick={onClose}><Icon name="close" /></button></div>{children}
  </dialog>;
}

function Login({ onLogin }) {
  const [code, setCode] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const connect = async (value) => { setBusy(true); setError(''); try { await api('/login', { code: value }); onLogin(); } catch (e) { setError(e.message); } finally { setBusy(false); } };
  useEffect(() => { const value = new URLSearchParams(location.hash.slice(1)).get('code'); if (value) { history.replaceState(null, '', location.pathname); connect(value); } }, []);
  return <main className="login"><div className="login-art"><div className="orbit o1" /><div className="orbit o2" /><span className="wordmark">studio<span> /</span></span><div><p className="eyebrow">MOINS DE FRICTION. PLUS DE CRÉATION.</p><h1>Vos idées.<br /><em>Leur prochain<br />chapitre.</em></h1></div><small>Un atelier privé, pour tous vos univers.</small></div>
    <form className="login-form" onSubmit={e => { e.preventDefault(); connect(code); }}><span className="eyebrow">VOTRE ESPACE DE CRÉATION</span><h2>Bienvenue au studio.</h2><p>Retrouvez vos images, donnez votre avis et emportez votre prochain post.</p><label>Code d’accès<input type="password" autoComplete="current-password" autoFocus value={code} onChange={e => setCode(e.target.value)} required /></label>{error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>{busy ? 'Connexion…' : 'Entrer dans le studio'}<Icon name="arrow" /></button><small>Votre code se trouve sur la machine du studio, dans <code>runtime/access-code</code>.</small></form>
  </main>;
}

function App() {
  const [auth, setAuth] = useState(null); const [state, setState] = useState(null); const [projectId, setProjectId] = useState(localStorage.getItem('studio-project') || 'realify');
  const [tab, setTab] = useState('posts'); const [packId, setPackId] = useState(null); const [modal, setModal] = useState(null);
  const [busy, setBusy] = useState(false); const [toast, setToast] = useState(''); const [loadError, setLoadError] = useState(''); const [archives, setArchives] = useState({});
  const toastTimer = useRef();
  function notify(message) { setToast(message); clearTimeout(toastTimer.current); toastTimer.current = setTimeout(() => setToast(''), 6500); }
  const refresh = async (signal) => { const next = await api('/state', undefined, signal); setState(next); setLoadError(''); return next; };
  useEffect(() => { api('/session').then(r => setAuth(r.authenticated)).catch(e => setLoadError(e.message)); }, []);
  useEffect(() => {
    if (!auth) return;
    const controller = new AbortController(); let alive = true; let timer;
    const poll = async () => { try { await refresh(controller.signal); } catch (e) { if (alive) setLoadError(e.message); } finally { if (alive) timer = setTimeout(poll, 4000); } };
    poll();
    return () => { alive = false; controller.abort(); clearTimeout(timer); };
  }, [auth]);
  useEffect(() => { if (!auth) return; let alive = true; Promise.all(['doflamingo.jpg', 'ace.jpg', 'kaido.jpg'].map(async name => [name, (await api('/reference', { name })).image])).then(items => { if (alive) setArchives(Object.fromEntries(items)); }).catch(() => {}); return () => { alive = false; }; }, [auth]);
  const act = async (work) => { setBusy(true); try { const result = await work(); await refresh(); return result; } catch (e) { notify(e.message); } finally { setBusy(false); } };
  const generate = (concept = 'auto', notes = '') => act(async () => { const p = await api('/packs', { project_id: projectId, concept_id: concept, notes }); setPackId(p.id); setTab('posts'); setModal(null); notify('Le studio prépare vos images et votre fiche TikTok. Vous pouvez fermer cette page.'); });
  const selectProject = (id) => { setProjectId(id); localStorage.setItem('studio-project', id); setPackId(null); setTab('posts'); };
  if (auth === null) return <div className="boot"><span className="wordmark">studio /</span><p>{loadError || 'Ouverture de votre atelier…'}</p>{loadError && <button onClick={() => location.reload()}>Réessayer</button>}</div>;
  if (!auth) return <Login onLogin={() => setAuth(true)} />;
  if (!state) return <div className="boot"><span className="wordmark">studio /</span><p>{loadError || 'Chargement des projets…'}</p></div>;
  const project = state.projects.find(p => p.id === projectId) || state.projects[0];
  const packs = state.packs.filter(p => p.project_id === project.id);
  const pack = packs.find(p => p.id === packId) || packs.find(p => !p.published_at) || packs[0];
  const jobs = state.jobs.filter(j => packs.some(p => p.id === j.pack_id));
  const working = jobs.filter(j => ['running', 'queued'].includes(j.state));
  const chosenJobs = pack ? jobs.filter(j => j.pack_id === pack.id) : [];
  const activeJob = chosenJobs.find(j => ['running', 'queued'].includes(j.state));
  const latestFailed = chosenJobs[0]?.state === 'failed' ? chosenJobs[0] : null;
  const reference = (name) => archives[name] ? `data:image/jpeg;base64,${archives[name]}` : undefined;
  const selectedSlot = modal?.type === 'image' && pack?.slots.find(s => s.key === modal.slot);
  return <div className="shell">
    <aside className="sidebar"><a href="#" className="wordmark" onClick={e => { e.preventDefault(); setTab('posts'); }}>studio<span> /</span></a><span className="sidebar-label">VOTRE ESPACE</span>
      <div className="project-switch"><span className="project-avatar">{project.name.slice(0, 1)}</span><select aria-label="Projet actif" value={project.id} onChange={e => selectProject(e.target.value)}>{state.projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
      <nav>{[['posts', 'grid', 'Mes posts'], ['analysis', 'chart', 'Les enseignements'], ['direction', 'layers', 'Direction créative']].map(([id, icon, label]) => <button key={id} className={tab === id ? 'nav-item active' : 'nav-item'} onClick={() => setTab(id)}><Icon name={icon} />{label}{id === 'posts' && <span>{packs.length}</span>}</button>)}</nav>
      <button className="new-project" onClick={() => setModal({ type: 'project' })}><Icon name="plus" />Nouvel univers</button>
      <div className="sidebar-note"><span className="live-dot" />Votre atelier tourne en fond.<p>Les bonnes idées restent.<br />Les tâches répétitives s’effacent.</p></div>
      <button className="nav-item logout" onClick={async () => { await api('/logout', {}); setAuth(false); setState(null); }}><Icon name="logout" />Déconnexion</button>
    </aside>
    <div className="workspace"><header className="topbar"><div><span className="muted">Votre atelier</span><span className="slash">/</span>{project.name}</div><span className="engine"><span className={working.length ? 'live-dot pulse' : 'live-dot'} />{working.length ? `${working.length} création${working.length > 1 ? 's' : ''} en cours` : 'À votre rythme'}</span></header>
      <main className="content">{loadError && <div role="alert" className="error connection-error">{loadError} Les données affichées peuvent être anciennes.</div>}
      {tab === 'posts' && <>
        <div className="page-heading"><div><p className="eyebrow">L’ATELIER / {project.universe.toUpperCase()}</p><h1>Votre prochain post,<br /><em>sans partir de zéro.</em></h1><p>Les images, les mots, la suite. Vous gardez le dernier regard.</p></div><button className="primary" disabled={busy} onClick={() => generate()}><Icon name="spark" />Préparer mon prochain post</button></div>
        <div className="section-line"><h2>{pack && !pack.published_at ? 'Sur votre table de travail' : 'Votre collection'}</h2><span>{packs.filter(p => p.status === 'ready' && !p.published_at).length} prêt · {working.length} en préparation</span></div>
        {pack ? <>
          <section className="post-board"><div className="board-heading"><div className="tags"><span className={`tag ${pack.published_at ? 'published' : pack.status}`}>{pack.published_at ? 'Publié' : status[pack.status]}</span><span className="muted">{date(pack.created)} · {pack.slots.length} images · {pack.ratio}</span></div><div className="board-title"><h2>{pack.title}</h2><span className="post-index">N° {String(packs.length - packs.indexOf(pack)).padStart(2, '0')}</span></div>
          {activeJob && <div className="progress"><span className="spinner" /><div><strong>{activeJob.correction ? 'Votre retouche prend forme.' : 'Le studio prépare votre post.'}</strong><p>{activeJob.state === 'queued' ? 'Il attend son tour. Les travaux passent un par un.' : 'La génération peut prendre plusieurs minutes. Vous pouvez revenir plus tard.'}</p></div></div>}
          {latestFailed && <div role="alert" className="failure"><p>{latestFailed.message}</p><button disabled={busy} onClick={() => act(async () => { await api(`/jobs/${latestFailed.id}/retry`, {}); notify('La préparation reprend, en conservant les images déjà reçues.'); })}>Reprendre la génération<Icon name="arrow" /></button></div>}
          </div><div className="image-strip">{pack.slots.map((slot, i) => <div className="slide" key={slot.key}><button className="slide-image" style={{ aspectRatio: pack.ratio.replace(':', ' / ') }} disabled={!slot.active} aria-label={`Ouvrir ${slot.subject}`} onClick={() => setModal({ type: 'image', slot: slot.key })}>{slot.active ? <img src={media(slot.active)} alt={slot.subject} loading={i ? 'lazy' : 'eager'} /> : <div className="image-placeholder"><Icon name="spark" size={28} /><span>{slot.subject}</span><small>{activeJob ? 'En préparation' : 'Image attendue'}</small></div>}<span className="slide-number">{String(i + 1).padStart(2, '0')}</span>{slot.active && <span className="edit-hover"><Icon name="edit" />Retoucher</span>}</button><div className="slide-label"><span>{slot.subject}</span>{slot.active && <a aria-label={`Télécharger ${slot.subject}`} href={`${media(slot.active)}?download=1`}><Icon name="down" size={16} /></a>}</div></div>)}</div>
          <div className="board-footer"><span><Icon name="edit" size={16} />Un détail à changer ? Cliquez sur l’image.</span><button className="text-button" onClick={() => setModal({ type: 'generate' })}>Donner une idée au studio<Icon name="arrow" size={16} /></button></div></section>
          <div className="post-bottom"><PostSheet pack={pack} busy={busy} act={act} notify={notify} onPublish={() => setModal({ type: 'publish' })} />
            <section className="feedback-card"><div className="section-icon"><Icon name="message" /></div><p className="eyebrow">VOTRE REGARD FAIT LA DIFFÉRENCE</p><h2>Le studio apprend<br /><em>vos préférences.</em></h2><p>Plus cinématographique, moins sombre, un autre style… Votre retour accompagne les prochains posts de cet univers.</p><Feedback pack={pack} busy={busy} act={act} notify={notify} />{pack.feedback.length > 0 && <details><summary>{pack.feedback.length} retour{pack.feedback.length > 1 ? 's' : ''} conservé{pack.feedback.length > 1 ? 's' : ''}</summary>{pack.feedback.slice(-4).map((f, i) => <p className="feedback-history" key={i}>{f.text}</p>)}</details>}</section>
          </div>
        </> : <section className="empty-studio"><div className="empty-copy"><span className="tag">TOUT COMMENCE ICI</span><h2>Une direction.<br /><em>Des images qui vous ressemblent.</em></h2><p>Le studio prépare un carrousel de cinq images et sa fiche TikTok. Vous choisissez ce qui mérite d’être publié.</p><button className="primary" disabled={busy} onClick={() => generate()}>Lancer mon premier post<Icon name="arrow" /></button></div>{project.id === 'realify' ? <div className="archive-fan">{['kaido.jpg', 'doflamingo.jpg', 'ace.jpg'].map((name, i) => <img key={name} className={`fan-${i}`} src={reference(name)} alt="Référence issue des archives Realify" />)}<span>VOTRE DA · ARCHIVES DE RÉFÉRENCE</span></div> : <div className="abstract-stack"><div /><div /><div /><span>{project.universe}</span></div>}</section>}
        {packs.length > 1 && <><div className="section-line"><h2>Les autres posts</h2><span>Votre mémoire de création</span></div><div className="collection">{packs.filter(p => p.id !== pack?.id).map(p => <button key={p.id} className="collection-card" onClick={() => { setPackId(p.id); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>{p.slots[0].active ? <img src={media(p.slots[0].active)} alt="" /> : <div className="mini-placeholder"><Icon name="clock" /></div>}<div><span className="eyebrow">{p.published_at ? 'PUBLIÉ' : status[p.status]}</span><h3>{p.title}</h3><small>{date(p.created)} · {p.slots.length} images</small></div><Icon name="arrow" /></button>)}</div></>}
      </>}
      {tab === 'analysis' && <Analytics project={project} />}
      {tab === 'direction' && <Direction project={project} act={act} notify={notify} archives={archives} />}
      <footer className="page-footer"><span>studio /</span><span>Votre créativité. Un peu plus de liberté.</span></footer>
      </main></div>
      {toast && <div role="status" className="toast">{toast}<button aria-label="Fermer la notification" onClick={() => setToast('')}><Icon name="close" size={16} /></button></div>}
      {modal?.type === 'project' && <ProjectForm onClose={() => setModal(null)} busy={busy} onCreate={data => act(async () => { const p = await api('/projects', data); selectProject(p.id); setModal(null); notify('Votre nouvel univers est prêt.'); })} />}
      {modal?.type === 'generate' && <GenerateForm project={project} onClose={() => setModal(null)} busy={busy} onGenerate={generate} />}
      {selectedSlot && <ImageEditor slot={selectedSlot} pack={pack} busy={busy || !!activeJob} onClose={() => setModal(null)} onCorrect={instruction => act(async () => { await api(`/packs/${pack.id}/correct`, { slot: selectedSlot.key, instruction }); setModal(null); notify('Retouche lancée. La version actuelle est conservée.'); })} onRestore={file => act(async () => { await api(`/packs/${pack.id}/restore`, { slot: selectedSlot.key, file }); notify('Version restaurée.'); })} />}
      {modal?.type === 'publish' && <PublishForm busy={busy} onClose={() => setModal(null)} autoNext={project.auto_next} onPublish={url => act(async () => { const r = await api(`/packs/${pack.id}/publish`, { url }); if (r.next) setPackId(r.next.id); setModal(null); notify(r.next_error ? `Post marqué publié. ${r.next_error}` : r.next ? 'Post marqué publié. Le suivant est déjà en préparation.' : 'Post marqué publié.'); })} />}
  </div>;
}

function Feedback({ pack, busy, act, notify }) {
  const [value, setValue] = useState('');
  useEffect(() => setValue(''), [pack.id]);
  return <form onSubmit={e => { e.preventDefault(); act(async () => { await api(`/packs/${pack.id}/feedback`, { text: value }); setValue(''); notify('Retour conservé pour les prochains posts.'); }); }}><label className="sr-only" htmlFor="feedback">Votre retour</label><textarea id="feedback" placeholder="J’aime cette ambiance, mais je voudrais…" value={value} onChange={e => setValue(e.target.value)} maxLength={1500} required rows={3} /><button disabled={busy || !value.trim()} className="secondary">Garder ce retour<Icon name="arrow" size={16} /></button></form>;
}

async function copy(value, notify) {
  try { await navigator.clipboard.writeText(value); notify('Copié.'); } catch { notify('La copie automatique demande HTTPS. Sélectionnez le texte et copiez-le avec le menu du navigateur.'); }
}

function PostSheet({ pack, busy, act, notify, onPublish }) {
  const [editing, setEditing] = useState(false); const [form, setForm] = useState(null); const [sharing, setSharing] = useState(false);
  useEffect(() => { setForm(pack.post); setEditing(false); }, [pack.id, JSON.stringify(pack.post)]);
  const ready = pack.status === 'ready' && pack.post;
  const share = async () => {
    if (!navigator.share || !navigator.canShare) return notify('Le partage de fichiers dépend du navigateur et de HTTPS. Utilisez les téléchargements individuels ou le ZIP.');
    setSharing(true);
    try { const files = await Promise.all(pack.slots.map(async (s, i) => new File([await (await fetch(media(s.active))).blob()], `${String(i + 1).padStart(2, '0')}_${s.key}.png`, { type: 'image/png' }))); if (!navigator.canShare({ files })) return notify('Ces fichiers ne peuvent pas être partagés ici. Utilisez le ZIP ou les images individuelles.'); await navigator.share({ files, title: pack.title }); } catch (e) { if (e.name !== 'AbortError') notify('Le partage a échoué. Les téléchargements restent disponibles.'); } finally { setSharing(false); }
  };
  return <section className="post-sheet"><div className="section-line"><h2>Votre fiche TikTok</h2>{pack.post && <button className="text-button" onClick={() => setEditing(!editing)}><Icon name="edit" size={15} />{editing ? 'Annuler' : 'Modifier'}</button>}</div>
    {!pack.post ? <div className="sheet-pending"><Icon name="spark" /><p>Le titre, la description et les hashtags seront préparés à partir des images de ce post.</p></div> : editing ? <form onSubmit={e => { e.preventDefault(); act(async () => { await api(`/packs/${pack.id}/metadata`, form); setEditing(false); notify('Fiche mise à jour.'); }); }}>
      <label>Titre<input value={form.title} maxLength={120} required onChange={e => setForm({ ...form, title: e.target.value })} /></label><label>Description<textarea rows={5} value={form.description} maxLength={1800} required onChange={e => setForm({ ...form, description: e.target.value })} /></label><label>Hashtags (1 à 5)<input value={form.hashtags.join(' ')} onChange={e => setForm({ ...form, hashtags: e.target.value.split(/\s+/) })} /></label><button className="secondary" disabled={busy}>Enregistrer</button>
    </form> : <><div className="copy-block"><div><span className="eyebrow">TITRE DU POST</span><button aria-label="Copier le titre" onClick={() => copy(pack.post.title, notify)}><Icon name="copy" size={16} /></button></div><h3>{pack.post.title}</h3></div><div className="copy-block"><div><span className="eyebrow">DESCRIPTION</span><button aria-label="Copier la description" onClick={() => copy(pack.post.description, notify)}><Icon name="copy" size={16} /></button></div><p className="caption">{pack.post.description}</p></div><div className="hashtags">{pack.post.hashtags.map(t => <span key={t}>{t}</span>)}</div><button className="text-button" onClick={() => copy(pack.caption, notify)}><Icon name="copy" size={16} />Copier description + hashtags</button></>}
    <div className="export-actions">{ready ? <><a className="primary" href={`/api/packs/${pack.id}/download`}><Icon name="down" />Télécharger le post</a><button className="secondary" disabled={sharing} onClick={share}><Icon name="share" />{sharing ? 'Préparation…' : 'Partager les images'}</button></> : <button className="primary" disabled><Icon name="down" />Le pack arrive bientôt</button>}</div><small className="download-note">ZIP : 5 images ordonnées + fiche du post. Sur téléphone, vous pouvez aussi télécharger chaque image séparément.</small>
    {ready && !pack.published_at && <button className="published-button" disabled={busy} onClick={onPublish}><Icon name="check" />Je l’ai publié sur TikTok</button>}{pack.published_at && <p className="published-line"><Icon name="check" />Marqué publié le {date(pack.published_at)}{pack.publication_url && <a href={pack.publication_url} target="_blank" rel="noreferrer">Voir le post ↗</a>}</p>}
  </section>;
}

function ImageEditor({ slot, pack, busy, onClose, onCorrect, onRestore }) {
  const [mode, setMode] = useState('edit'); const [instruction, setInstruction] = useState(''); const [overlay, setOverlay] = useState(''); const [position, setPosition] = useState('en bas');
  return <Modal title={slot.subject} onClose={onClose} wide><div className="image-editor"><div className="editor-preview"><img src={media(slot.active)} alt={slot.subject} /></div><div className="editor-controls"><p className="eyebrow">UN DÉTAIL, PAS TOUT RECOMMENCER</p><h3>Gardez ce qui<br /><em>vous plaît.</em></h3><div className="segmented"><button className={mode === 'edit' ? 'selected' : ''} onClick={() => setMode('edit')}>Retoucher</button><button className={mode === 'text' ? 'selected' : ''} onClick={() => setMode('text')}>Ajouter du texte</button></div><form onSubmit={e => { e.preventDefault(); onCorrect(mode === 'edit' ? instruction : `Ajouter uniquement le texte exact ${JSON.stringify(overlay)} ${position}, en capitales blanches lisibles avec ombre subtile, sans couvrir le visage. Garder la photographie, les couleurs et tous les autres éléments inchangés. Vérifier l’orthographe exacte.`); }}>
      {mode === 'edit' ? <label>Votre consigne<textarea autoFocus rows={5} value={instruction} onChange={e => setInstruction(e.target.value)} maxLength={1200} placeholder="Éclaircis le visage, garde le décor et les vêtements." required /></label> : <><label>Texte exact<input value={overlay} maxLength={160} onChange={e => setOverlay(e.target.value)} placeholder="DOFLAMINGO" required /></label><label>Position<select aria-label="Position" value={position} onChange={e => setPosition(e.target.value)}><option>en bas</option><option>en haut</option><option>au centre</option></select></label></>}
      <button className="primary" disabled={busy}><Icon name="spark" />{busy ? 'Génération déjà en cours' : 'Créer une nouvelle version'}</button><small>Cette image seule sera retravaillée. L’original reste disponible.</small></form>
      <div className="version-list"><h4>Historique · {slot.versions.length} version{slot.versions.length > 1 ? 's' : ''}</h4>{[...slot.versions].reverse().map((v, i) => <div key={v.file}><span>Version {slot.versions.length - i}<small>{v.instruction || 'Génération originale'}</small></span>{v.file === slot.active ? <span className="tag">Actuelle</span> : <button disabled={busy} onClick={() => onRestore(v.file)}>Restaurer</button>}</div>)}</div><a className="text-button" href={`${media(slot.active)}?download=1`}><Icon name="down" />Télécharger cette image</a></div></div></Modal>;
}

function ProjectForm({ onClose, busy, onCreate }) {
  const [form, setForm] = useState({ name: '', universe: '', direction: '', subjects: '', ratio: '2:3' });
  return <Modal title="Un nouvel univers" onClose={onClose}><form className="project-form" onSubmit={e => { e.preventDefault(); onCreate({ ...form, subjects: form.subjects.split(',').map(s => s.trim()).filter(Boolean) }); }}><p>Une autre chaîne, une collection de produits, des paysages… Chaque projet garde sa propre direction et ses retours.</p>{[['name', 'Nom du projet', 'Atelier botanique'], ['universe', 'Univers / type d’images', 'Photographie de plantes et intérieurs'], ['subjects', 'Sujets récurrents, séparés par des virgules', 'Monstera, cactus, orchidée']].map(([key, label, placeholder]) => <label key={key}>{label}<input value={form[key]} maxLength={key === 'subjects' ? 1500 : 150} required placeholder={placeholder} onChange={e => setForm({ ...form, [key]: e.target.value })} /></label>)}<label>Direction artistique<textarea value={form.direction} rows={4} maxLength={3000} required placeholder="Lumière douce du matin, murs crème, photographie éditoriale, détails naturels…" onChange={e => setForm({ ...form, direction: e.target.value })} /></label><label>Format<select aria-label="Format" value={form.ratio} onChange={e => setForm({ ...form, ratio: e.target.value })}><option value="2:3">Portrait · 2:3</option><option value="1:1">Carré · 1:1</option><option value="3:2">Paysage · 3:2</option></select></label><button className="primary" disabled={busy}>Créer cet univers<Icon name="arrow" /></button></form></Modal>;
}

function GenerateForm({ project, onClose, busy, onGenerate }) {
  const [notes, setNotes] = useState('');
  return <Modal title="Une idée pour la suite ?" onClose={onClose}><form onSubmit={e => { e.preventDefault(); onGenerate('auto', notes); }}><p>Donnez simplement une direction. Le studio s’occupe des scènes, des images et de la fiche pour {project.name}.</p><label>Votre idée (facultatif)<textarea rows={5} value={notes} maxLength={2000} onChange={e => setNotes(e.target.value)} placeholder="Un post plus lumineux, sur un plateau en plein air…" /></label><button className="primary" disabled={busy}>Préparer ce nouveau post<Icon name="spark" /></button></form></Modal>;
}

function PublishForm({ busy, onClose, onPublish, autoNext }) {
  const [url, setUrl] = useState('');
  return <Modal title="Un post de plus dans votre histoire." onClose={onClose}><form onSubmit={e => { e.preventDefault(); onPublish(url); }}><p>Vous avez publié ce post sur TikTok ? Marquez-le ici pour garder le fil.{autoNext && ' Le studio préparera automatiquement le suivant si aucun autre post n’attend.'}</p><label>Lien TikTok (facultatif)<input type="url" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://www.tiktok.com/@…/video/…" /></label><button className="primary" disabled={busy}><Icon name="check" />Marquer comme publié</button><small>Cette action ne publie rien sur TikTok.</small></form></Modal>;
}

function Direction({ project, act, notify, archives }) {
  const [form, setForm] = useState({ ...project, subjects: project.subjects.join(', ') });
  useEffect(() => setForm({ ...project, subjects: project.subjects.join(', ') }), [project.id]);
  const upload = async file => {
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) return notify('Utiliser une image de moins de 8 Mo.');
    const reader = new FileReader(); reader.onload = () => act(async () => { await api(`/projects/${project.id}/reference`, { image: reader.result.split(',')[1] }); notify('Référence ajoutée pour les prochaines créations.'); }); reader.readAsDataURL(file);
  };
  return <><div className="page-heading"><div><p className="eyebrow">LA MÉMOIRE DE VOTRE UNIVERS</p><h1>Une signature.<br /><em>Jamais une formule.</em></h1><p>Ce que le studio garde en tête, à chaque nouvelle création.</p></div></div><div className="direction-layout"><section className="post-sheet"><h2>{project.name}</h2><form onSubmit={e => { e.preventDefault(); act(async () => { await api(`/projects/${project.id}/update`, { ...form, subjects: form.subjects.split(',').map(s => s.trim()).filter(Boolean) }); notify('Direction artistique enregistrée.'); }); }}><label>Univers<input value={form.universe} maxLength={160} required onChange={e => setForm({ ...form, universe: e.target.value })} /></label><label>Direction artistique<textarea rows={7} value={form.direction} maxLength={3000} required onChange={e => setForm({ ...form, direction: e.target.value })} /></label><label>Sujets récurrents<input value={form.subjects} onChange={e => setForm({ ...form, subjects: e.target.value })} required /></label><label>Format<select aria-label="Format" value={form.ratio} onChange={e => setForm({ ...form, ratio: e.target.value })}><option value="2:3">Portrait · 2:3</option><option value="1:1">Carré · 1:1</option><option value="3:2">Paysage · 3:2</option></select></label><label className="checkbox"><input type="checkbox" checked={form.auto_next} onChange={e => setForm({ ...form, auto_next: e.target.checked })} />Préparer le prochain post quand je marque le précédent publié</label><button className="primary">Enregistrer ma direction<Icon name="check" /></button></form></section><section className="references"><h2>Votre matière première</h2><p>Des références visuelles pour donner le ton. Elles restent propres à cet univers.</p><div className="reference-grid">{project.id === 'realify' && Object.entries(archives).map(([name, value]) => <img key={name} src={`data:image/jpeg;base64,${value}`} alt={`Archive Realify ${name}`} />)}{project.reference_files.map(file => <img key={file} src={media(file)} alt="Référence du projet" />)}</div><label className="upload"><Icon name="plus" />Ajouter une référence<input type="file" accept="image/png,image/jpeg,image/webp" onChange={e => { upload(e.target.files[0]); e.target.value = ''; }} /></label><small>Jusqu’à 8 références personnelles · PNG, JPEG, WebP</small>{project.id === 'realify' && <div className="note"><strong>La mémoire Realify est déjà intégrée.</strong><p>Personnages reconnaissables, textures photographiques, portraits cinéma et coulisses fictives. Vos archives servent de référence, pas de contenu nouvellement généré.</p></div>}</section></div></>;
}

function Analytics({ project }) {
  const [data, setData] = useState(null); const [error, setError] = useState('');
  useEffect(() => { if (project.id !== 'realify') return; const c = new AbortController(); api('/analytics', undefined, c.signal).then(setData).catch(e => { if (e.name !== 'AbortError') setError(e.message); }); return () => c.abort(); }, [project.id]);
  if (project.id !== 'realify') return <div className="empty-analysis"><Icon name="chart" size={38} /><h1>Une histoire à écrire.</h1><p>Ce projet n’a pas encore d’analytics importées. Ses créations utiliseront votre direction artistique et vos retours, sans lui appliquer les chiffres de Realify.</p></div>;
  if (!data) return <p>{error || 'Lecture de vos résultats…'}</p>;
  const months = Object.entries(data.monthly); const max = Math.max(...months.map(([, v]) => v['Video Views']));
  return <><div className="page-heading"><div><p className="eyebrow">REALIFY AI / EXPORT DU 11 SEPTEMBRE 2026</p><h1>Ce que vos images<br /><em>nous ont appris.</em></h1><p>Des repères pour créer la suite. Des observations, pas des promesses.</p></div><span className="tag">DONNÉES IMPORTÉES</span></div><div className="stats-grid">{[['Vues sur la période', data.totals['Video Views']], ['Abonnés au 10 sept.', data.followers.current], ['Partages', data.totals.Shares], ['Publications dans l’export', data.posts.length]].map(([label, value]) => <div className="stat" key={label}><span>{label}</span><strong>{fmt(value)}</strong></div>)}</div><div className="analytics-grid"><section className="chart-card"><div className="section-line"><h2>Le moment où tout a changé</h2><span>Vues / mois</span></div><div className="bar-chart" role="img" aria-label="Pic de 2,71 millions de vues en octobre 2025, suivi d’une baisse progressive">{months.map(([month, v]) => <div key={month} title={`${month} : ${v['Video Views'].toLocaleString('fr-FR')} vues`}><span style={{ height: `${Math.max(v['Video Views'] / max * 100, 1)}%` }} className={month === '2025-10' ? 'highlight' : ''} /><small>{month.slice(5)}</small></div>)}</div><p>Le 2–16 octobre concentre <strong>69,6 % des vues</strong> de la période. Septembre 2025 et septembre 2026 couvrent des mois partiels.</p></section><section className="insight-card"><Icon name="spark" /><p className="eyebrow">LE REPÈRE ÉDITORIAL</p><h2>Le spectaculaire<br />et le <em>spontané.</em></h2><p>1,8 M de vues pour les grands méchants. 7,49 % d’interactions pour les coulisses Part 3. Deux directions pour alimenter les prochains posts.</p><small>Le format exact du post à 719 k vues reste à identifier.</small></section></div><div className="section-line"><h2>Les publications qui donnent le ton</h2><span>Compteurs « Total » de 15 posts exportés</span></div><div className="table-wrap"><table><thead><tr><th>Publication</th><th>Vues</th><th>Interactions / vues</th><th>Partages</th></tr></thead><tbody>{data.posts.map((p, i) => <tr key={p.id}><td><span className="rank">{String(i + 1).padStart(2, '0')}</span><a href={p.url} target="_blank" rel="noreferrer">{p.title}<small>{p.family} · {p.post_date_label}</small></a></td><td>{fmt(p.views)}</td><td>{p.interaction_rate.toFixed(2)} %</td><td>{fmt(p.shares)}</td></tr>)}</tbody></table></div><div className="audience-grid"><section className="post-sheet"><h2>Un public international</h2><p>81 % masculin · France : 14,2 %. Le reste de l’audience se répartit dans de nombreux pays.</p>{Object.entries(data.followers.territories).slice(0, 5).map(([country, value]) => <div className="territory" key={country}><span>{country}</span><div><span style={{ width: `${value * 5}%` }} /></div><strong>{value} %</strong></div>)}</section><section className="post-sheet"><h2>Les limites qui comptent</h2><p>Pas de rétention ni d’abonnements par publication. Les formats sont classés à partir des captions, et les pics quotidiens ne sont pas attribués à un post.</p><p>L’activité des abonnés culmine aux heures 15–17 de l’export, mais son fuseau n’est pas précisé.</p><details><summary>Voir la méthode et les réserves</summary>{data.caveats.map(c => <p key={c}>{c}</p>)}<p>{data.viewers.note}</p><p>{data.provenance.year_inference}</p><p>{data.provenance.post_scope}</p></details></section></div></>;
}

createRoot(document.getElementById('root')).render(<App />);
