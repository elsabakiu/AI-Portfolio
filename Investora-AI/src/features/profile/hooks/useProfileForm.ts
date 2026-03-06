import { useMemo, useState } from "react";

export function useProfileForm(initialRisk: "low" | "medium" | "high", initialInterests: string[]) {
  const [risk, setRisk] = useState<"low" | "medium" | "high">(initialRisk);
  const [interests, setInterests] = useState<string[]>(initialInterests);

  const isValid = useMemo(() => interests.length > 0, [interests]);

  const toggleInterest = (interest: string) => {
    setInterests((prev) =>
      prev.includes(interest) ? prev.filter((x) => x !== interest) : [...prev, interest]
    );
  };

  return {
    risk,
    setRisk,
    interests,
    setInterests,
    toggleInterest,
    isValid,
  };
}
