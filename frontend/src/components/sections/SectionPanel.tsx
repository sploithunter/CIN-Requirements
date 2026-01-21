"use client";

import { useState } from "react";
import type { Section, SectionBinding, BindingType, SectionStatus } from "@/types";
import { cn } from "@/lib/utils";

interface SectionPanelProps {
  sections: Section[];
  activeBindings: SectionBinding[];
  activeSectionId: string | null;
  onSectionClick: (sectionId: string) => void;
  onSectionActivate: (sectionId: string, bindingType: BindingType) => void;
  onSectionDeactivate: (sectionId: string) => void;
  onSectionStatusChange?: (sectionId: string, status: SectionStatus) => void;
  className?: string;
}

const statusColors: Record<SectionStatus, string> = {
  empty: "bg-gray-100 border-gray-300",
  draft: "bg-blue-50 border-blue-300",
  needs_review: "bg-yellow-50 border-yellow-300",
  approved: "bg-green-50 border-green-300",
  disputed: "bg-red-50 border-red-300",
};

const statusLabels: Record<SectionStatus, string> = {
  empty: "Empty",
  draft: "Draft",
  needs_review: "Needs Review",
  approved: "Approved",
  disputed: "Disputed",
};

const bindingTypeColors: Record<BindingType, string> = {
  discussion: "ring-blue-500",
  editing: "ring-purple-500",
  reference: "ring-gray-500",
  question: "ring-yellow-500",
  approval: "ring-green-500",
};

const bindingTypeLabels: Record<BindingType, string> = {
  discussion: "Discussing",
  editing: "Editing",
  reference: "Referenced",
  question: "Question",
  approval: "Approving",
};

export function SectionPanel({
  sections,
  activeBindings,
  activeSectionId,
  onSectionClick,
  onSectionActivate,
  onSectionDeactivate,
  onSectionStatusChange,
  className,
}: SectionPanelProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleExpanded = (sectionId: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  const getActiveBinding = (sectionId: string) =>
    activeBindings.find((b) => b.section_id === sectionId && b.is_active);

  const isActive = (sectionId: string) => activeSectionId === sectionId;

  // Build tree structure
  const rootSections = sections.filter((s) => !s.parent_id);
  const getChildren = (parentId: string) =>
    sections.filter((s) => s.parent_id === parentId).sort((a, b) => a.order - b.order);

  const renderSection = (section: Section, depth = 0) => {
    const children = getChildren(section.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedSections.has(section.id);
    const binding = getActiveBinding(section.id);
    const active = isActive(section.id);

    return (
      <div key={section.id} className="select-none">
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg border-2 cursor-pointer transition-all",
            statusColors[section.status],
            active && binding && `ring-2 ${bindingTypeColors[binding.binding_type]}`,
            active && "shadow-md",
            !active && "hover:shadow-sm"
          )}
          style={{ marginLeft: depth * 16 }}
          onClick={() => onSectionClick(section.id)}
        >
          {/* Expand/collapse toggle */}
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpanded(section.id);
              }}
              className="w-5 h-5 flex items-center justify-center text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? "−" : "+"}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}

          {/* Section number and title */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-gray-500">
                {section.section_number}
              </span>
              <span className="font-medium truncate">{section.title}</span>
            </div>
            {section.content_preview && (
              <p className="text-xs text-gray-500 truncate mt-0.5">
                {section.content_preview}
              </p>
            )}
          </div>

          {/* Status badge */}
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded-full whitespace-nowrap",
              section.status === "approved" && "bg-green-100 text-green-700",
              section.status === "needs_review" && "bg-yellow-100 text-yellow-700",
              section.status === "draft" && "bg-blue-100 text-blue-700",
              section.status === "disputed" && "bg-red-100 text-red-700",
              section.status === "empty" && "bg-gray-100 text-gray-500"
            )}
          >
            {statusLabels[section.status]}
          </span>

          {/* Active binding indicator */}
          {active && binding && (
            <span
              className={cn(
                "text-xs px-2 py-0.5 rounded-full whitespace-nowrap animate-pulse",
                binding.binding_type === "discussion" && "bg-blue-100 text-blue-700",
                binding.binding_type === "editing" && "bg-purple-100 text-purple-700",
                binding.binding_type === "question" && "bg-yellow-100 text-yellow-700",
                binding.binding_type === "approval" && "bg-green-100 text-green-700"
              )}
            >
              {bindingTypeLabels[binding.binding_type]}
            </span>
          )}

          {/* AI indicator */}
          {section.ai_generated && (
            <span className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded">
              AI
            </span>
          )}

          {/* Action buttons */}
          <div className="flex items-center gap-1">
            {active ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSectionDeactivate(section.id);
                }}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
                title="Stop focusing on this section"
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
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSectionActivate(section.id, "discussion");
                }}
                className="p-1 text-gray-400 hover:text-blue-600 rounded"
                title="Focus on this section"
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
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {children.map((child) => renderSection(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">Document Sections</h3>
        {activeSectionId && (
          <button
            onClick={() => onSectionDeactivate(activeSectionId)}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Clear focus
          </button>
        )}
      </div>

      {sections.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">
          No sections yet. Sections will appear as the document is structured.
        </p>
      ) : (
        <div className="space-y-1">
          {rootSections
            .sort((a, b) => a.order - b.order)
            .map((section) => renderSection(section))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 mb-2">Section Status</p>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(statusLabels) as SectionStatus[]).map((status) => (
            <span
              key={status}
              className={cn(
                "text-xs px-2 py-0.5 rounded border",
                statusColors[status]
              )}
            >
              {statusLabels[status]}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
