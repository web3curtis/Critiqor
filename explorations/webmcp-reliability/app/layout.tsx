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
  title: 'Critiqor Lab — Interactive WebMCP Reliability Experiment',
  description: 'Run an interactive replay of matched raw and playbook-improved WebMCP experiments, then inspect Critiqor audits and compare the results.',
  openGraph: {
    title: 'Critiqor Lab — Raw vs Improved WebMCP',
    description: 'Replay the experiment. Inspect both audits. Compare 2 effects with 1.',
    images: [{ url: '/og.png', width: 1731, height: 909, alt: 'Raw WebMCP run with two effects compared with an improved run with one effect' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Critiqor Lab — Raw vs Improved WebMCP',
    description: 'Replay the experiment. Inspect both audits. Compare 2 effects with 1.',
    images: ['/og.png'],
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
