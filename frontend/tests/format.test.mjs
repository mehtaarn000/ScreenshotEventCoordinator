import assert from "node:assert/strict";
import test from "node:test";
import { dateTimeLocalValue, zonedLocalToIso } from "../app/lib/format.ts";

test("converts event wall time using its IANA timezone", () => {
  assert.equal(
    zonedLocalToIso("2026-07-15T18:30", "America/New_York"),
    "2026-07-15T22:30:00.000Z",
  );
  assert.equal(
    zonedLocalToIso("2026-01-15T18:30", "America/New_York"),
    "2026-01-15T23:30:00.000Z",
  );
});

test("formats a timestamp for the event timezone", () => {
  assert.equal(
    dateTimeLocalValue("2026-07-15T22:30:00.000Z", "America/New_York"),
    "2026-07-15T18:30",
  );
});
