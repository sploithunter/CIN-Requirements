"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { Toolbar } from "./Toolbar";

interface EditorProps {
  content?: string;
  onChange?: (content: string) => void;
  placeholder?: string;
  editable?: boolean;
}

export function Editor({
  content = "",
  onChange,
  placeholder = "Start writing your requirements...",
  editable = true,
}: EditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder,
      }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class:
          "prose prose-sm sm:prose max-w-none focus:outline-none min-h-[300px] px-4 py-3",
      },
    },
  });

  if (!editor) {
    return null;
  }

  return (
    <div className="border rounded-lg overflow-hidden bg-background">
      {editable && <Toolbar editor={editor} />}
      <EditorContent editor={editor} />
    </div>
  );
}
