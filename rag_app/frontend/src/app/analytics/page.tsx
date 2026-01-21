
"use client"

import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"

export default function AnalyticsPage() {
  const [clusters, setClusters] = useState<any[]>([])
  const [sentiment, setSentiment] = useState<any>(null)
  const [timeseries, setTimeseries] = useState<any[]>([])

  useEffect(() => {
      fetch("http://localhost:5000/api/analytics/clusters")
        .then(res => res.json())
        .then(data => setClusters(data.data.clusters || []))

      fetch("http://localhost:5000/api/analytics/sentiment")
        .then(res => res.json())
        .then(data => setSentiment(data.data))

      fetch("http://localhost:5000/api/analytics/timeseries")
        .then(res => res.json())
        .then(data => setTimeseries(data.data || []))
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
        <p className="text-muted-foreground">Insights derived from your knowledge base.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Sentiment Analysis */}
          <Card>
              <CardHeader>
                  <CardTitle>Sentiment Analysis</CardTitle>
                  <CardDescription>Overall tone of ingested documents</CardDescription>
              </CardHeader>
              <CardContent>
                  {sentiment ? (
                      <div className="space-y-2">
                          <div className="flex justify-between">
                              <span>Positive</span>
                              <span className="font-bold text-green-600">{sentiment.positive}</span>
                          </div>
                          <div className="flex justify-between">
                              <span>Neutral</span>
                              <span className="font-bold text-gray-600">{sentiment.neutral}</span>
                          </div>
                          <div className="flex justify-between">
                              <span>Negative</span>
                              <span className="font-bold text-red-600">{sentiment.negative}</span>
                          </div>
                      </div>
                  ) : (
                      <p>Loading...</p>
                  )}
              </CardContent>
          </Card>

          {/* Time Series */}
          <Card className="col-span-2">
              <CardHeader>
                  <CardTitle>Ingestion Timeline</CardTitle>
                  <CardDescription>Document creation frequency</CardDescription>
              </CardHeader>
              <CardContent>
                  <div className="h-[200px] flex items-end space-x-2">
                      {timeseries.map((item, i) => (
                          <div key={i} className="flex flex-col items-center flex-1">
                              <div
                                className="w-full bg-blue-500 rounded-t"
                                style={{ height: `${Math.min(item.count * 10, 150)}px` }}
                              />
                              <span className="text-xs mt-2 text-muted-foreground">{item.date}</span>
                          </div>
                      ))}
                  </div>
              </CardContent>
          </Card>
      </div>

      {/* Clusters */}
      <Card>
          <CardHeader>
              <CardTitle>Topic Clusters</CardTitle>
              <CardDescription>Automatically grouped content (Unsupervised Learning)</CardDescription>
          </CardHeader>
          <CardContent>
              <div className="space-y-4">
                  {clusters.map((cluster) => (
                      <div key={cluster.id} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                              <h4 className="font-semibold">Cluster {cluster.id + 1}</h4>
                              <span className="text-xs bg-secondary px-2 py-1 rounded">
                                  {cluster.count} docs
                              </span>
                          </div>
                          <p className="text-sm text-muted-foreground italic">"{cluster.sample_text}"</p>
                          <p className="text-xs mt-2 text-gray-500">Top Source: {cluster.top_source}</p>
                      </div>
                  ))}
                  {clusters.length === 0 && <p>No clusters found.</p>}
              </div>
          </CardContent>
      </Card>
    </div>
  )
}
