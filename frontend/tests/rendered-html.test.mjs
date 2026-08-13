import assert from "node:assert/strict";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }), {
    ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) },
  }, { waitUntil() {}, passThroughOnException() {} });
}

test("renders the Gatherly application shell", async () => {
  const response = await render();
  const html = await response.text();
  assert.equal(response.status, 200);
  assert.match(html, /<title>Gatherly/);
  assert.match(html, /Turn any event screenshot into a plan/);
  assert.match(html, /Sign in/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Starter Project/);
});

test("does not leave signed-out event visitors in a loading state", async () => {
  const response = await render("/events/00000000-0000-4000-8000-000000000000");
  const html = await response.text();
  assert.equal(response.status, 200);
  assert.match(html, /Sign in to see this event/);
  assert.doesNotMatch(html, /Loading the plan/);
});
