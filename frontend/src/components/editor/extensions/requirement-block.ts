import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer } from "@tiptap/react";

export interface RequirementBlockOptions {
  HTMLAttributes: Record<string, unknown>;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    requirementBlock: {
      setRequirementBlock: (attributes?: {
        id?: string;
        category?: string;
        priority?: string;
      }) => ReturnType;
      toggleRequirementBlock: () => ReturnType;
    };
  }
}

export const RequirementBlock = Node.create<RequirementBlockOptions>({
  name: "requirementBlock",

  group: "block",

  content: "block+",

  defining: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    };
  },

  addAttributes() {
    return {
      id: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-requirement-id"),
        renderHTML: (attributes) => {
          if (!attributes.id) return {};
          return { "data-requirement-id": attributes.id };
        },
      },
      category: {
        default: "functional",
        parseHTML: (element) =>
          element.getAttribute("data-category") || "functional",
        renderHTML: (attributes) => ({
          "data-category": attributes.category,
        }),
      },
      priority: {
        default: "medium",
        parseHTML: (element) =>
          element.getAttribute("data-priority") || "medium",
        renderHTML: (attributes) => ({
          "data-priority": attributes.priority,
        }),
      },
      status: {
        default: "draft",
        parseHTML: (element) => element.getAttribute("data-status") || "draft",
        renderHTML: (attributes) => ({
          "data-status": attributes.status,
        }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: 'div[data-type="requirement-block"]',
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": "requirement-block",
        class: "requirement-block",
      }),
      0,
    ];
  },

  addCommands() {
    return {
      setRequirementBlock:
        (attributes) =>
        ({ commands }) => {
          return commands.wrapIn(this.name, attributes);
        },
      toggleRequirementBlock:
        () =>
        ({ commands }) => {
          return commands.toggleWrap(this.name);
        },
    };
  },

  addKeyboardShortcuts() {
    return {
      "Mod-Shift-r": () => this.editor.commands.toggleRequirementBlock(),
    };
  },
});

// CSS styles for the requirement block (add to globals.css)
export const requirementBlockStyles = `
.requirement-block {
  position: relative;
  margin: 1rem 0;
  padding: 1rem;
  padding-left: 1.5rem;
  border-left: 4px solid hsl(var(--primary));
  background-color: hsl(var(--muted) / 0.3);
  border-radius: 0 0.5rem 0.5rem 0;
}

.requirement-block::before {
  content: 'REQ';
  position: absolute;
  top: -0.5rem;
  left: -0.25rem;
  padding: 0.125rem 0.5rem;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  border-radius: 0.25rem;
}

.requirement-block[data-priority="high"] {
  border-left-color: hsl(0 84% 60%);
}

.requirement-block[data-priority="high"]::before {
  background-color: hsl(0 84% 60%);
}

.requirement-block[data-priority="low"] {
  border-left-color: hsl(142 76% 36%);
}

.requirement-block[data-priority="low"]::before {
  background-color: hsl(142 76% 36%);
}

.requirement-block[data-category="non-functional"] {
  border-left-style: dashed;
}

.requirement-block[data-category="constraint"] {
  border-left-style: dotted;
}
`;
