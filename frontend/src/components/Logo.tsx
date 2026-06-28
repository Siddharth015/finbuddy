// FinBuddy brand mark: a friendly coin-with-a-smile inside a gradient tile.
export function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="fb-grad" x1="0" y1="0" x2="40" y2="40">
          <stop offset="0" stopColor="#34d399" />
          <stop offset="1" stopColor="#0ea5a4" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" fill="url(#fb-grad)" />
      <circle
        cx="20"
        cy="20"
        r="11"
        fill="none"
        stroke="#fff"
        strokeWidth="2.4"
        opacity="0.96"
      />
      <circle cx="16" cy="18" r="1.7" fill="#fff" />
      <circle cx="24" cy="18" r="1.7" fill="#fff" />
      <path
        d="M15 23.4c1.7 2.3 7.6 2.3 10 0"
        stroke="#fff"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
}
