import test from "node:test";
import assert from "node:assert/strict";

import { checkElevenLabsCredential } from "./elevenlabs-check-lib.mjs";


test("fails closed when no credential is configured", async () => {
  const result = await checkElevenLabsCredential({ apiKey: "TODO_KEY" });
  assert.equal(result.ok, false);
  assert.match(result.message, /not configured/i);
});

test("does not expose a credential when the network fails", async () => {
  const secret = "private_voice_secret";
  const result = await checkElevenLabsCredential({
    apiKey: secret,
    fetchImpl: async () => {
      throw new Error(`network failed with ${secret}`);
    },
  });
  assert.equal(result.ok, false);
  assert.match(result.message, /could not reach/i);
  assert.doesNotMatch(result.message, new RegExp(secret));
});

test("reports an HTTP rejection without sending the secret to output", async () => {
  const secret = "private_voice_secret";
  const result = await checkElevenLabsCredential({
    apiKey: secret,
    fetchImpl: async (_url, options) => {
      assert.equal(options.headers["xi-api-key"], secret);
      return { ok: false, status: 401, statusText: "Unauthorized" };
    },
  });
  assert.equal(result.ok, false);
  assert.equal(result.message, "ElevenLabs credential check failed: 401 Unauthorized");
  assert.doesNotMatch(result.message, new RegExp(secret));
});

test("reports only the subscription tier after success", async () => {
  const result = await checkElevenLabsCredential({
    apiKey: "private_voice_secret",
    fetchImpl: async () => ({
      ok: true,
      json: async () => ({ subscription: { tier: "creator" } }),
    }),
  });
  assert.deepEqual(result, {
    ok: true,
    message: "ElevenLabs credential check: OK (creator)",
  });
});
