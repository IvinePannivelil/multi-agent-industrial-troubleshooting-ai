export interface TelemetryData {
    timestamp: string;
    temperature: number; // Critical > 75
    flowRate: number;
    pressure: number;
}

export function generateTelemetry(): TelemetryData {
    const now = new Date();

    // Base values with slight random fluctuations
    // Temperature designed to occasionally spike above 75
    const baseTemp = 72;
    const tempSpike = Math.random() > 0.8 ? (Math.random() * 5 + 3) : (Math.random() * 4 - 2);

    return {
        timestamp: now.toLocaleTimeString(),
        temperature: Number((baseTemp + tempSpike).toFixed(1)),
        flowRate: Number((120 + Math.random() * 10 - 5).toFixed(1)), // L/min
        pressure: Number((2.5 + Math.random() * 0.2 - 0.1).toFixed(2)), // Bar
    };
}
