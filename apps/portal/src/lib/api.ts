export async function sendChatMessage(sessionId: string, query: string) {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    
    const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId, query }),
    });

    if (!res.ok) {
        throw new Error("Failed to connect to Goose Sense backend.");
    }

    return res.json();
}
