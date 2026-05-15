"use client";

import { LanguageSelector } from "@/components/LanguageSelector";

export default function SettingsPage() {
  return (
    <main className="max-w-xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-6">Settings</h1>

      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Language</div>
            <div className="text-xs text-zinc-500">Choose the app language.</div>
          </div>
          <LanguageSelector />
        </div>
      </section>
    </main>
  );
}
