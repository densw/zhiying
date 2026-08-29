import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://zhiying-decision-platform.swworkspace-2782.chatgpt.site'),
  title: '智营｜客户经营决策平台',
  description: '从客户数据到营销决策的一体化经营工作台。',
  openGraph: {
    title: '智营｜客户经营决策平台',
    description: '把客户预测，变成经营决策。',
    images: [{ url: 'https://zhiying-decision-platform.swworkspace-2782.chatgpt.site/og.png', width: 1200, height: 630, alt: '智营客户经营决策平台' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: '智营｜客户经营决策平台',
    description: '把客户预测，变成经营决策。',
    images: ['https://zhiying-decision-platform.swworkspace-2782.chatgpt.site/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
