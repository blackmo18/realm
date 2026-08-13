#!/usr/bin/env node
/**
 * teams-webhook-server.js — lightweight MCP server for Microsoft Teams webhooks.
 * Posts MessageCard notifications to organization Teams channel.
 *
 * Usage (Cursor MCP):
 *   node mcp/teams/teams-webhook-server.js
 *   env: REALM_TEAMS_WEBHOOK=<incoming-webhook-url>
 */

const WEBHOOK = process.env.REALM_TEAMS_WEBHOOK;

async function postToTeams({ title, text, themeColor = "0076D7", facts = [] }) {
  if (!WEBHOOK) {
    throw new Error("REALM_TEAMS_WEBHOOK not set");
  }

  const body = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    themeColor,
    summary: title,
    sections: [
      {
        activityTitle: title,
        facts: facts.map(({ name, value }) => ({ name, value })),
        text: text || "",
      },
    ],
  };

  const res = await fetch(WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Teams webhook failed (${res.status}): ${err}`);
  }
  return { ok: true, status: res.status };
}

// Minimal stdio MCP protocol — post_message tool
const TOOLS = {
  post_message: {
    description: "Post a message to Microsoft Teams via incoming webhook",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        text: { type: "string" },
        themeColor: { type: "string" },
        facts: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              value: { type: "string" },
            },
          },
        },
      },
      required: ["title"],
    },
  },
};

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

process.stdin.on("data", async (chunk) => {
  let req;
  try {
    req = JSON.parse(chunk.toString());
  } catch {
    return;
  }

  if (req.method === "initialize") {
    send({
      jsonrpc: "2.0",
      id: req.id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "realm-teams-webhook", version: "1.0.0" },
      },
    });
    return;
  }

  if (req.method === "tools/list") {
    send({
      jsonrpc: "2.0",
      id: req.id,
      result: {
        tools: Object.entries(TOOLS).map(([name, t]) => ({
          name,
          description: t.description,
          inputSchema: t.inputSchema,
        })),
      },
    });
    return;
  }

  if (req.method === "tools/call" && req.params?.name === "post_message") {
    try {
      const result = await postToTeams(req.params.arguments || {});
      send({
        jsonrpc: "2.0",
        id: req.id,
        result: {
          content: [{ type: "text", text: JSON.stringify(result) }],
        },
      });
    } catch (e) {
      send({
        jsonrpc: "2.0",
        id: req.id,
        error: { code: -32000, message: e.message },
      });
    }
    return;
  }
});

process.stderr.write("realm-teams-webhook MCP server ready\n");
