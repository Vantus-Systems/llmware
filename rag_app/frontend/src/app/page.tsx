
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ArrowRight, Database, FileText, Search } from "lucide-react"

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Manage your knowledge base and start chatting.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">128</div>
            <p className="text-xs text-muted-foreground">+4 from last week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Library Status</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Active</div>
            <p className="text-xs text-muted-foreground">rag_assistant_v1</p>
          </CardContent>
        </Card>
        {/* Add more stats */}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
            <CardDescription>Launch common workflows</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
             <div className="flex items-center justify-between p-4 border rounded-lg">
                 <div>
                     <h4 className="font-semibold">Start a New Chat</h4>
                     <p className="text-sm text-muted-foreground">Query your documents using LLM</p>
                 </div>
                 <Link href="/chat">
                    <Button>
                        Open Chat <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                 </Link>
             </div>

             <div className="flex items-center justify-between p-4 border rounded-lg">
                 <div>
                     <h4 className="font-semibold">Ingest Documents</h4>
                     <p className="text-sm text-muted-foreground">Add new files to the knowledge base</p>
                 </div>
                 <Link href="/settings">
                    <Button variant="outline">
                        Manage Data <Database className="ml-2 h-4 w-4" />
                    </Button>
                 </Link>
             </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest ingestions and queries</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
                <div className="flex items-center gap-4">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium">Ingested codebase/src</p>
                        <p className="text-xs text-muted-foreground">2 hours ago</p>
                    </div>
                </div>
                {/* More items */}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
