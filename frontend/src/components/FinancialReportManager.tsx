import React, { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Progress } from './ui/progress'

export default function FinancialReportManager() {
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleFetchReports = async () => {
    setIsLoading(true)
    setProgress(0)
    setMessage('')
    setError(null)

    try {
      const response = await fetch('/api/admin/financial-reports/fetch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('決算資料の取得に失敗しました')
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('レスポンスの読み取りに失敗しました')
      }

      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // Server-Sent Eventsのメッセージをデコード
        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.error) {
                setError(prev => prev ? `${prev}\n${data.error}` : data.error)
              } else {
                if (data.progress !== undefined) {
                  setProgress(data.progress)
                }
                if (data.message) {
                  setMessage(data.message)
                }
              }
            } catch (e) {
              console.error('Failed to parse SSE message:', e)
            }
          }
        }
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : '予期せぬエラーが発生しました')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>決算資料管理</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Button
            onClick={handleFetchReports}
            disabled={isLoading}
          >
            {isLoading ? '取得中...' : '決算資料を取得'}
          </Button>
          {isLoading && (
            <div className="flex-1">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-gray-500 mt-1">{message}</p>
            </div>
          )}
        </div>
        
        {error && (
          <div className="text-red-500 text-sm whitespace-pre-line">
            {error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
