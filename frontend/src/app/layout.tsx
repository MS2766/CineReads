import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'CineReads - Movie to Book Recommendations',
  description: 'Turn your favorite movies into personalized book recommendations',
  keywords: ['movies', 'books', 'recommendations', 'reading', 'cinema'],
  authors: [{ name: 'CineReads Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#2563eb',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}