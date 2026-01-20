
"use client"

import { ChatInterface } from "@/components/features/ChatInterface"

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-3xl font-bold tracking-tight">Chat Assistant</h2>
        <p className="text-muted-foreground">Ask questions about your ingested documents.</p>
      </div>
      <div className="flex-1 border rounded-lg bg-background shadow-sm">
        <ChatInterface />
      </div>
    </div>
  )
}
