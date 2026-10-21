import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
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
    callout?: string | { title?: string; body?: string };
    proof_card?: { title?: string; body?: string; tag?: string };
    badge?: { text?: string };
    evidence_ids?: string[];
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

// Comprehensive TypeScript Syntax Tokenizer
interface Token {
  type: 'comment' | 'string' | 'keyword' | 'type' | 'number' | 'call' | 'property' | 'operator' | 'punctuation' | 'identifier' | 'whitespace';
  value: string;
}

const tokenizeTypeScript = (code: string): Token[] => {
  const tokens: Token[] = [];
  const regex = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:const|let|var|import|from|export|default|async|await|return|function|class|new|if|else|try|catch|finally|throw|type|interface|extends|implements|as|in|of|typeof|keyof|readonly|static|get|set)\b|\b(?:string|number|boolean|any|void|unknown|never|Record|Promise|Array|true|false|null|undefined)\b|\b\d+(?:\.\d+)?\b|[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*\()|[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*:)|(=>|===|!==|==|!=|<=|>=|&&|\|\||[+\-*/%=<>!&|?:]+)|([{}()[\].,;])|[a-zA-Z_$][a-zA-Z0-9_$]*|[^\S\r\n]+|\n|[^\s\w]+)/g;

  let match;
  while ((match = regex.exec(code)) !== null) {
    const val = match[0];
    if (val.startsWith('//') || val.startsWith('/*')) {
      tokens.push({ type: 'comment', value: val });
    } else if (val.startsWith('"') || val.startsWith("'") || val.startsWith('`')) {
      tokens.push({ type: 'string', value: val });
    } else if (/^(const|let|var|import|from|export|default|async|await|return|function|class|new|if|else|try|catch|finally|throw|type|interface|extends|implements|as|in|of|typeof|keyof|readonly|static|get|set)$/.test(val)) {
      tokens.push({ type: 'keyword', value: val });
    } else if (/^(string|number|boolean|any|void|unknown|never|Record|Promise|Array|true|false|null|undefined)$/.test(val)) {
      tokens.push({ type: 'type', value: val });
    } else if (/^\d+(?:\.\d+)?$/.test(val)) {
      tokens.push({ type: 'number', value: val });
    } else if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(val) && code.slice(regex.lastIndex).trim().startsWith('(')) {
      tokens.push({ type: 'call', value: val });
    } else if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(val) && code.slice(regex.lastIndex).trim().startsWith(':') && !code.slice(regex.lastIndex).trim().startsWith('::')) {
      tokens.push({ type: 'property', value: val });
    } else if (/^(=>|===|!==|==|!=|<=|>=|&&|\|\||[+\-*/%=<>!&|?:]+)$/.test(val)) {
      tokens.push({ type: 'operator', value: val });
    } else if (/^[{}()[\].,;]$/.test(val)) {
      tokens.push({ type: 'punctuation', value: val });
    } else if (/^[^\S\r\n]+$/.test(val) || val === '\n') {
      tokens.push({ type: 'whitespace', value: val });
    } else {
      tokens.push({ type: 'identifier', value: val });
    }
  }

  return tokens;
};

const renderSyntaxLine = (line: string) => {
  if (!line) return <span>&nbsp;</span>;
  const tokens = tokenizeTypeScript(line);

  return tokens.map((token, idx) => {
    switch (token.type) {
      case 'comment':
        return <span key={idx} style={{ color: '#64748b', fontStyle: 'italic' }}>{token.value}</span>;
      case 'string':
        return <span key={idx} style={{ color: '#34d399' }}>{token.value}</span>;
      case 'keyword':
        return <span key={idx} style={{ color: '#c084fc', fontWeight: 600 }}>{token.value}</span>;
      case 'type':
        return <span key={idx} style={{ color: '#38bdf8', fontWeight: 600 }}>{token.value}</span>;
      case 'number':
        return <span key={idx} style={{ color: '#fb923c' }}>{token.value}</span>;
      case 'call':
        return <span key={idx} style={{ color: '#60a5fa', fontWeight: 600 }}>{token.value}</span>;
      case 'property':
        return <span key={idx} style={{ color: '#e2e8f0', fontWeight: 500 }}>{token.value}</span>;
      case 'operator':
        return <span key={idx} style={{ color: '#f472b6' }}>{token.value}</span>;
      case 'punctuation':
        return <span key={idx} style={{ color: '#94a3b8' }}>{token.value}</span>;
      case 'whitespace':
        return <span key={idx}>{token.value}</span>;
      default:
        return <span key={idx} style={{ color: '#f1f5f9' }}>{token.value}</span>;
    }
  });
};

export const CodeSpotlightScene: React.FC<CodeSpotlightSceneProps> = ({
  scene,
  sceneStartFrame = 0,
  isWidescreen = false,
}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  const localFrame = Math.max(0, frame - sceneStartFrame);

  const rawCode = scene?.code || scene?.code_snippet || '';
  if (!rawCode.trim()) {
    throw new Error(
      `[CodeSpotlightScene] Validation Error: 'code' or 'code_snippet' is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }

  const lines = rawCode.split('\n');
  const filename = scene?.filename || 'snippet.ts';
  const highlightLines = new Set(scene?.highlight_lines || []);

  const calloutRaw = scene?.callout;
  const calloutText = typeof calloutRaw === 'string'
    ? calloutRaw
    : (calloutRaw?.body || scene?.focus_phrase || scene?.title || '');

  const badgeText = scene?.badge?.text || (scene?.focus_phrase ? `FOCUS: ${scene.focus_phrase}` : (scene?.title || 'CODE SPOTLIGHT'));
  const proofText = scene?.proof_card?.body || (scene?.focus_phrase ? `Verified syntax: ${scene.focus_phrase}` : '');

  // Calculate dynamic font size based on max line length to prevent horizontal clipping
  const maxLineLength = Math.max(...lines.map((l) => l.length), 1);
  const availableCodeWidth = isWidescreen ? 1120 : 860;
  
  // Monospace character width ratio is roughly 0.58-0.61 of font size
  const computedFontSize = Math.floor(availableCodeWidth / (maxLineLength * 0.59));
  // Target >= 26px at 1080p widescreen, scaling down smoothly if lines are extra long
  const fontSize = isWidescreen
    ? Math.max(20, Math.min(27, computedFontSize))
    : Math.max(18, Math.min(23, computedFontSize));

  // Check if any line overflows safe bounds
  const estimatedLineWidth = maxLineLength * fontSize * 0.59;
  if (estimatedLineWidth > availableCodeWidth + 180) {
    throw new Error(
      `[CodeSpotlightScene] Line width overflow: line length ${maxLineLength} at ${fontSize}px exceeds available container width (${availableCodeWidth}px).`
    );
  }

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
        padding: isWidescreen ? '30px 40px' : '20px 10px',
        boxSizing: 'border-box',
        fontFamily: brand.font_sans,
      }}
    >
      {/* Main Column: Dark Glass IDE Card */}
      <div
        style={{
          flex: isWidescreen ? '0 0 68%' : '1 1 auto',
          maxWidth: isWidescreen ? '1180px' : '960px',
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
          {/* Window action dots */}
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
              fontSize: '14px',
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
            fontSize: `${fontSize}px`,
            lineHeight: 1.55,
            overflowX: 'visible',
            boxSizing: 'border-box',
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
                  opacity: (highlightLines.size === 0 || isHighlighted) ? 1.0 : 0.55,
                  transition: 'opacity 0.2s ease, background-color 0.2s ease',
                  position: 'relative',
                  whiteSpace: 'pre',
                }}
              >
                {/* Line number */}
                <span
                  style={{
                    width: '38px',
                    minWidth: '38px',
                    color: isHighlighted ? '#a5b4fc' : '#475569',
                    fontSize: `${Math.max(13, fontSize - 10)}px`,
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

      {/* Right Column (Widescreen) or Bottom Annotation Card */}
      <div
        style={{
          flex: isWidescreen ? '0 0 28%' : 'none',
          width: isWidescreen ? 'auto' : '100%',
          maxWidth: isWidescreen ? '420px' : '960px',
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
              {badgeText}
            </span>
          </div>

          <div
            style={{
              fontSize: isWidescreen ? '20px' : '22px',
              fontWeight: 700,
              color: '#ffffff',
              lineHeight: 1.35,
              marginBottom: proofText ? '14px' : '0px',
            }}
          >
            {calloutText}
          </div>

          {proofText ? (
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
              {proofText}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default CodeSpotlightScene;
