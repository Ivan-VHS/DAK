# Ivan-VHS ecosystem portal

A dependency-free, responsive static website introducing the public Ivan-VHS repositories:

- [DuckOS](https://github.com/Ivan-VHS/DuckOS) — operating-system foundation
- [Reaper](https://github.com/Ivan-VHS/Reaper) — systems language and developer workbench
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — processor-systems workstation
- [OPlague](https://github.com/Ivan-VHS/OPlague) — device, driver and gaming workbench
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — procedural audio workstation

## Local preview

Open \`index.html\` directly in a modern browser. The page has no build step, package manager, remote font, analytics script or runtime dependency.

## Languages

The interface supports English, Ukrainian, Russian and Simplified Chinese. The first visit follows the browser language; the selected language is stored locally in the browser when storage is available.

## GitHub Pages

The workflow at \`.github/workflows/portal-pages.yml\` publishes this directory to GitHub Pages when changes reach \`main\`.

Before the first deployment, open **DuckOS → Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**. The expected project-site URL is:

\`https://ivan-vhs.github.io/DuckOS/\`

## Vercel

The repository-root \`vercel.json\` sets \`portal\` as the static output directory. Import the DuckOS repository in Vercel and deploy from the repository root; no build command or framework is required.

## Content policy

The portal describes the repository state documented on their default branches. It distinguishes verified, partial and planned work and does not imply that every project already runs natively inside DuckOS. Repository documentation remains the source of truth.
