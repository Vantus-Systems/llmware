
"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card"

export default function SettingsPage() {
  const [ingestPath, setIngestPath] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")

  // Config state
  const [config, setConfig] = useState({
      embedding_model: "",
      vector_db: "",
      llm_model: ""
  })

  useEffect(() => {
      // Fetch initial status/config
      fetch("http://localhost:5000/api/status")
        .then(res => res.json())
        .then(data => {
            if(data.status === "ok" && data.config) {
                setConfig(data.config)
            }
        })
        .catch(err => console.error(err))
  }, [])

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

  const handleConfigUpdate = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config)
        })
        const data = await res.json()
        if (data.status === "success") {
            alert("Configuration updated!")
        }
      } catch (e) {
          alert("Failed to update config")
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
          <CardTitle>Pipeline Configuration</CardTitle>
          <CardDescription>Select models for embedding and inference.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium">Embedding Model</label>
                    <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={config.embedding_model}
                        onChange={(e) => setConfig({...config, embedding_model: e.target.value})}
                    >
                        <option value="mini-lm-sbert">mini-lm-sbert (Fast)</option>
                        <option value="industry-bert-sec">industry-bert-sec (Finance)</option>
                    </select>
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium">Vector Database</label>
                    <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={config.vector_db}
                        onChange={(e) => setConfig({...config, vector_db: e.target.value})}
                    >
                        <option value="sqlite">SQLite (Embedded)</option>
                        <option value="chromadb">ChromaDB</option>
                        <option value="milvus">Milvus</option>
                    </select>
                </div>
                <div className="space-y-2">
                    <label className="text-sm font-medium">Inference Model (LLM)</label>
                    <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={config.inference_model}
                        onChange={(e) => setConfig({...config, llm_model: e.target.value})}
                    >
                        <option value="bling-phi-3-gguf">bling-phi-3-gguf</option>
                        <option value="bling-tiny-llama-v0">bling-tiny-llama-v0</option>
                        <option value="dragon-yi-6b-v0">dragon-yi-6b-v0 (High Quality)</option>
                    </select>
                </div>
            </div>
        </CardContent>
        <CardFooter>
            <Button onClick={handleConfigUpdate}>Save Configuration</Button>
        </CardFooter>
      </Card>
    </div>
  )
}
