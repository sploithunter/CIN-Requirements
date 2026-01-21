import { createClient } from "@liveblocks/client";

export const liveblocksClient = createClient({
  authEndpoint: async (room) => {
    if (!room) {
      throw new Error("Room ID is required");
    }

    // Extract session ID from room name (format: session-{uuid})
    const sessionId = room.replace("session-", "");

    const response = await fetch(`/api/v1/sessions/${sessionId}/liveblocks-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to get Liveblocks token");
    }

    const data = await response.json();
    return { token: data.token };
  },
});

export type UserInfo = {
  name: string;
  email: string;
  avatar?: string;
  color: string;
};

// Generate consistent colors for users based on their ID
export function getUserColor(userId: string): string {
  const colors = [
    "#E57373",
    "#81C784",
    "#64B5F6",
    "#FFD54F",
    "#BA68C8",
    "#4DB6AC",
    "#FF8A65",
    "#A1887F",
  ];

  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}
