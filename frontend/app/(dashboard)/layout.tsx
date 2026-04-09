import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="content-shell">
        <Topbar />
        <div className="content-scroll">{children}</div>
      </main>
    </div>
  );
}
