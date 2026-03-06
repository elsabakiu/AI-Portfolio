export const queryKeys = {
  latestReport: ["latest-report"] as const,
  runHistory: ["run-history"] as const,
  dashboard: (userId: string | undefined) => ["dashboard", userId] as const,
  personalizedSignals: (userId: string | undefined) => ["personalized-signals", userId] as const,
  alerts: (userId: string | undefined) => ["alerts", userId] as const,
};

export const dashboardInvalidationKeys = [
  queryKeys.latestReport,
  queryKeys.runHistory,
] as const;
