import { AlertTriangle, Target, TrendingDown, TrendingUp, PiggyBank, Brain } from 'lucide-react';
import './AIInsights.css';

const TYPE_CONFIG = {
  risk:        { icon: AlertTriangle, accent: 'red',    label: 'Risk'        },
  warning:     { icon: Target,        accent: 'yellow',  label: 'Warning'     },
  info:        { icon: Brain,         accent: 'blue',    label: 'Insight'     },
  opportunity: { icon: TrendingDown,  accent: 'green',   label: 'Opportunity' },
  success:     { icon: TrendingUp,    accent: 'green',   label: 'Positive'    },
};

function BriefingItem({ item }) {
  const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.info;
  const Icon = cfg.icon;
  return (
    <div className={`briefing-item briefing-item--${cfg.accent}`}>
      <div className={`briefing-item-icon briefing-item-icon--${cfg.accent}`}>
        <Icon size={13} strokeWidth={2} />
      </div>
      <div className="briefing-item-body">
        <div className="briefing-item-meta">
          <span className={`briefing-item-tag briefing-item-tag--${cfg.accent}`}>{item.label}</span>
        </div>
        <span className="briefing-item-title">{item.title}</span>
        <p className="briefing-item-desc">{item.body}</p>
      </div>
    </div>
  );
}

function SkeletonItem() {
  return (
    <div className="briefing-item briefing-item--skeleton">
      <div className="briefing-skeleton-icon" />
      <div className="briefing-skeleton-body">
        <div className="briefing-skeleton-tag" />
        <div className="briefing-skeleton-title" />
        <div className="briefing-skeleton-desc" />
      </div>
    </div>
  );
}

export default function AIInsights({ loading, items = [] }) {
  const today = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <div className="briefing-card">
      <div className="briefing-header">
        <div>
          <div className="briefing-header-row">
            <span className="briefing-badge">AI</span>
            <h2 className="briefing-title">Mate's Daily Briefing</h2>
          </div>
          <p className="briefing-subtitle">{today} · Generated from your data</p>
        </div>
      </div>

      <div className="briefing-list">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonItem key={i} />)
        ) : items.length === 0 ? (
          <div className="briefing-empty">
            <Brain size={28} strokeWidth={1.5} />
            <p>Upload transactions to get personalized insights.</p>
          </div>
        ) : (
          items.map((item, i) => <BriefingItem key={i} item={item} />)
        )}
      </div>
    </div>
  );
}
