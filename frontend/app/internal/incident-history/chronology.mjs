export function chronology(statusHistory, assignmentHistory) {
  return [
    ...statusHistory.map(item => ({ ...item, kind: 'status', at: item.changed_at })),
    ...assignmentHistory.map(item => ({ ...item, kind: 'assignment', at: item.changed_at })),
  ].sort((a, b) => new Date(a.at) - new Date(b.at));
}
