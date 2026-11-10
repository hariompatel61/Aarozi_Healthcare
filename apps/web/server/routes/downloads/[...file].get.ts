import { defineEventHandler, getRouterParam, createError, setHeader, sendStream } from 'h3'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { resolve, join } from 'node:path'

export default defineEventHandler(async (event) => {
  const fileName = getRouterParam(event, 'file')
  if (!fileName) {
    throw createError({ statusCode: 400, statusMessage: 'Filename required' })
  }

  // Prevent directory traversal
  const sanitized = fileName.replace(/(\.\.[\/\\])+/g, '').replace(/^[\/\\]+/, '')
  
  // Resolve against public downloads folder
  const candidatePaths = [
    resolve(process.cwd(), 'apps/web/public/downloads', sanitized),
    resolve(process.cwd(), 'public/downloads', sanitized),
    resolve(process.cwd(), '.output/public/downloads', sanitized),
  ]

  let resolvedPath = ''
  for (const p of candidatePaths) {
    if (existsSync(p) && statSync(p).isFile()) {
      resolvedPath = p
      break
    }
  }

  if (!resolvedPath) {
    throw createError({ statusCode: 404, statusMessage: `Release file "${sanitized}" not found` })
  }

  const stat = statSync(resolvedPath)
  const isExe = sanitized.endsWith('.exe')
  const isZip = sanitized.endsWith('.zip')
  const isBat = sanitized.endsWith('.bat')

  const contentType = isExe
    ? 'application/vnd.microsoft.portable-executable'
    : isZip
      ? 'application/zip'
      : isBat
        ? 'text/plain'
        : 'application/octet-stream'

  setHeader(event, 'Content-Type', contentType)
  setHeader(event, 'Content-Length', String(stat.size))
  setHeader(event, 'Content-Disposition', `attachment; filename="${sanitized}"`)
  setHeader(event, 'Cache-Control', 'public, max-age=3600')

  return sendStream(event, createReadStream(resolvedPath) as any)
})
