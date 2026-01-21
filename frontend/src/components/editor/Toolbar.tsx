"use client";

import { Editor } from "@tiptap/react";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading1,
  Heading2,
  Heading3,
  Quote,
  Undo,
  Redo,
  Code,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ToolbarProps {
  editor: Editor;
}

export function Toolbar({ editor }: ToolbarProps) {
  const tools = [
    {
      icon: Bold,
      label: "Bold",
      action: () => editor.chain().focus().toggleBold().run(),
      isActive: () => editor.isActive("bold"),
    },
    {
      icon: Italic,
      label: "Italic",
      action: () => editor.chain().focus().toggleItalic().run(),
      isActive: () => editor.isActive("italic"),
    },
    {
      icon: Code,
      label: "Code",
      action: () => editor.chain().focus().toggleCode().run(),
      isActive: () => editor.isActive("code"),
    },
    { type: "divider" as const },
    {
      icon: Heading1,
      label: "Heading 1",
      action: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
      isActive: () => editor.isActive("heading", { level: 1 }),
    },
    {
      icon: Heading2,
      label: "Heading 2",
      action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
      isActive: () => editor.isActive("heading", { level: 2 }),
    },
    {
      icon: Heading3,
      label: "Heading 3",
      action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
      isActive: () => editor.isActive("heading", { level: 3 }),
    },
    { type: "divider" as const },
    {
      icon: List,
      label: "Bullet List",
      action: () => editor.chain().focus().toggleBulletList().run(),
      isActive: () => editor.isActive("bulletList"),
    },
    {
      icon: ListOrdered,
      label: "Numbered List",
      action: () => editor.chain().focus().toggleOrderedList().run(),
      isActive: () => editor.isActive("orderedList"),
    },
    {
      icon: Quote,
      label: "Quote",
      action: () => editor.chain().focus().toggleBlockquote().run(),
      isActive: () => editor.isActive("blockquote"),
    },
    { type: "divider" as const },
    {
      icon: Undo,
      label: "Undo",
      action: () => editor.chain().focus().undo().run(),
      isActive: () => false,
      disabled: () => !editor.can().undo(),
    },
    {
      icon: Redo,
      label: "Redo",
      action: () => editor.chain().focus().redo().run(),
      isActive: () => false,
      disabled: () => !editor.can().redo(),
    },
  ];

  return (
    <div className="flex items-center gap-1 p-2 border-b bg-muted/50 flex-wrap">
      {tools.map((tool, index) => {
        if ("type" in tool && tool.type === "divider") {
          return (
            <div key={index} className="w-px h-6 bg-border mx-1" />
          );
        }

        const Icon = tool.icon;
        const isActive = tool.isActive?.();
        const isDisabled = "disabled" in tool && tool.disabled?.();

        return (
          <Button
            key={index}
            variant="ghost"
            size="icon"
            className={cn("h-8 w-8", {
              "bg-accent": isActive,
            })}
            onClick={tool.action}
            disabled={isDisabled}
            title={tool.label}
          >
            <Icon className="h-4 w-4" />
          </Button>
        );
      })}
    </div>
  );
}
