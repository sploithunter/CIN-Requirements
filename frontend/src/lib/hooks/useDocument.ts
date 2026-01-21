"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "@/lib/api";
import type {
  DocumentWithContent,
  Section,
  SectionBinding,
  BindingType,
  SectionStatus,
} from "@/types";

interface UseDocumentOptions {
  documentId: string;
  onError?: (error: Error) => void;
}

export function useDocument({ documentId, onError }: UseDocumentOptions) {
  const [document, setDocument] = useState<DocumentWithContent | null>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [activeBindings, setActiveBindings] = useState<SectionBinding[]>([]);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load document and sections
  const loadDocument = useCallback(async () => {
    try {
      setIsLoading(true);
      const [doc, sectionList, bindings] = await Promise.all([
        api.getDocument(documentId),
        api.listSections(documentId),
        api.getActiveBindings(documentId),
      ]);
      setDocument(doc);
      setSections(sectionList);
      setActiveBindings(bindings);
      setError(null);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to load document");
      setError(error);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [documentId, onError]);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  // Update document content
  const updateContent = useCallback(
    async (content: Record<string, unknown>) => {
      try {
        const updated = await api.updateDocument(documentId, { content });
        setDocument((prev) => (prev ? { ...prev, content } : null));
        return updated;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to update document");
        onError?.(error);
        throw error;
      }
    },
    [documentId, onError]
  );

  // Create a version snapshot
  const createVersion = useCallback(
    async (changeSummary?: string) => {
      try {
        return await api.createDocumentVersion(documentId, changeSummary);
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to create version");
        onError?.(error);
        throw error;
      }
    },
    [documentId, onError]
  );

  // Section management
  const createSection = useCallback(
    async (data: { section_number: string; title: string; parent_id?: string; order?: number }) => {
      try {
        const section = await api.createSection(documentId, data);
        setSections((prev) => [...prev, section]);
        return section;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to create section");
        onError?.(error);
        throw error;
      }
    },
    [documentId, onError]
  );

  const updateSection = useCallback(
    async (sectionId: string, data: Partial<Section>) => {
      try {
        const updated = await api.updateSection(documentId, sectionId, data);
        setSections((prev) =>
          prev.map((s) => (s.id === sectionId ? { ...s, ...updated } : s))
        );
        return updated;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to update section");
        onError?.(error);
        throw error;
      }
    },
    [documentId, onError]
  );

  const deleteSection = useCallback(
    async (sectionId: string) => {
      try {
        await api.deleteSection(documentId, sectionId);
        setSections((prev) => prev.filter((s) => s.id !== sectionId));
        if (activeSectionId === sectionId) {
          setActiveSectionId(null);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to delete section");
        onError?.(error);
        throw error;
      }
    },
    [documentId, activeSectionId, onError]
  );

  // Section binding management
  const activateSection = useCallback(
    async (sectionId: string, bindingType: BindingType = "discussion", messageId?: string) => {
      try {
        // Deactivate current binding if exists
        const currentBinding = activeBindings.find(
          (b) => b.section_id === activeSectionId && b.is_active
        );
        if (currentBinding) {
          await api.updateSectionBinding(documentId, currentBinding.id, { is_active: false });
        }

        // Create new binding
        const binding = await api.createSectionBinding(documentId, sectionId, {
          binding_type: bindingType,
          message_id: messageId,
        });

        setActiveBindings((prev) => [
          ...prev.filter((b) => b.section_id !== sectionId || !b.is_active),
          binding,
        ]);
        setActiveSectionId(sectionId);

        return binding;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to activate section");
        onError?.(error);
        throw error;
      }
    },
    [documentId, activeBindings, activeSectionId, onError]
  );

  const deactivateSection = useCallback(
    async (sectionId: string) => {
      try {
        const binding = activeBindings.find(
          (b) => b.section_id === sectionId && b.is_active
        );
        if (binding) {
          await api.updateSectionBinding(documentId, binding.id, { is_active: false });
          setActiveBindings((prev) =>
            prev.map((b) => (b.id === binding.id ? { ...b, is_active: false } : b))
          );
        }
        if (activeSectionId === sectionId) {
          setActiveSectionId(null);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Failed to deactivate section");
        onError?.(error);
        throw error;
      }
    },
    [documentId, activeBindings, activeSectionId, onError]
  );

  // Get section by ID
  const getSectionById = useCallback(
    (sectionId: string) => sections.find((s) => s.id === sectionId),
    [sections]
  );

  // Check if a section is active
  const isSectionActive = useCallback(
    (sectionId: string) => activeSectionId === sectionId,
    [activeSectionId]
  );

  // Get active binding for a section
  const getActiveBinding = useCallback(
    (sectionId: string) => activeBindings.find((b) => b.section_id === sectionId && b.is_active),
    [activeBindings]
  );

  return {
    // Data
    document,
    sections,
    activeBindings,
    activeSectionId,
    activeSection: activeSectionId ? getSectionById(activeSectionId) : null,

    // State
    isLoading,
    error,

    // Document actions
    updateContent,
    createVersion,
    reload: loadDocument,

    // Section actions
    createSection,
    updateSection,
    deleteSection,

    // Binding actions
    activateSection,
    deactivateSection,

    // Helpers
    getSectionById,
    isSectionActive,
    getActiveBinding,
  };
}
