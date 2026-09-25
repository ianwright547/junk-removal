// Serverless function: writes job photos into img/ by committing to GitHub.
// Vercel redeploys on the commit, so the photo is live ~1 min after upload.
//
// Required env vars (set in Vercel > Project > Settings > Environment Variables):
//   ADMIN_PASSWORD  - the password the /admin page asks for
//   GITHUB_TOKEN    - a fine-grained PAT with Contents: Read and write on this repo
// Optional:
//   GITHUB_REPO     - "owner/repo", defaults to ianwright547/junk-removal
//   GITHUB_BRANCH   - defaults to main

const REPO = process.env.GITHUB_REPO || 'ianwright547/junk-removal';
const BRANCH = process.env.GITHUB_BRANCH || 'main';
const MAX_SLOT = 12;
const MAX_BYTES = 4 * 1024 * 1024;

function gh(path, init) {
  return fetch('https://api.github.com/repos/' + REPO + '/contents/' + path, {
    ...init,
    headers: {
      Authorization: 'Bearer ' + process.env.GITHUB_TOKEN,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
      ...(init && init.headers),
    },
  });
}

// Constant-time-ish compare so the password can't be guessed by timing.
function sameSecret(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Use POST.' });
  }
  if (!process.env.ADMIN_PASSWORD || !process.env.GITHUB_TOKEN) {
    return res.status(500).json({
      error: 'Server not configured. ADMIN_PASSWORD and GITHUB_TOKEN must be set in Vercel.',
    });
  }

  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body || {};
  const { password, slot, image, action } = body;

  if (!sameSecret(String(password || ''), process.env.ADMIN_PASSWORD)) {
    return res.status(401).json({ error: 'Wrong password.' });
  }

  const n = Number(slot);
  if (!Number.isInteger(n) || n < 1 || n > MAX_SLOT) {
    return res.status(400).json({ error: 'Slot must be a whole number from 1 to ' + MAX_SLOT + '.' });
  }
  const path = 'img/job-' + n + '.jpg';

  // Look up the current file so we can overwrite (GitHub needs the blob sha) or delete it.
  let sha;
  try {
    const cur = await gh(path + '?ref=' + encodeURIComponent(BRANCH));
    if (cur.ok) sha = (await cur.json()).sha;
    else if (cur.status !== 404) {
      return res.status(502).json({ error: 'GitHub read failed (' + cur.status + ').' });
    }
  } catch {
    return res.status(502).json({ error: 'Could not reach GitHub.' });
  }

  if (action === 'delete') {
    if (!sha) return res.status(404).json({ error: 'Slot ' + n + ' is already empty.' });
    const del = await gh(path, {
      method: 'DELETE',
      body: JSON.stringify({ message: 'Remove job photo ' + n, sha, branch: BRANCH }),
    });
    if (!del.ok) return res.status(502).json({ error: 'Delete failed (' + del.status + ').' });
    return res.status(200).json({ ok: true, slot: n, deleted: true });
  }

  const base64 = String(image || '').replace(/^data:image\/\w+;base64,/, '');
  if (!base64) return res.status(400).json({ error: 'No image data received.' });
  if (!/^[A-Za-z0-9+/]+={0,2}$/.test(base64)) {
    return res.status(400).json({ error: 'Image data is not valid base64.' });
  }
  if (Buffer.from(base64, 'base64').length > MAX_BYTES) {
    return res.status(413).json({ error: 'Photo is over 4 MB even after resizing. Try a smaller one.' });
  }

  const put = await gh(path, {
    method: 'PUT',
    body: JSON.stringify({
      message: (sha ? 'Replace' : 'Add') + ' job photo ' + n,
      content: base64,
      branch: BRANCH,
      ...(sha ? { sha } : {}),
    }),
  });
  if (!put.ok) {
    const detail = await put.text();
    return res.status(502).json({ error: 'Upload failed (' + put.status + '). ' + detail.slice(0, 200) });
  }
  return res.status(200).json({ ok: true, slot: n, path });
};
