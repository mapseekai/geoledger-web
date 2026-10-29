// Run with ego-browser only. This tests the static site, not the GeoLedger database.
// ./scripts/browser-check.sh (optionally GL_WEB_TASK_SPACE=29 to reuse an owned task space)
const fs = await import("node:fs/promises");
const path = await import("node:path");
const config = globalThis.GEOLEDGER_WEB_TEST ?? {};
const root = config.root;
if (!root || !path.isAbsolute(root))
  throw new Error("Run this test through scripts/browser-check.sh");
const base = config.base ?? "http://localhost:1313";
const existing = config.spaceId;
const task = await taskSpace(
  existing ? Number(existing) : "GeoLedger Web smoke test",
);
const page = task.page("p1");
const report = {
  base,
  testedAt: new Date().toISOString(),
  pages: [],
  diagrams: [],
  failures: [],
};
const output = path.join(root, "artifacts");
await fs.mkdir(output, { recursive: true });
const monitor = await page.cdp("Page.addScriptToEvaluateOnNewDocument", {
  source:
    "window.__glTestErrors=[];addEventListener('error',e=>window.__glTestErrors.push(String(e.message||'resource error')));addEventListener('unhandledrejection',e=>window.__glTestErrors.push(String(e.reason)));",
});
try {
  for (const width of [320, 390, 768, 1440]) {
    await page.cdp("Emulation.setDeviceMetricsOverride", {
      width,
      height: width < 768 ? 844 : 1000,
      deviceScaleFactor: 1,
      mobile: width < 768,
    });
    for (const route of [
      "/",
      "/docs/",
      "/docs/start/quickstart/",
      "/docs/reference/sdk/",
      "/blog/",
      "/tags/main/",
      "/tags/engineering/",
    ]) {
      await page.goto(base + route);
      await page.evaluate(() =>
        document.fonts.ready.then(
          () =>
            new Promise((resolve) =>
              requestAnimationFrame(() => requestAnimationFrame(resolve)),
            ),
        ),
      );
      if (route.startsWith("/tags/"))
        await page.evaluate(() =>
          document.querySelector(".gl-footer-brand")?.scrollIntoView({ block: "center" }),
        );
      const result = await page.evaluate(() => {
        const brand = document.querySelector(".gl-footer-brand");
        const rect = brand?.getBoundingClientRect();
        const hit = rect && document.elementFromPoint(
          rect.x + rect.width / 2, rect.y + rect.height / 2,
        );
        return {
          path: location.pathname,
          width: innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          h1: document.querySelector("h1")?.textContent,
          footerBrandVisible: location.pathname.startsWith("/tags/")
            ? !!hit && brand.contains(hit) : undefined,
          errors: window.__glTestErrors ?? [],
          httpErrors: performance
            .getEntriesByType("resource")
            .filter((r) => r.responseStatus >= 400)
            .map((r) => ({ url: r.name, status: r.responseStatus })),
        };
      });
      report.pages.push(result);
      if (
        result.path !== route ||
        !result.h1 ||
        result.scrollWidth > result.width ||
        result.footerBrandVisible === false ||
        result.errors.length ||
        result.httpErrors.length
      )
        report.failures.push(result);
      if (route === "/" && [390, 1440].includes(width))
        await page.screenshot({ path: path.join(output, `home-${width}.png`) });
      if (route === "/blog/" && width === 1440)
        await page.screenshot({ path: path.join(output, "blog-desktop.png") });
    }
  }
  for (const slug of ["version-model", "merge", "storage", "transactions"]) {
    await page.goto(`${base}/docs/architecture/${slug}/`);
    await page.evaluate(() =>
      document
        .querySelector("[data-td-diagram-stage]")
        ?.scrollIntoView({ block: "center" }),
    );
    await page.waitForFunction(
      () => document.querySelector("[data-td-diagram-stage] svg"),
      undefined,
      { timeout: 15000 },
    );
    const result = await page.evaluate(() => ({
      path: location.pathname,
      count: document.querySelectorAll("[data-td-diagram-stage] svg").length,
      errors: window.__glTestErrors ?? [],
    }));
    report.diagrams.push(result);
    if (!result.count || result.errors.length) report.failures.push(result);
  }
  await fs.writeFile(
    path.join(output, "browser-check.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(
    JSON.stringify(
      {
        pages: report.pages.length,
        widths: [...new Set(report.pages.map((p) => p.width))],
        diagrams: report.diagrams.length,
        failures: report.failures,
      },
      null,
      2,
    ),
  );
  if (report.failures.length)
    throw new Error(`${report.failures.length} browser checks failed`);
} finally {
  if (monitor.identifier)
    await page.cdp("Page.removeScriptToEvaluateOnNewDocument", {
      identifier: monitor.identifier,
    });
  if (!existing) await task.finish({ keep: [] });
}
