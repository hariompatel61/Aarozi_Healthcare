const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 3456;
const HOST = '127.0.0.1';
const BASE_URL = `http://${HOST}:${PORT}`;

const targets = [
  { url: `${BASE_URL}/reporting/release?auth=demo_token`, name: 'release-1366x768.png', width: 1366, height: 768 },
  { url: `${BASE_URL}/reporting/release?auth=demo_token`, name: 'release-390x844.png', width: 390, height: 844 },
];

const outDir = path.resolve(__dirname, '../docs/ux/after');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function waitServerReady(url, maxRetries = 20) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = await new Promise((resolve, reject) => {
        const req = http.get(url, (response) => {
          resolve(response.statusCode);
        });
        req.on('error', reject);
        req.setTimeout(2000, () => {
          req.destroy();
          reject(new Error('timeout'));
        });
      });
      console.log(`Probe to ${url} returned HTTP ${res}`);
      return true;
    } catch (e) {
      console.log(`Wait attempt ${i + 1}/${maxRetries}: ${e.message}`);
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  throw new Error(`Server did not respond at ${url}`);
}

function capture(chromePath, url, outPath, width, height) {
  return new Promise((resolve, reject) => {
    const args = [
      '--headless=new',
      '--disable-gpu',
      '--no-sandbox',
      `--window-size=${width},${height}`,
      `--screenshot=${outPath}`,
      '--virtual-time-budget=4000',
      url
    ];
    const proc = spawn(chromePath, args);
    proc.on('close', (code) => {
      if (code === 0 && fs.existsSync(outPath)) {
        console.log(`[OK] Captured ${path.basename(outPath)} (${width}x${height})`);
        resolve();
      } else {
        reject(new Error(`Failed capturing ${outPath}, exit code ${code}`));
      }
    });
  });
}

async function run() {
  console.log(`Starting Nitro server on ${HOST}:${PORT}...`);
  const serverPath = path.resolve(__dirname, '../apps/web/.output/server/index.mjs');
  const server = spawn('node', [serverPath], {
    env: { ...process.env, HOST, NITRO_HOST: HOST, PORT: String(PORT), NITRO_PORT: String(PORT), NODE_ENV: 'production' },
    stdio: 'inherit'
  });

  try {
    console.log('Waiting for server...');
    await waitServerReady(`${BASE_URL}/`);
    console.log('Server is ready! Capturing screenshots...');

    for (const t of targets) {
      const outPath = path.join(outDir, t.name);
      await capture(CHROME_PATH, t.url, outPath, t.width, t.height);
    }
    console.log('All screenshots captured successfully!');
  } finally {
    console.log('Shutting down server...');
    server.kill();
  }
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
