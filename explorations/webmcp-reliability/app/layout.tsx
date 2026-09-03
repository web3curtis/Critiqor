import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Critiqor × Crema — Genuine Reliability Experiment',
  description: 'Use the genuine Crema target and anonymous Critiqor dashboards, then inspect the exact method, findings, and five-pair comparison.',
  openGraph: {
    title: 'Critiqor × Crema — Genuine Reliability Experiment',
    description: 'Five matched WebMCP pairs: blind redispatch and duplicate cart peaks fell from 2/5 to 0/5 while task success stayed 5/5.',
    images: [],
  },
  twitter: {
    card: 'summary',
    title: 'Critiqor × Crema — Genuine Reliability Experiment',
    description: 'Five matched WebMCP pairs: blind redispatch and duplicate cart peaks fell from 2/5 to 0/5 while task success stayed 5/5.',
    images: [],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
