interface LogoProps {
  className?: string;
}

export function Logo({ className = 'w-5 h-5' }: LogoProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path d="M 51,48 C 65,48 85,38 88,18 C 72,16 55,30 51,48 Z" fill="#4B8C24"/>
      <path d="M 51.5,47 Q 70,32 88,18" stroke="#D0E35B" strokeWidth="1.5" strokeLinecap="round" fill="none"/>

      <path d="M 49,48 C 37.1,48 20.1,39.5 17.6,22.5 C 31.2,20.8 45.6,32.7 49,48 Z" fill="#60A82A"/>
      <path d="M 48.6,47.2 Q 32.9,34.4 17.6,22.5" stroke="#D0E35B" strokeWidth="1.5" strokeLinecap="round" fill="none"/>

      <rect x="47" y="46" width="6" height="46" fill="#151515" rx="1"/>

      <path d="M 31,64 C 28,60 23,61 20,66 C 23,71 28,70 32,68 Z" fill="#151515"/>

      <path d="M 30,64 C 38,52 48,51 55,54 C 65,58 65,70 54,76 C 42,80 40,86 50,88 C 56,90 53,96 47,98 C 51,94 52,90 49,83 C 46,81 46,76 53,71 C 60,67 60,60 54,58 C 48,56 40,57 32,68 Z" fill="#151515"/>
    </svg>
  );
}
