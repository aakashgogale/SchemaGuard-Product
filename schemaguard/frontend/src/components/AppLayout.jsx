import Sidebar from './Sidebar';
import Footer from './Footer';

export default function AppLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 p-6 lg:p-10 pt-20 lg:pt-10">{children}</main>
        <Footer variant="minimal" />
      </div>
    </div>
  );
}
