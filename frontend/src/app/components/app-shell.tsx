import type { ReactNode } from "react";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      <Sidebar />

      <div className="ml-[248px] min-h-screen">
        <Topbar />

        <main className="px-6 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}