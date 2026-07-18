const apiKey = process.env.ELEVENLABS_API_KEY;

if (!apiKey || apiKey.startsWith("TODO_")) {
  console.error(
    "ELEVENLABS_API_KEY is not configured. Add your key to the local .env file, then run npm run check:elevenlabs."
  );
  process.exit(1);
}

const response = await fetch("https://api.elevenlabs.io/v1/user", {
  headers: { "xi-api-key": apiKey },
});

if (!response.ok) {
  console.error(`ElevenLabs credential check failed: ${response.status} ${response.statusText}`);
  process.exit(1);
}

const user = await response.json();
console.log(`ElevenLabs credential check: OK (${user.subscription?.tier ?? "account verified"})`);
