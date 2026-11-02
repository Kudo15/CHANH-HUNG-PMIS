/**
 * Formats FastAPI/Pydantic validation errors safely into displayable strings.
 * Never leaks untrusted submitted input values.
 * Unknown or malformed shapes return fallbackMessage.
 */

function formatSingleError(item: unknown): string | null {
  if (typeof item === 'string') {
    const trimmed = item.trim()
    return trimmed.length > 0 ? trimmed : null
  }

  if (typeof item !== 'object' || item === null) {
    return null
  }

  const record = item as Record<string, unknown>

  // Extract trusted message fields
  let msg: string | null = null
  if (typeof record.msg === 'string' && record.msg.trim().length > 0) {
    msg = record.msg.trim()
  } else if (typeof record.message === 'string' && record.message.trim().length > 0) {
    msg = record.message.trim()
  }

  // Extract trusted location fields
  let locStr: string | null = null
  if (Array.isArray(record.loc)) {
    const parts = record.loc
      .filter((p): p is string | number => typeof p === 'string' || typeof p === 'number')
      .map(String)
      .map((s) => s.trim())
      .filter(Boolean)

    if (parts.length > 0) {
      const filtered = parts.filter((p) => p !== 'body')
      locStr = (filtered.length > 0 ? filtered : parts).join('.')
    }
  } else if (typeof record.loc === 'string' && record.loc.trim().length > 0) {
    locStr = record.loc.trim()
  }

  // If both loc and msg
  if (locStr && msg) {
    return `${locStr}: ${msg}`
  }
  if (msg) {
    return msg
  }
  if (locStr) {
    return locStr
  }

  // If neither trusted msg nor loc is present, do not expose untrusted fields like input
  return null
}

export function formatApiError(detail: unknown, fallbackMessage: string): string {
  if (typeof detail === 'string') {
    const trimmed = detail.trim()
    return trimmed.length > 0 ? trimmed : fallbackMessage
  }

  if (typeof detail !== 'object' || detail === null) {
    return fallbackMessage
  }

  // If object has a nested `detail` property (e.g. whole error response passed)
  if ('detail' in detail && (detail as Record<string, unknown>).detail !== undefined) {
    return formatApiError((detail as Record<string, unknown>).detail, fallbackMessage)
  }

  if (Array.isArray(detail)) {
    if (detail.length === 0) {
      return fallbackMessage
    }
    const formattedItems = detail
      .map(formatSingleError)
      .filter((s): s is string => typeof s === 'string' && s.length > 0)

    if (formattedItems.length === 0) {
      return fallbackMessage
    }
    return formattedItems.join('; ')
  }

  const single = formatSingleError(detail)
  return single ?? fallbackMessage
}
