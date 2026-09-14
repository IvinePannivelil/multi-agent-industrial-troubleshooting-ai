"use client";

import React, { useState, useEffect } from "react";
import { generateTelemetry, TelemetryData } from "@/lib/telemetry";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { AlertCircle, Thermometer, CheckCircle2, HardDrive, Users } from "lucide-react";

const MAX_DATA_POINTS = 20;
const CRITICAL_TEMP = 75;

export default function DashboardPage() {
    const [data, setData] = useState<TelemetryData[]>([]);
    const [resolutionData, setResolutionData] = useState<any>(null);
    const [isAlerting, setIsAlerting] = useState(false);

    useEffect(() => {
        // Initial data load
        const initialData = Array.from({ length: 10 }, generateTelemetry);
        setData(initialData);

        // Live update interval
        const interval = setInterval(() => {
            setData((currentData) => {
                const newDataPoint = generateTelemetry();
                const updatedData = [...currentData, newDataPoint];
                if (updatedData.length > MAX_DATA_POINTS) {
                    updatedData.shift();
                }

                // Check for Critical Threshold
                if (newDataPoint.temperature > CRITICAL_TEMP && !isAlerting) {
                    setIsAlerting(true);
                    triggerAutomatedResolution(newDataPoint.temperature);
                } else if (newDataPoint.temperature <= CRITICAL_TEMP && isAlerting) {
                    setIsAlerting(false);
                }

                return updatedData;
            });
        }, 2000);

        return () => clearInterval(interval);
    }, [isAlerting]);

    const triggerAutomatedResolution = async (temp: number) => {
        try {
            const res = await fetch('/api/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: `Pasteurizer temperature high S7-1500 currently at ${temp}C` }),
            });
            const data = await res.json();
            setResolutionData(data.recommendations);
        } catch (e) {
            console.error("Resolution trigger failed", e);
        }
    };

    const currentStatus = data.length > 0 ? data[data.length - 1] : null;
    const isCritical = currentStatus && currentStatus.temperature > CRITICAL_TEMP;

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col p-8">
            <header className="mb-8">
                <h1 className="text-4xl font-extrabold text-[#005596]">Goose Digital IIoT</h1>
                <p className="text-lg text-[#6c757d]">Milk Pasteurizer Monitoring Console</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Status Card */}
                <div className={`col-span-1 p-6 rounded-2xl shadow-lg flex flex-col items-center justify-center text-white transition-colors duration-500 ${isCritical ? 'bg-[#ff8800] animate-pulse' : 'bg-[#10b981]'}`}>
                    {isCritical ? <AlertCircle className="w-16 h-16 mb-4" /> : <CheckCircle2 className="w-16 h-16 mb-4" />}
                    <h2 className="text-2xl font-bold">{isCritical ? 'CRITICAL ALERT' : 'SYSTEM OPTIMAL'}</h2>
                    {currentStatus && (
                        <div className="mt-4 text-center">
                            <p className="text-5xl font-black">{currentStatus.temperature.toFixed(1)}°C</p>
                            <p className="text-sm opacity-80 mt-1">Threshold: {CRITICAL_TEMP}°C</p>
                        </div>
                    )}
                </div>

                {/* Live Chart */}
                <div className="col-span-1 lg:col-span-2 bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                    <div className="flex items-center gap-2 mb-4">
                        <Thermometer className="text-[#005596] w-6 h-6" />
                        <h3 className="font-bold text-gray-800 text-xl">Real-Time Temperature Trace</h3>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                <XAxis dataKey="timestamp" stroke="#9CA3AF" fontSize={12} tickMargin={10} />
                                <YAxis domain={['auto', 'auto']} stroke="#9CA3AF" fontSize={12} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="temperature"
                                    stroke={isCritical ? "#ff8800" : "#005596"}
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6 }}
                                    isAnimationActive={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Ecosystem Action Card - Triggers only on Critical State */}
            {isCritical && resolutionData && (
                <div className="w-full bg-white rounded-2xl shadow-2xl border-l-8 border-[#ff8800] p-6 animate-in slide-in-from-bottom-8 duration-500">
                    <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <AlertCircle className="text-[#ff8800] w-6 h-6" />
                        Automated Resolution Plan Activated
                    </h3>
                    <p className="text-[#6c757d] mb-6">The EcosystemRouter has processed the critical temperature spike and located relevant resolutions.</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Goose Mart Integration */}
                        {resolutionData.products?.length > 0 && (
                            <div className="p-4 border border-gray-100 rounded-xl bg-gray-50 flex items-center justify-between">
                                <div>
                                    <h4 className="font-bold text-[#005596] flex items-center gap-2">
                                        <HardDrive className="w-5 h-5" /> Hardware Replacement
                                    </h4>
                                    <p className="text-sm text-gray-600 mt-1">{resolutionData.products[0].name} detected as faulty.</p>
                                </div>
                                <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="px-4 py-2 bg-[#005596] hover:bg-[#00447a] text-white text-sm font-bold rounded-lg transition-colors shadow-md whitespace-nowrap">
                                    Order Parts (Goose Mart)
                                </a>
                            </div>
                        )}

                        {/* HireMyEngineer Integration */}
                        {resolutionData.experts?.length > 0 && (
                            <div className="p-4 border border-gray-100 rounded-xl bg-gray-50 flex items-center justify-between">
                                <div>
                                    <h4 className="font-bold text-[#8b5cf6] flex items-center gap-2">
                                        <Users className="w-5 h-5" /> Emergency Consultant
                                    </h4>
                                    <p className="text-sm text-gray-600 mt-1">{resolutionData.experts[0].name} available for remote support.</p>
                                </div>
                                <a href="http://localhost:3003" target="_blank" rel="noreferrer" className="px-4 py-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-sm font-bold rounded-lg transition-colors shadow-md whitespace-nowrap">
                                    Alert Expert (HireMyEngineer)
                                </a>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
