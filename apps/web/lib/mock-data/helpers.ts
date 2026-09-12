/** Fixture timestamps are generated relative to load time so the demo always feels live. */
export const minutesAgo = (m: number) => new Date(Date.now() - m * 60_000).toISOString();
export const daysAgo = (d: number) => minutesAgo(d * 24 * 60);