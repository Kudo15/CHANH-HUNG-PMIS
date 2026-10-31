export function isTaskOverdue(
  dueDate?: string | null,
  status?: string,
  asOf?: Date
): boolean {
  if (!dueDate) return false
  if (status === 'done' || status === 'cancelled') return false
  const now = asOf ? asOf.getTime() : Date.now()
  const due = new Date(dueDate).getTime()
  return due < now
}
