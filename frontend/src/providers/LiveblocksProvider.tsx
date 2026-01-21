"use client";

import { ReactNode } from "react";
import { RoomProvider } from "@liveblocks/react/suspense";
import { liveblocksClient, getUserColor } from "@/lib/liveblocks";
import { useAuth } from "./AuthProvider";

interface LiveblocksRoomProviderProps {
  roomId: string;
  children: ReactNode;
}

export function LiveblocksRoomProvider({
  roomId,
  children,
}: LiveblocksRoomProviderProps) {
  const { user } = useAuth();

  if (!user) {
    return <>{children}</>;
  }

  return (
    <RoomProvider
      id={roomId}
      initialPresence={{
        cursor: null,
        selection: null,
      }}
    >
      {children}
    </RoomProvider>
  );
}

export { liveblocksClient };
