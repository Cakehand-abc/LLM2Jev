import { cp, mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createMarkdownRenderer } from 'vitepress'

const site = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(site, '..')
const content = path.join(site, 'content')
const repo = 'https://github.com/Yinsongxu/LLM2Jev/blob/main/'
const base = '/LLM2Jev/'
const documents = new Map()

async function collect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const filename = path.join(directory, entry.name)
    if (entry.isDirectory()) await collect(filename)
    else if (entry.name.endsWith('.md')) {
      const relative = path.relative(path.join(root, 'docs'), filename)
      documents.set(filename, relative.startsWith('en/') ? relative.slice(3) : relative)
    }
  }
}

function rewriteLinks(markdown, source, output) {
  return markdown.replace(/\]\(([^)]+)\)/g, (match, href) => {
    if (/^(?:[a-z]+:|\/\/)/i.test(href)) return match
    if (href.startsWith('#')) return source.endsWith('README.md') || source.endsWith('README_zh.md')
      ? `](index.md${href})` : match
    const [filename, hash] = href.split('#')
    const resolved = path.resolve(path.dirname(source), filename)
    let target = documents.get(resolved)
    if (resolved === path.join(root, 'README.md')) target = 'index.md'
    if (resolved === path.join(root, 'README_zh.md')) target = 'zh/index.md'
    if (target) {
      const relative = path.posix.relative(path.posix.dirname(output), target)
      return `](${relative}${hash ? `#${hash}` : ''})`
    }
    const relative = path.relative(root, resolved)
    if (relative.startsWith('assets/')) return `](/${relative})`
    return `](${repo}${relative}${hash ? `#${hash}` : ''})`
  })
}

await rm(content, { recursive: true, force: true })
await mkdir(content, { recursive: true })
await collect(path.join(root, 'docs'))
for (const [source, output] of documents) {
  const target = path.join(content, output)
  await mkdir(path.dirname(target), { recursive: true })
  let markdown = await readFile(source, 'utf8')
  // Language switching and homepage navigation are provided by the site header.
  markdown = markdown.replace(/^\[(?:简体中文|English)\].*\n/m, '')
  await writeFile(target, rewriteLinks(markdown, source, output))
}
await cp(path.join(site, 'pages'), content, { recursive: true })
await cp(path.join(root, 'assets'), path.join(content, 'public/assets'), { recursive: true })
await cp(path.join(site, 'public'), path.join(content, 'public'), { recursive: true })

const renderer = await createMarkdownRenderer(base)
const news = {}
for (const lang of ['en', 'zh']) {
  const source = path.join(root, lang === 'en' ? 'README.md' : 'README_zh.md')
  const readme = await readFile(source, 'utf8')
  const section = readme.match(/## 📰 [^\n]+\n([\s\S]*?)(?=\n## )/)?.[1]
  if (!section) throw new Error(`Missing News section: ${source}`)
  const output = lang === 'en' ? 'news.md' : 'zh/news.md'
  const markdown = rewriteLinks(section.trim(), source, output)
  const heading = lang === 'en' ? '# News\n\nProject updates, releases, and experiments.' : '# 最新动态\n\n项目进展、版本更新与实验记录。'
  await writeFile(path.join(content, output), `${heading}\n\n${markdown}\n`)
  news[lang] = section.trim().split('\n').filter(line => line.startsWith('- ')).map(line => {
    const match = line.match(/^- \*\*(.+?)\*\* - (.*)$/)
    if (!match) throw new Error(`Unexpected News entry: ${line}`)
    const markup = rewriteLinks(match[2], source, lang === 'en' ? 'index.md' : 'zh/index.md')
    const html = renderer.renderInline(markup).replace(/href="([^"#]+\.md)(#[^"]*)?"/g, (link, href, hash = '') => {
      if (href.startsWith('https://')) return link
      return `href="${base}${lang === 'zh' ? 'zh/' : ''}${href === 'index.md' ? '' : href.slice(0, -3)}${hash}"`
    })
    return { date: match[1], html }
  })
}
await writeFile(path.join(site, '.vitepress/theme/news.json'), JSON.stringify(news))
console.log(`Prepared ${documents.size} documents, bilingual homepages, and News from README.`)
