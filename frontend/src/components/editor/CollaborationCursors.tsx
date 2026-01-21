"use client";

import { useOthers, useSelf } from "@liveblocks/react/suspense";

interface Cursor {
  x: number;
  y: number;
}

interface Presence {
  cursor: Cursor | null;
  selection: unknown;
}

interface UserInfo {
  name: string;
  color: string;
  avatar?: string;
}

export function CollaborationCursors() {
  const others = useOthers();

  return (
    <>
      {others.map(({ connectionId, presence, info }) => {
        const cursor = (presence as unknown as Presence)?.cursor;
        if (!cursor) return null;

        const userInfo = info as unknown as UserInfo;

        return (
          <div
            key={connectionId}
            className="pointer-events-none absolute z-50 transition-transform duration-75"
            style={{
              transform: `translate(${cursor.x}px, ${cursor.y}px)`,
            }}
          >
            {/* Cursor */}
            <svg
              width="24"
              height="36"
              viewBox="0 0 24 36"
              fill="none"
              className="drop-shadow-md"
            >
              <path
                d="M5.65376 12.3673H5.46026L5.31717 12.4976L0.500002 16.8829L0.500002 1.19841L11.7841 12.3673H5.65376Z"
                fill={userInfo?.color || "#000"}
                stroke="white"
              />
            </svg>

            {/* Name tag */}
            <div
              className="absolute left-4 top-4 px-2 py-1 rounded text-xs text-white whitespace-nowrap"
              style={{ backgroundColor: userInfo?.color || "#000" }}
            >
              {userInfo?.name || "Anonymous"}
            </div>
          </div>
        );
      })}
    </>
  );
}

export function useCollaborators() {
  const others = useOthers();
  const self = useSelf();

  return {
    others: others.map((other) => ({
      id: other.connectionId,
      info: other.info as unknown as UserInfo,
      presence: other.presence as unknown as Presence,
    })),
    self: self
      ? {
          id: self.connectionId,
          info: self.info as unknown as UserInfo,
          presence: self.presence as unknown as Presence,
        }
      : null,
    count: others.length + 1,
  };
}
