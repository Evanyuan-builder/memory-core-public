"use client";

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

export function Toggle({ checked, onChange, label }: ToggleProps) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={
        "relative inline-flex h-6 w-11 items-center rounded-full transition " +
        (checked ? "bg-zinc-900" : "bg-zinc-300")
      }
    >
      <span
        className={
          "inline-block h-4 w-4 transform rounded-full bg-white transition " +
          (checked ? "translate-x-6" : "translate-x-1")
        }
      />
    </button>
  );
}
