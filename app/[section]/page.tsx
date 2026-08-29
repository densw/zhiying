import { redirect } from 'next/navigation';

const destinations = {
  analytics: 'http://analytics.localhost',
  decision: 'http://decision.localhost',
  reports: 'http://report.localhost',
  experiments: 'http://experiments.localhost',
  monitoring: 'http://monitor.localhost',
  pipeline: 'http://pipeline.localhost',
} as const;

export default async function SectionRedirect({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  redirect(destinations[section as keyof typeof destinations] ?? '/');
}
