// Starter chat sessions — seeded on first load so the sidebar isn't empty.
// These look like real prior conversations and give users a sense of what the assistant can do.

export const starterSessions = [
    {
        id: "s1",
        title: "S7-1500 CPU fault diagnosis",
        messages: [
            {
                id: "s1-w",
                role: "assistant",
                content: "Hello! I am Goose Sense, your Industrial AI Assistant. Ask me anything about PLCs, SCADA systems, industrial hardware, troubleshooting, or automation — I'm here to help."
            },
            {
                id: "s1-u1",
                role: "user",
                content: "My Siemens S7-1500 PLC is showing a STOP state after a power blip. BF LED is red. How do I recover it?"
            },
            {
                id: "s1-a1",
                role: "assistant",
                content: "A red BF (Bus Fault) LED combined with a STOP state after a power blip is a common scenario and usually means the CPU couldn't re-establish communication with one or more PROFIBUS/PROFINET devices on startup.\n\n**Steps to recover:**\n\n1. **Check TIA Portal diagnostics** — Go to Online > Accessible Devices and connect to the CPU. Open the diagnostics buffer (CPU Properties → Diagnostics). Look for the first fault entry logged right after the power event.\n\n2. **Force a cold restart** — In TIA Portal, switch the PLC to STOP, then back to RUN. If a specific module missed initialisation, this will re-trigger the startup sequence.\n\n3. **Check PROFINET device states** — Navigate to the network view and verify that all connected IO devices (ET200SP, drives, etc.) show a green status. A missing or faulted device will hold the CPU in STOP if 'Startup if expected config ≠ actual config' is unchecked.\n\n4. **Review the actual vs. expected config** — Go to Device Configuration and compare the hardware catalog entries to the physical rack. A firmware mismatch or missing module can cause a BF after a power event.\n\n5. **If the issue persists** — Check the 24V DC supply voltage to the CPU. A weak PSU that drops below 20.4V during startup can cause a corrupt startup sequence.\n\nWould you like me to walk you through reading the TIA Portal diagnostic buffer step by step?"
            }
        ]
    },
    {
        id: "s2",
        title: "PROFINET vs PROFIBUS comparison",
        messages: [
            {
                id: "s2-w",
                role: "assistant",
                content: "Hello! I am Goose Sense, your Industrial AI Assistant. Ask me anything about PLCs, SCADA systems, industrial hardware, troubleshooting, or automation — I'm here to help."
            },
            {
                id: "s2-u1",
                role: "user",
                content: "What is the difference between PROFINET and PROFIBUS? Which one should I use for a new project?"
            },
            {
                id: "s2-a1",
                role: "assistant",
                content: "Great question. Both are Siemens-led industrial fieldbus standards, but they target different eras and use cases:\n\n| Feature | PROFIBUS | PROFINET |\n|---|---|---|\n| Media | RS-485 copper with termination | Standard Ethernet (CAT5e/6) |\n| Speed | Up to 12 Mbit/s | 100 Mbit/s standard, 1 Gbit/s possible |\n| Topology | Linear bus (daisy-chain) | Star, ring, line — flexible |\n| Cycle time | ~1–10ms typical | <1ms with IRT (Isochronous Real-Time) |\n| Diagnostics | Limited, device-level | Rich — web-based, SNMP, detailed alarms |\n| Cable distance | Up to 200m @ 1Mbit/s | Standard Ethernet rules apply |\n| Integration | Legacy devices, drives | Drives, vision, safety, motion |\n\n**For new projects: use PROFINET.** \n\nPROFINET is Siemens' strategic standard going forward. It runs on standard Ethernet infrastructure, supports device-level web diagnostics, integrates with cloud/edge systems, and handles everything from basic IO to high-speed motion control (IRT mode). TIA Portal v17+ has excellent PROFINET commissioning tools.\n\nThe only reason to choose PROFIBUS today is if you are integrating with legacy devices that don't have a PROFINET interface, or expanding an existing PROFIBUS installation where a complete migration isn't feasible.\n\nDo you have specific devices in mind? I can advise on whether they support PROFINET natively."
            }
        ]
    },
    {
        id: "s3",
        title: "PID tuning for temperature loop",
        messages: [
            {
                id: "s3-w",
                role: "assistant",
                content: "Hello! I am Goose Sense, your Industrial AI Assistant. Ask me anything about PLCs, SCADA systems, industrial hardware, troubleshooting, or automation — I'm here to help."
            },
            {
                id: "s3-u1",
                role: "user",
                content: "How do I tune a PID controller for a pasteurizer temperature loop in TIA Portal?"
            },
            {
                id: "s3-a1",
                role: "assistant",
                content: "Tuning a temperature PID for a pasteurizer is a great use case — thermal processes are relatively slow, which actually makes them more forgiving to tune. Here's a structured approach using TIA Portal's built-in PID_Compact block:\n\n**Step 1 — Use PID_Compact FB**\nIn TIA Portal, insert a `PID_Compact` (FB 1) instance in your OB30 (cyclic interrupt, set to 100ms for temperature). This block handles auto-tuning, anti-windup, and output limiting natively.\n\n**Step 2 — Configure the block**\n- `Input`: Your temperature sensor (4-20mA → scaled to °C)\n- `Setpoint`: Your target pasteurisation temp (e.g. 72°C)\n- `Output`: Your control valve/heater (0–100%)\n- Enable `OutputUpperLimit` and `OutputLowerLimit` to protect the actuator\n\n**Step 3 — Pre-tuning (manual)**\nBring the process to a stable operating point ~60% of setpoint. Then run a step test — put the output at 50% and record how the temperature responds. Note:\n- **Dead time** (how long before temp starts rising)\n- **Process gain** (total °C rise / % output change)\n- **Time constant** (63% of total rise)\n\n**Step 4 — Auto-tuning in TIA Portal**\nRight-click the PID_Compact instance → `Start PID Tuning`. Set `Mode = 4` (self-tuning) and enable it. The block will run a relay feedback test and calculate P, I, D automatically. This typically takes 2–5 process time constants.\n\n**Step 5 — Fine-tune manually if needed**\n- Overshoot? Reduce Kp or increase Ti\n- Slow response? Increase Kp or reduce Ti\n- Oscillating? Reduce Kp, add Td carefully\n\nWant me to share the exact ladder / SCL code for the PID_Compact setup?"
            }
        ]
    }
];
