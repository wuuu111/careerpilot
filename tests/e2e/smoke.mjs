import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import process from "node:process";
import { spawn, spawnSync } from "node:child_process";

import { chromium } from "playwright";
import { resolveWorkspaceRoot } from "./paths.mjs";

const workspaceRoot = resolveWorkspaceRoot(import.meta.url);
const apiPort = 8012;
const webPort = 4177;
const apiBaseUrl = `http://127.0.0.1:${apiPort}`;
const webBaseUrl = `http://127.0.0.1:${webPort}`;

function toSqliteUrl(filePath) {
  return `sqlite:////${filePath.replace(/^\/+/, "")}`;
}

function runOrThrow(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: workspaceRoot,
    stdio: "pipe",
    encoding: "utf8",
    ...options,
  });

  if (result.status !== 0) {
    throw new Error(
      [`Command failed: ${command} ${args.join(" ")}`, result.stdout, result.stderr]
        .filter(Boolean)
        .join("\n"),
    );
  }
}

function startProcess(command, args, env) {
  const child = spawn(command, args, {
    cwd: workspaceRoot,
    env: { ...process.env, ...env },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  return {
    child,
    getLogs() {
      return { stdout, stderr };
    },
  };
}

async function waitForUrl(url, label) {
  const started = Date.now();
  while (Date.now() - started < 20000) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Timed out waiting for ${label} at ${url}`);
}

async function main() {
  const tempDir = await mkdtemp(path.join(tmpdir(), "careerpilot-e2e-"));
  const dbPath = path.join(tempDir, "smoke.db");
  const resumePath = path.join(tempDir, "resume.pdf");
  const screenshotPath = path.join(tempDir, "failure.png");
  const databaseUrl = toSqliteUrl(dbPath);

  const sharedEnv = {
    CAREERPILOT_DATABASE_URL: databaseUrl,
    CAREERPILOT_JWT_SECRET: "e2e-secret-with-at-least-32-bytes",
    CAREERPILOT_CELERY_TASK_ALWAYS_EAGER: "true",
  };

  const apiServer = startProcess(
    "uv",
    ["run", "uvicorn", "careerpilot.api.main:app", "--host", "127.0.0.1", "--port", String(apiPort)],
    sharedEnv,
  );
  const webServer = startProcess(
    "npm",
    ["--workspace", "apps/web", "run", "dev", "--", "--host", "127.0.0.1", "--port", String(webPort)],
    { VITE_API_BASE_URL: apiBaseUrl },
  );

  let succeeded = false;

  try {
    runOrThrow("uv", ["run", "alembic", "upgrade", "head"], {
      env: { ...process.env, ...sharedEnv },
    });

    runOrThrow(
      "uv",
      [
        "run",
        "python",
        "-c",
        [
          "import fitz",
          `doc = fitz.open()`,
          "page = doc.new_page()",
          "page.insert_text((72, 72), 'Test Candidate\\nPython FastAPI React\\nProject Alpha\\nIntern experience at Agent Lab')",
          `doc.save(r'${resumePath}')`,
        ].join("; "),
      ],
      { env: { ...process.env, ...sharedEnv } },
    );

    await waitForUrl(`${apiBaseUrl}/health`, "api");
    await waitForUrl(`${webBaseUrl}/register`, "web");

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
      const email = `user${Date.now()}@example.com`;

      await page.goto(`${webBaseUrl}/register`, { waitUntil: "networkidle" });
      await page.getByLabel("Name").fill("Test User");
      await page.getByLabel("Email").fill(email);
      await page.getByLabel("Password").fill("supersecret123");
      await page.getByRole("button", { name: /register/i }).click();
      await page.waitForURL(`${webBaseUrl}/`);

      await page.goto(`${webBaseUrl}/resumes`, { waitUntil: "networkidle" });
      await page.locator('input[type="file"]').setInputFiles(resumePath);
      await page.getByRole("button", { name: /^upload$/i }).click();
      await page.getByText("Test Candidate").waitFor({ timeout: 10000 });

      await page.goto(`${webBaseUrl}/job-analysis`, { waitUntil: "networkidle" });
      await page.getByRole("textbox", { name: "Company", exact: true }).fill("OpenAI");
      await page.getByRole("textbox", { name: "Role", exact: true }).fill("AI Engineer");
      await page
        .getByRole("textbox", { name: "Job description", exact: true })
        .fill(
          "Build AI agents with Python, FastAPI, React, evaluation workflows, and production debugging.",
        );
      await page
        .getByRole("textbox", { name: "Company context", exact: true })
        .fill("OpenAI builds APIs, safety systems, evaluations, and production AI infrastructure.");
      await page.getByRole("button", { name: /save target role/i }).click();
      await page.getByRole("button", { name: /run matching/i }).waitFor({ timeout: 10000 });

      await page.goto(`${webBaseUrl}/matching`, { waitUntil: "networkidle" });
      await page.getByRole("button", { name: /^run workflow$/i }).click();
      await page.getByText("Recommendations").waitFor({ timeout: 15000 });

      await page.goto(`${webBaseUrl}/generated`, { waitUntil: "networkidle" });
      await page.getByText("Company knowledge").waitFor({ timeout: 10000 });
      await page.getByText("Retrieval citations").waitFor({ timeout: 10000 });
      await page.getByRole("button", { name: "evaluation" }).click();
      await page.getByText("Hallucination risk").waitFor({ timeout: 10000 });
      await page.getByRole("button", { name: "cover_letter" }).click();
      await page.getByRole("button", { name: /generate cover letter/i }).click();
      await page.getByText("Version history").waitFor({ timeout: 10000 });

      await page.goto(`${webBaseUrl}/trace`, { waitUntil: "networkidle" });
      await page.getByText("ResumeParserAgent").waitFor({ timeout: 10000 });
      await page.getByText("EvaluationAgent").waitFor({ timeout: 10000 });
      succeeded = true;
    } catch (error) {
      await page.screenshot({ path: screenshotPath, fullPage: true });
      throw new Error(`${error instanceof Error ? error.message : String(error)}\nScreenshot: ${screenshotPath}`);
    } finally {
      await browser.close();
    }
  } finally {
    apiServer.child.kill("SIGTERM");
    webServer.child.kill("SIGTERM");
    if (succeeded) {
      await rm(tempDir, { recursive: true, force: true });
    } else {
      console.error(`Artifacts kept at ${tempDir}`);
    }
    const apiLogs = apiServer.getLogs();
    const webLogs = webServer.getLogs();
    if (process.env.CI_DEBUG_LOGS === "1") {
      console.log("=== API STDOUT ===\n", apiLogs.stdout);
      console.log("=== API STDERR ===\n", apiLogs.stderr);
      console.log("=== WEB STDOUT ===\n", webLogs.stdout);
      console.log("=== WEB STDERR ===\n", webLogs.stderr);
    }
  }
}

await main();
