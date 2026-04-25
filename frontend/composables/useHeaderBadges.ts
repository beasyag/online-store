export const useHeaderBadges = () => {
  const badges = useState<Record<string, number>>("header-badges", () => ({
    "/cart": 0,
    "/chat": 0,
    "/account": 0,
    "/seller": 0
  }));

  const setBadge = (key: string, value: number) => {
    badges.value[key] = Math.max(0, Number(value || 0));
  };

  const getBadge = (key: string) => badges.value[key] || 0;

  return {
    badges,
    setBadge,
    getBadge
  };
};
