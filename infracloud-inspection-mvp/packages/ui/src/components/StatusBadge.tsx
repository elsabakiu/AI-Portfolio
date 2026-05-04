import type { ReactNode } from "react";

const toneMap: Record<string, string> = {
  ready: "badge badge-primary",
  attention: "badge badge-warning",
  success: "badge badge-success",
  neutral: "badge",
  warning: "badge badge-warning",
  primary: "badge badge-primary",
};

interface StatusBadgeProps {
  children: ReactNode;
  tone?: string;
}

export function StatusBadge({ children, tone = "neutral" }: StatusBadgeProps) {
  return <span className={toneMap[tone] || toneMap.neutral}>{children}</span>;
}
