
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card"

export default function SettingsPage() {
  const [ingestPath, setIngestPath] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")

  const handleIngest = async () => {
    if (!ingestPath) return
    setLoading(true)
    setMessage("")
    try {
        const res = await fetch("http://localhost:5000/api/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path: ingestPath })
        })
        const data = await res.json()
        if (data.status === "success") {
            setMessage("Ingestion successful!")
        } else {
            setMessage("Error: " + data.message)
        }
    } catch (e) {
        setMessage("Connection failed.")
    } finally {
        setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Configure your RAG pipeline.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Data Ingestion</CardTitle>
          <CardDescription>
            Point to a local folder to ingest documents into the library.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Local Folder Path</label>
            <Input
                placeholder="/path/to/documents"
                value={ingestPath}
                onChange={(e) => setIngestPath(e.target.value)}
            />
          </div>
          {message && (
              <p className={`text-sm ${message.startsWith("Error") ? "text-red-500" : "text-green-500"}`}>
                  {message}
              </p>
          )}
        </CardContent>
        <CardFooter>
          <Button onClick={handleIngest} disabled={loading}>
            {loading ? "Ingesting..." : "Start Ingestion"}
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model Configuration</CardTitle>
          <CardDescription>Select models for embedding and inference.</CardDescription>
        </CardHeader>
        <CardContent>
            <div className="space-y-2">
                <p className="text-sm">Current Embedding Model: <strong>mini-lm-sbert</strong></p>
                <p className="text-sm">Current LLM: <strong>bling-phi-3-gguf</strong></p>
                <p className="text-xs text-muted-foreground mt-2">To change models, update <code>backend/rag_engine.py</code>.</p>
            </div>
        </CardContent>
      </Card>
    </div>
  )
}
