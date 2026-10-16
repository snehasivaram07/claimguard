import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ShieldCheck, ArrowRight, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AuditEventItem } from '../../types';

interface RecentActivityWidgetProps {
  events: AuditEventItem[];
  isLoading?: boolean;
}

export const RecentActivityWidget: React.FC<RecentActivityWidgetProps> = ({
  events,
  isLoading = false,
}) => {
  const formatAction = (action: string) => {
    return action
      .replace(/_/g, ' ')
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-500" />
            <CardTitle>Recent Audit Trail</CardTitle>
          </div>
          <CardDescription>
            Immutable chronological record of security and investigative actions.
          </CardDescription>
        </div>
        <Link to="/audit" className="text-xs font-semibold text-brand-500 hover:text-brand-400">
          Full trail &rarr;
        </Link>
      </CardHeader>

      <CardContent className="flex-1 space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-14 bg-slate-100 dark:bg-navy-800 animate-pulse rounded-lg"
              />
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="py-8 text-center text-slate-500 dark:text-slate-400">
            <Clock className="h-7 w-7 mx-auto mb-2 opacity-50" />
            <p className="text-xs font-medium">No activity recorded in this session yet.</p>
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              className="p-3 rounded-xl border border-slate-100 dark:border-navy-800 bg-slate-50/50 dark:bg-navy-850/40 flex items-center justify-between text-xs"
            >
              <div className="space-y-0.5 min-w-0 pr-3">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {formatAction(event.action)}
                  </span>
                  <Badge
                    variant={event.outcome === 'SUCCESS' ? 'success' : 'danger'}
                    size="sm"
                  >
                    {event.outcome}
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                  {event.resource_type}: {event.resource_id}
                </p>
              </div>

              <div className="text-[11px] text-slate-400 dark:text-slate-500 shrink-0">
                {new Date(event.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          ))
        )}
      </CardContent>

      <CardFooter className="py-3">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Live tamper-proof events
        </span>
        <Link to="/audit">
          <Button size="sm" variant="outline" rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
            View Audit Log
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
};
