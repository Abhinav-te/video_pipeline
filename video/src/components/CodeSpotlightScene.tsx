import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { useBrand } from '../context/BrandContext';
import { CodeIcon, SparklesIcon, CheckIcon } from './SvgIcons';

export interface CodeSpotlightSceneProps {
  scene: {
    title?: string;
    code?: string;
    code_snippet?: string;
    filename?: string;
    language?: string;
    highlight_lines?: number[];
    focus_phrase?: string;
    callout?: string;
    evidence_ids?: string[];
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

// Tokenizes a line of code into syntax highlighted React elements
const renderSyntaxLine = (line: string) => {
  if (!line) return <span>&nbsp;</span>;

  // Regex tokenizer matching comments, strings, keywords, numbers, punctuation, and identifiers
  const tokenRegex = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:const|let|var|import|from|export|default|async|await|return|function|class|if|else|try|catch|throw|new|typeof|yield)\b|\b(?:true|false|null|undefined)\b|\b\d+\b|[{}()[\].,;:+\-*/%=<>!&|]+|[a-zA-Z_$][a-zA-Z0-9_$]*|[^\s]+|\s+)/g;

  const parts = [];
  let match;
  let keyIdx = 0;

  while ((match = tokenRegex.exec(line)) !== null) {
    const token = match[0];
    keyIdx++;

    // Comments
    if (token.startsWith('//') || token.startsWith('/*')) {
      parts.push(<span key={keyIdx} style={{ color: '#64748b', fontStyle: 'italic' }}>{token}</span>);
    }
    // Strings
    else if (token.startsWith('"') || token.startsWith("'") || token.startsWith('`')) {
      parts.push(<span key={keyIdx} style={{ color: '#34d399' }}>{token}</span>);
    }
    // Keywords
    else if (/^(const|let|var|import|from|export|default|async|await|return|function|class|if|else|try|catch|throw|new|typeof|yield)$/.test(token)) {
      parts.push(<span key={keyIdx} style={{ color: '#c084fc', fontWeight: 600 }}>{token}</span>);
    }
    // Booleans / Literals
    else if (/^(true|false|null|undefined)$/.test(token)) {
      parts.push(<span key={keyIdx} style={{ color: '#f472b6', fontWeight: 600 }}>{token}</span>);
    }
    // Numbers
    else if (/^\d+$/.test(token)) {
      parts.push(<span key={keyIdx} style={{ color: '#fb923c' }}>{token}</span>);
    }
    // Methods / step.run
    else if (token === 'run' || token === 'step' || token === 'inngest' || token === 'createFunction') {
      parts.push(<span key={keyIdx} style={{ color: '#38bdf8', fontWeight: 700 }}>{token}</span>);
    }
    // Operators
    else if (/^[{}()[\].,;:+\-*/%=<>!&|]+$/.test(token)) {
      parts.push(<span key={keyIdx} style={{ color: '#94a3b8' }}>{token}</span>);
    }
    // Default identifiers
    else {
      parts.push(<span key={keyIdx} style={{ color: '#f1f5f9' }}>{token}</span>);
    }
  }

  return parts;
};

export const CodeSpotlightScene: React.FC<CodeSpotlightSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  const rawCode = scene?.code || scene?.code_snippet || `export const processOrder = inngest.createFunction(\n  { id: "process-order" },\n  { event: "order/created" },\n  async ({ event, step }) => {\n    const billing = await step.run("fetch-billing-data", async () => {\n      return await api.getBillingCustomer(event.data.userId);\n    });\n    await step.run("charge-customer", async () => {\n      return await api.chargeCustomer(billing.id, event.data.amount);\n    });\n  }\n);`;

  const lines = rawCode.split('\n');
  const filename = scene?.filename || 'process-order.ts';
  const highlightLines = new Set(scene?.highlight_lines || [5, 6, 7]);
  const calloutText = scene?.callout || scene?.focus_phrase || 'step.run checkpoints state and isolates retries';

  // Highlight pulse animation
  const pulseOpacity = interpolate(
    Math.sin((localFrame / 15) * Math.PI),
    [-1, 1],
    [0.18, 0.32]
  );

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: isWidescreen ? 'row' : 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: isWidescreen ? '40px' : '24px',
        padding: isWidescreen ? '30px 50px' : '20px 10px',
        boxSizing: 'border-box',
        fontFamily: brand.font_sans,
      }}
    >
      {/* Left/Main Column: Sleek Modern Dark Glass IDE Card */}
      <div
        style={{
          flex: isWidescreen ? '0 0 65%' : '1 1 auto',
          maxWidth: isWidescreen ? '1100px' : '960px',
          width: '100%',
          backgroundColor: '#0c0e17',
          borderRadius: '24px',
          border: '1.5px solid rgba(99, 102, 241, 0.3)',
          boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.9), 0 0 32px rgba(99, 102, 241, 0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backdropFilter: 'blur(20px)',
        }}
      >
        {/* Window Chrome Header */}
        <div
          style={{
            height: '48px',
            backgroundColor: '#111320',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 20px',
            boxSizing: 'border-box',
          }}
        >
          {/* Mac window dots */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ff5f56' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ffbd2e' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#27c93f' }} />
          </div>

          {/* Active File Tab */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '8px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#cbd5e1',
              fontFamily: brand.font_mono,
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            <CodeIcon size={16} color="#60a5fa" />
            {filename}
          </div>

          <div style={{ width: '40px' }} />
        </div>

        {/* Code Editor Body */}
        <div
          style={{
            padding: isWidescreen ? '26px 28px' : '20px 18px',
            fontFamily: brand.font_mono,
            fontSize: isWidescreen ? '18px' : '19px',
            lineHeight: 1.6,
            overflowX: 'hidden',
          }}
        >
          {lines.map((line, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = highlightLines.has(lineNum);

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: isHighlighted ? `rgba(99, 102, 241, ${pulseOpacity})` : 'transparent',
                  borderLeft: isHighlighted ? '3.5px solid #6366F1' : '3.5px solid transparent',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  opacity: isHighlighted ? 1 : 0.6,
                  transition: 'opacity 0.2s ease, background-color 0.2s ease',
                  position: 'relative',
                }}
              >
                {/* Line number */}
                <span
                  style={{
                    width: '36px',
                    color: isHighlighted ? '#a5b4fc' : '#475569',
                    fontSize: '13px',
                    userSelect: 'none',
                    fontWeight: isHighlighted ? 700 : 400,
                  }}
                >
                  {lineNum}
                </span>

                {/* Syntax highlighted line */}
                <div style={{ flex: 1, whiteSpace: 'pre' }}>
                  {renderSyntaxLine(line)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column (Widescreen) or Bottom Floating Card: Live Annotation Badge */}
      <div
        style={{
          flex: isWidescreen ? '0 0 30%' : 'none',
          width: isWidescreen ? 'auto' : '100%',
          maxWidth: isWidescreen ? '440px' : '960px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(17, 19, 28, 0.9)',
            borderRadius: '20px',
            border: '1.5px solid rgba(99, 102, 241, 0.4)',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.8), 0 0 24px rgba(99, 102, 241, 0.2)',
            padding: '24px 28px',
            backdropFilter: 'blur(16px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '8px',
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                border: '1px solid #6366F1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SparklesIcon size={16} color="#818cf8" />
            </div>
            <span
              style={{
                fontSize: '13px',
                fontWeight: 800,
                color: '#818cf8',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontFamily: brand.font_mono,
              }}
            >
              ACTIVE ISOLATION SCOPE
            </span>
          </div>

          <div
            style={{
              fontSize: isWidescreen ? '20px' : '22px',
              fontWeight: 700,
              color: '#ffffff',
              lineHeight: 1.35,
              marginBottom: '14px',
            }}
          >
            {calloutText}
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              color: '#34d399',
              fontWeight: 600,
            }}
          >
            <CheckIcon size={16} color="#34d399" />
            Automatic Memoization & Retry Guard
          </div>
        </div>
      </div>
    </div>
  );
};

export default CodeSpotlightScene;

