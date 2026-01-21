
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { LayoutDashboard, MessageSquare, Settings, FileText, PieChart } from 'lucide-react'

const navItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Chat Assistant', href: '/chat', icon: MessageSquare },
  { name: 'Analytics', href: '/analytics', icon: PieChart },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  return (
    <div className="w-64 border-r bg-card min-h-screen p-4 flex flex-col">
      <div className="mb-8 px-4">
        <h1 className="text-xl font-bold tracking-tight">RAG Assistant</h1>
        <p className="text-xs text-muted-foreground">Powered by llmware</p>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-4 py-2 text-sm font-medium rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </Link>
        ))}
      </nav>
    </div>
  )
}
