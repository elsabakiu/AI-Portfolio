import { fetchWithRetry } from "../lib/upstream.js";

function parseJsonOrRaw(text) {
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    return { raw: text };
  }
}

export async function runWorkflow({
  config,
  file,
  suspicionId,
  existingRecord,
}) {
  const requestBody = {
    suspicion_id: String(suspicionId),
    existing_record: existingRecord,
    audio: {
      filename: file.originalname || "inspection-audio.wav",
      content_type: file.mimetype || "audio/wav",
      base64: file.buffer.toString("base64"),
    },
  };

  const response = await fetchWithRetry(
    `${config.langgraphServiceUrl}/v1/extractions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    },
    config
  );

  const text = await response.text();
  const payload = parseJsonOrRaw(text);

  if (payload?.ok === true && payload.data) {
    return {
      provider: "langgraph",
      response,
      payload: payload.data,
    };
  }

  return {
    provider: "langgraph",
    response,
    payload,
  };
}
