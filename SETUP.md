# Setup

The site is plain static HTML. The only moving part is the photo uploader.

## Photo uploader

Live at **/admin** (hidden from search engines, not linked from the site).

It needs two environment variables in Vercel:
**Project → Settings → Environment Variables**, scope Production.

| Name | Value |
|---|---|
| `ADMIN_PASSWORD` | Any password you pick. This is what /admin asks for. |
| `GITHUB_TOKEN` | A GitHub fine-grained personal access token. |

### Making the GitHub token

1. github.com → Settings → Developer settings → **Personal access tokens → Fine-grained tokens** → Generate new token
2. Repository access: **Only select repositories** → `ianwright547/junk-removal`
3. Permissions → Repository permissions → **Contents: Read and write**
4. Generate, copy the token, paste it into Vercel as `GITHUB_TOKEN`
5. Redeploy so the new variables take effect

Optional overrides: `GITHUB_REPO` (default `ianwright547/junk-removal`) and
`GITHUB_BRANCH` (default `main`).

### How it works

Uploading commits the photo to `img/job-N.jpg` on `main`. Vercel sees the
commit and redeploys, so the photo appears on the site roughly a minute later.
Photos are resized to 1600px wide and converted to JPG in the browser first,
so phone camera files are fine.

HEIC does not work. Set iPhone Settings → Camera → Formats → **Most Compatible**.

### Security

The password is checked server-side and never stored in the page. The GitHub
token stays in the serverless function and is never sent to the browser.
There is no rate limiting, so use a password that is not guessable.
