export const fmt = (n) =>
  new Intl.NumberFormat("fr-FR", {
    notation: n >= 10000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(n);
export const date = (n) =>
  new Date(n * 1000).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
  });
export const media = (file) => `/media/${file}`;
export const status = {
  ready: "Prêt à emporter",
  queued: "Dans la file",
  running: "Création en cours",
  failed: "À reprendre",
};
export async function api(path, body, signal) {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    signal,
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "La connexion a échoué.");
  return data;
}

export async function copy(value, notify) {
  try {
    await navigator.clipboard.writeText(value);
    notify("Copié.");
  } catch {
    notify(
      "La copie automatique demande HTTPS. Sélectionnez le texte et copiez-le avec le menu du navigateur.",
    );
  }
}

// randomUUID requires a secure context; LAN phone access can use plain HTTP.
export function requestId() {
  return Array.from(crypto.getRandomValues(new Uint32Array(4)), (n) =>
    n.toString(16),
  ).join("-");
}
