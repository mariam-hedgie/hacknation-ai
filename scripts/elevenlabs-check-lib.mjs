export async function checkElevenLabsCredential({ apiKey, fetchImpl = fetch }) {
  if (!apiKey || apiKey.startsWith("TODO_")) {
    return {
      ok: false,
      message:
        "ELEVENLABS_API_KEY is not configured. Add your key to the local .env file, then run npm run check:elevenlabs.",
    };
  }

  let response;
  try {
    response = await fetchImpl("https://api.elevenlabs.io/v1/user", {
      headers: { "xi-api-key": apiKey },
    });
  } catch {
    return {
      ok: false,
      message: "ElevenLabs credential check could not reach the service. Try again when network access is available.",
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      message: `ElevenLabs credential check failed: ${response.status} ${response.statusText}`,
    };
  }

  const user = await response.json();
  return {
    ok: true,
    message: `ElevenLabs credential check: OK (${user.subscription?.tier ?? "account verified"})`,
  };
}
