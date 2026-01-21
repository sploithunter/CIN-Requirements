"use client";

import type { Section, SectionBinding, BindingType } from "@/types";
import { cn } from "@/lib/utils";

interface ActiveSectionBannerProps {
  section: Section | null;
  binding: SectionBinding | null;
  onChangeBindingType?: (type: BindingType) => void;
  onDeactivate?: () => void;
  className?: string;
}

const bindingTypeConfig: Record<
  BindingType,
  { label: string; icon: string; color: string; bgColor: string }
> = {
  discussion: {
    label: "Discussing",
    icon: "💬",
    color: "text-blue-700",
    bgColor: "bg-blue-50 border-blue-200",
  },
  editing: {
    label: "Editing",
    icon: "✏️",
    color: "text-purple-700",
    bgColor: "bg-purple-50 border-purple-200",
  },
  reference: {
    label: "Referencing",
    icon: "🔗",
    color: "text-gray-700",
    bgColor: "bg-gray-50 border-gray-200",
  },
  question: {
    label: "Asking about",
    icon: "❓",
    color: "text-yellow-700",
    bgColor: "bg-yellow-50 border-yellow-200",
  },
  approval: {
    label: "Reviewing for approval",
    icon: "✅",
    color: "text-green-700",
    bgColor: "bg-green-50 border-green-200",
  },
};

export function ActiveSectionBanner({
  section,
  binding,
  onChangeBindingType,
  onDeactivate,
  className,
}: ActiveSectionBannerProps) {
  if (!section || !binding) {
    return null;
  }

  const config = bindingTypeConfig[binding.binding_type];

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2 rounded-lg border",
        config.bgColor,
        className
      )}
    >
      <span className="text-lg">{config.icon}</span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn("text-sm font-medium", config.color)}>
            {config.label}
          </span>
          <span className="text-sm text-gray-600">
            Section {section.section_number}: {section.title}
          </span>
        </div>
        {section.content_preview && (
          <p className="text-xs text-gray-500 truncate mt-0.5">
            {section.content_preview}
          </p>
        )}
      </div>

      {/* Binding type selector */}
      {onChangeBindingType && (
        <select
          value={binding.binding_type}
          onChange={(e) => onChangeBindingType(e.target.value as BindingType)}
          className="text-xs border rounded px-2 py-1 bg-white"
        >
          {(Object.keys(bindingTypeConfig) as BindingType[]).map((type) => (
            <option key={type} value={type}>
              {bindingTypeConfig[type].label}
            </option>
          ))}
        </select>
      )}

      {/* Close button */}
      {onDeactivate && (
        <button
          onClick={onDeactivate}
          className="p-1 text-gray-400 hover:text-gray-600 rounded"
          title="Clear section focus"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
