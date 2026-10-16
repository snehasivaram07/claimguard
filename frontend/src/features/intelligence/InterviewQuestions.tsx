import React, { useState } from 'react';
import {
  HelpCircle,
  Copy,
  Check,
  Sparkles,
} from 'lucide-react';

interface InterviewQuestionsProps {
  questions: string[];
}

export const InterviewQuestions: React.FC<InterviewQuestionsProps> = ({ questions }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedAll, setCopiedAll] = useState<boolean>(false);

  const copyToClipboard = async (text: string, index?: number) => {
    try {
      await navigator.clipboard.writeText(text);
      if (typeof index === 'number') {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
      } else {
        setCopiedAll(true);
        setTimeout(() => setCopiedAll(false), 2000);
      }
    } catch {
      // Ignore clipboard write failure
    }
  };

  const handleCopyAll = () => {
    const formatted = questions
      .map((q, idx) => `${idx + 1}. ${q}`)
      .join('\n\n');
    copyToClipboard(formatted);
  };

  if (!questions || questions.length === 0) {
    return (
      <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm text-center py-8">
        <Sparkles className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
          No Pending Investigator Questions
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
          Submitted documentation provided sufficient internal consistency with no prominent evidentiary gaps requiring deposition inquiry.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-700/80 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-navy-800">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-brand-500" />
            Targeted Interview & Deposition Questions ({questions.length})
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Probe contradictory statements during claimant or witness recorded examinations
          </p>
        </div>

        <button
          onClick={handleCopyAll}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-950 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors shrink-0"
        >
          {copiedAll ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                All Copied!
              </span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 text-slate-400" />
              <span>Copy All Questions</span>
            </>
          )}
        </button>
      </div>

      {/* Questions List */}
      <div className="space-y-2.5">
        {questions.map((question, index) => {
          const isCopied = copiedIndex === index;

          return (
            <div
              key={index}
              className="flex items-start justify-between gap-3 p-3.5 rounded-lg bg-slate-50/80 dark:bg-navy-950/60 hover:bg-slate-50 dark:hover:bg-navy-950 border border-slate-200/80 dark:border-navy-800 transition-all group"
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <span className="flex items-center justify-center h-6 w-6 rounded-full bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold text-xs shrink-0 mt-0.5 border border-brand-500/20">
                  {index + 1}
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                  {question}
                </p>
              </div>

              <button
                onClick={() => copyToClipboard(question, index)}
                className="p-1.5 rounded-md hover:bg-white dark:hover:bg-navy-900 border border-transparent hover:border-slate-200 dark:hover:border-navy-700 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors shrink-0"
                title="Copy question text"
              >
                {isCopied ? (
                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                ) : (
                  <Copy className="h-3.5 w-3.5 opacity-60 group-hover:opacity-100" />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
