// Magik Terminal. Original shader, MIT license.
// Windows Terminal's documented pixel shader interface.
Texture2D shaderTexture : register(t0);
SamplerState samplerState : register(s0);
cbuffer PixelShaderSettings : register(b0) {
    float Time;
    float Scale;
    float2 Resolution;
    float4 Background;
};

float hash21(float2 p) {
    return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
}
float noise(float2 p) {
    float2 i = floor(p), f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    return lerp(lerp(hash21(i), hash21(i + float2(1, 0)), f.x),
                lerp(hash21(i + float2(0, 1)), hash21(i + 1.0), f.x), f.y);
}
float4 main(float4 pos : SV_POSITION, float2 uv : TEXCOORD) : SV_TARGET {
    float4 terminal = shaderTexture.Sample(samplerState, uv);
    float2 size = Resolution / max(Scale, 1.0);
    float2 px = uv * size;
    float2 edge = min(px, size - px);
    float3 amber = float3(240, 179, 74) / 255.0;
    float3 cyan = float3(59, 224, 200) / 255.0;
    float3 ink = float3(7, 7, 10) / 255.0;

    // Codex draws full-width rectangular prompt/message backgrounds. Round
    // their visible corners in the compositor without changing TUI input or
    // touching glyphs, colored diffs, or selection colors.
    const float radius = 10.0;
    float high = max(terminal.r, max(terminal.g, terminal.b));
    float low = min(terminal.r, min(terminal.g, terminal.b));
    // Support both linear and sRGB terminal render surfaces.
    bool panelPixel = high > 0.009 && high < 0.26 && high - low < 0.035;
    if (panelPixel && edge.x < radius) {
        float verticalDistance = radius;
        float3 outside = ink;
        [unroll]
        for (int d = 1; d <= 10; d++) {
            float2 delta = float2(0, float(d) / size.y);
            float3 above = shaderTexture.Sample(samplerState, uv - delta).rgb;
            float3 below = shaderTexture.Sample(samplerState, uv + delta).rgb;
            // Bright text cannot be mistaken for a panel boundary.
            float aboveHigh = max(above.r, max(above.g, above.b));
            float belowHigh = max(below.r, max(below.g, below.b));
            if (aboveHigh < high * 0.55 || belowHigh < high * 0.55) {
                outside = aboveHigh < belowHigh ? above : below;
                verticalDistance = min(verticalDistance, float(d));
            }
        }
        float2 corner = max(float2(radius - edge.x, radius - verticalDistance), 0.0);
        float coverage = 1.0 - smoothstep(radius - 0.7, radius + 0.7, length(corner));
        terminal.rgb = lerp(outside, terminal.rgb, coverage);
    }

    // Only decorate background pixels; retain text, selections and diffs.
    float distanceFromInk = length(terminal.rgb - ink);
    float backgroundMask = 1.0 - smoothstep(0.025, 0.14, distanceFromInk);
    float3 decoration = 0;

    // Two amber rails and turquoise HUD corner brackets.
    float verticalRail = 1.0 - smoothstep(0.6, 1.6, abs(edge.x - 7.0));
    float horizontalRail = 1.0 - smoothstep(0.6, 1.6, abs(edge.y - 7.0));
    float corners = saturate(verticalRail * (1.0 - step(49.0, edge.y)) +
                            horizontalRail * (1.0 - step(49.0, edge.x)));
    decoration += cyan * corners * 0.8;
    decoration += amber * verticalRail * 0.16;

    // Quantized, rising flames stay within 48 logical pixels of the sides.
    float2 cell = floor(px / 3.0) * 3.0;
    float flow = noise(float2(cell.y * 0.026 + Time * 0.8, cell.x * 0.04));
    flow += 0.45 * noise(float2(cell.y * 0.06 + Time * 1.2, cell.x * 0.08));
    float tongue = 8.0 + 32.0 * flow;
    float flame = (1.0 - smoothstep(tongue - 9.0, tongue + 2.0, edge.x));
    flame *= smoothstep(9.0, 20.0, edge.x);
    flame *= 0.24 + 0.10 * sin(cell.y * 0.03 + Time);
    decoration += lerp(amber, cyan, step(0.5, uv.x)) * flame;

    // Faint circuit grid in the outer gutter only.
    float grid = (1.0 - step(1.0, fmod(px.y, 24.0))) * (1.0 - smoothstep(30.0, 70.0, edge.x));
    decoration += cyan * grid * 0.07;
    return float4(saturate(terminal.rgb + decoration * backgroundMask), terminal.a);
}
