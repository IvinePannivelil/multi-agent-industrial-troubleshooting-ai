import React from 'react';
import { PlayCircle, CheckCircle2, Circle, GraduationCap, MonitorPlay, ArrowRight } from 'lucide-react';
import { EcosystemRouter } from '@goose/database';

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
    // Query EcosystemRouter dynamically for the course context
    const resolvedParams = await params;
    const contextQuery = `Need hardware for ${resolvedParams.id.replace('-', ' ')} physical lab`;
    const ecosystemData = await EcosystemRouter(contextQuery);
    const recommendedHardware = ecosystemData.recommendations.products;

    const syllabus = [
        { title: 'Module 1: Relay Logic Fundamentals', completed: true },
        { title: 'Module 2: TIA Portal Basics', completed: true },
        { title: 'Module 3: Advanced S7-1500 Functions', completed: false, current: true },
        { title: 'Module 4: CIP System Deployment', completed: false },
        { title: 'Module 5: Safety PLC Programming', completed: false },
        { title: 'Final Certification Exam', completed: false }
    ];

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Navbar */}
            <nav className="bg-[#005596] text-white p-4 shadow-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <GraduationCap className="w-8 h-8 text-[#10b981]" />
                        <span className="text-xl font-bold tracking-tight">Goose Elevate</span>
                    </div>
                    <div className="text-sm bg-white/10 px-4 py-2 rounded-full font-medium">
                        FRIAP Curriculum • S7-1500 Mastery
                    </div>
                </div>
            </nav>

            <main className="flex-grow max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Main Content Area */}
                <div className="lg:col-span-2 space-y-8">

                    {/* Video Player Placeholder */}
                    <div className="bg-black rounded-2xl aspect-video shadow-2xl relative overflow-hidden group flex items-center justify-center border-4 border-[#005596]/20">
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-8">
                            <h1 className="text-white text-3xl font-bold mb-2">Module 3: Advanced S7-1500 Functions</h1>
                            <p className="text-gray-300">Instructor: Senior Automation Architect</p>
                        </div>
                        <PlayCircle className="w-24 h-24 text-white/50 group-hover:text-white group-hover:scale-110 transition-all cursor-pointer z-10" />
                    </div>

                    <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">Virtual Training Lab</h2>
                            <p className="text-gray-500 text-sm mt-1">Practice TIA Portal logic without physical hardware.</p>
                        </div>
                        <button className="bg-[#10b981] hover:bg-[#0ea5e9] text-white px-8 py-3 rounded-xl font-bold transition-colors shadow-md flex items-center gap-2">
                            <MonitorPlay className="w-5 h-5" /> Launch Virtual PLC Lab
                        </button>
                    </div>

                    {/* Contextual Ecosystem Links - The Widget */}
                    {recommendedHardware.length > 0 && (
                        <div className="bg-gradient-to-r from-[#005596]/5 to-transparent p-6 rounded-2xl border-l-4 border-[#005596]">
                            <h3 className="text-lg font-bold text-[#005596] mb-4">Ecosystem Suggestion: Upgrade to a Physical Lab</h3>
                            <p className="text-gray-600 text-sm mb-4">
                                Ready to move beyond the virtual lab? Get the exact hardware required for this module directly from Goose Mart.
                            </p>
                            <div className="flex flex-wrap gap-4">
                                {recommendedHardware.map((hw: any) => (
                                    <div key={hw.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex items-center gap-4 hover:border-[#005596] transition-colors cursor-pointer">
                                        <div className="bg-gray-100 p-3 rounded-md">
                                            <span className="font-mono text-xs text-gray-500">{hw.modelNumber}</span>
                                        </div>
                                        <div>
                                            <span className="block font-bold text-gray-900">{hw.name}</span>
                                        </div>
                                        <ArrowRight className="w-4 h-4 text-[#005596] ml-4" />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                </div>

                {/* Syllabus Sidebar */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 h-fit sticky top-24">
                    <h3 className="text-lg font-extrabold text-gray-900 mb-6 uppercase tracking-wider text-sm border-b pb-4">
                        FRIAP Curriculum Syllabus
                    </h3>
                    <ul className="space-y-6">
                        {syllabus.map((item, idx) => (
                            <li key={idx} className={`flex items-start gap-4 ${item.completed ? 'text-gray-400' : 'text-gray-900'}`}>
                                {item.completed ? (
                                    <CheckCircle2 className="w-6 h-6 text-[#10b981] flex-shrink-0" />
                                ) : item.current ? (
                                    <div className="relative">
                                        <Circle className="w-6 h-6 text-[#005596] flex-shrink-0 animate-pulse" />
                                        <div className="absolute inset-0 m-auto w-2 h-2 bg-[#005596] rounded-full"></div>
                                    </div>
                                ) : (
                                    <Circle className="w-6 h-6 text-gray-300 flex-shrink-0" />
                                )}
                                <div>
                                    <span className={`block font-medium ${item.current ? 'font-bold text-[#005596]' : ''}`}>
                                        {item.title}
                                    </span>
                                    {item.current && (
                                        <span className="text-xs font-bold text-[#ff8800] mt-1 block">IN PROGRESS</span>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

            </main>
        </div>
    );
}
