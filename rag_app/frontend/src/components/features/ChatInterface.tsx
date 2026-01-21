
import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: userMessage.content,
            history: messages
        }),
      })

      const data = await response.json()

      if (data.status === 'success') {
          const aiMessage: Message = {
              role: 'assistant',
              content: data.response.text,
              sources: data.response.sources
          }
          setMessages(prev => [...prev, aiMessage])
      } else {
          // Handle error
          setMessages(prev => [...prev, { role: 'assistant', content: "Error: " + data.message }])
      }

    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { role: 'assistant', content: "Failed to connect to backend." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "flex w-full",
              m.role === 'user' ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-lg p-4",
                m.role === 'user'
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-300 text-xs opacity-70">
                      <strong>Sources:</strong>
                      <ul className="list-disc pl-4 mt-1">
                          {m.sources.map((s: any, idx: number) => (
                              <li key={idx} className="truncate">
                                  {s.file_source} (p. {s.page_num || 1})
                              </li>
                          ))}
                      </ul>
                  </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-4 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your codebase..."
            disabled={loading}
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Thinking...' : 'Send'}
          </Button>
        </form>
      </div>
    </div>
  )
}
