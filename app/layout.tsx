import type { Metadata } from 'next'
import { SpeedInsights } from '@vercel/speed-insights/next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Lumbago Codex',
  description: 'Lumbago Music AI - Desktop app for DJs and music collectors',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}
        <SpeedInsights />
      </body>
    </html>
  )
}

