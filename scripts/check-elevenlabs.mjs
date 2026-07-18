import { checkElevenLabsCredential } from "./elevenlabs-check-lib.mjs";

const result = await checkElevenLabsCredential({
  apiKey: process.env.ELEVENLABS_API_KEY,
});

if (result.ok) {
  console.log(result.message);
} else {
  console.error(result.message);
  process.exitCode = 1;
}
