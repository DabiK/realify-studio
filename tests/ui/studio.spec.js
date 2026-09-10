import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Code d’accès").fill("browser-test-only");
  await page.getByRole("button", { name: "Entrer dans le studio" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Votre prochain post, sans partir de zéro.",
    }),
  ).toBeVisible();
});

test("desktop and mobile layouts, analytics and download", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
  const downloaded = page.waitForEvent("download");
  await page
    .getByRole("link", { name: "Télécharger le post", exact: true })
    .click();
  expect((await downloaded).suggestedFilename()).toMatch(/studio-.*\.zip/);
  await page.getByRole("button", { name: "Les enseignements" }).click();
  await expect(
    page.getByRole("heading", { name: "Les publications qui donnent le ton" }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(15);
  expect(errors).toEqual([]);
});

test("feedback and editable post sheet persist after refresh", async ({
  page,
}) => {
  await page
    .getByLabel("Votre retour", { exact: true })
    .fill("Une lumière plus naturelle pour la suite.");
  await page.getByRole("button", { name: "Garder ce retour" }).click();
  await expect(page.getByRole("status")).toContainText("Retour conservé");
  await page.getByRole("button", { name: "Modifier", exact: true }).click();
  await page
    .getByLabel("Titre", { exact: true })
    .fill("Titre corrigé par le créateur");
  await page.getByRole("button", { name: "Enregistrer", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Fiche mise à jour");
  await page.reload();
  await expect(
    page
      .getByRole("heading", { name: "Titre corrigé par le créateur" })
      .first(),
  ).toBeVisible();
  await expect(page.getByText("1 retour conservé")).toBeVisible();
});

test("new universe has its own direction and no Realify analytics", async ({
  page,
}) => {
  await page.getByRole("button", { name: "Nouvel univers" }).click();
  await page.getByLabel("Nom du projet").fill("Atelier botanique");
  await page.getByLabel("Univers / type d’images").fill("Botanique");
  await page
    .getByLabel("Sujets récurrents, séparés par des virgules")
    .fill("Orchidée, Monstera");
  await page
    .getByLabel("Direction artistique", { exact: true })
    .fill("Photographie naturelle, fond crème, lumière du matin.");
  await page.getByLabel("Format", { exact: true }).selectOption("1:1");
  await page.getByRole("button", { name: "Créer cet univers" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Une direction. Des images qui vous ressemblent.",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Les enseignements" }).click();
  await expect(
    page.getByRole("heading", { name: "Une histoire à écrire." }),
  ).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(0);
  await page.getByRole("button", { name: "Direction créative" }).click();
  await expect(page.getByLabel("Univers", { exact: true })).toHaveValue(
    "Botanique",
  );
  await page
    .getByLabel("Préparer le prochain post quand je marque le précédent publié")
    .uncheck();
  await page.getByRole("button", { name: "Enregistrer ma direction" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Direction artistique enregistrée",
  );
});

test("text edit targets only one image and preserves current version", async ({
  page,
}) => {
  await page
    .getByRole("button", { name: "Ouvrir Donquixote Doflamingo" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByRole("button", { name: "Ajouter du texte", exact: true })
    .click();
  await page.getByLabel("Texte exact").fill("DOFLAMINGO");
  const response = page.waitForResponse(
    (r) => r.url().includes("/correct") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Créer une nouvelle version" })
    .click();
  const job = await (await response).json();
  expect(job.slots).toEqual(["cover"]);
  expect(job.correction).toContain("DOFLAMINGO");
  await expect(page.getByText("Votre retouche prend forme.")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Télécharger le post", exact: true }),
  ).toBeVisible();
});
