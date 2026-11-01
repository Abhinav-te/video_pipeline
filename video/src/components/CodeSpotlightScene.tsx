import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { useBrand, ThemeTokens } from '../context/BrandContext';
import { CodeIcon, SparklesIcon, LightningIcon } from './SvgIcons';

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
    badge?: { text?: string; type?: string; label?: string };
    evidence_ids?: string[];
    domain?: string;
    explanation?: string;
    description?: string;
  };
  sceneStartFrame?: number;
  isWidescreen?: boolean;
}

// Comprehensive TypeScript Syntax Tokenizer
interface Token {
  type:
    | 'comment'
    | 'string'
    | 'keyword'
    | 'type'
    | 'number'
    | 'call'
    | 'property'
    | 'operator'
    | 'punctuation'
    | 'identifier'
    | 'whitespace';
  value: string;
}

const cleanProse = (text?: string): string => {
  if (!text) return '';
  return text.replace(/^#+\s*/gm, '').replace(/\*\*(.*?)\*\*/g, '$1').trim();
};

const normalizeForComparison = (text?: string): string => {
  return (text || '').toLowerCase().replace(/[^a-z0-9]/g, '');
};

const tokenizeTypeScript = (code: string): Token[] => {
  const tokens: Token[] = [];
  const regex =
    /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:const|let|var|import|from|export|default|async|await|return|function|class|new|if|else|try|catch|finally|throw|type|interface|extends|implements|as|in|of|typeof|keyof|readonly|static|get|set)\b|\b(?:string|number|boolean|any|void|unknown|never|Record|Promise|Array|true|false|null|undefined)\b|\b\d+(?:\.\d+)?\b|[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*\()|[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*:)|(=>|===|!==|==|!=|<=|>=|&&|\|\||[+\-*/%=<>!&|?:]+)|([{}()[\].,;])|[a-zA-Z_$][a-zA-Z0-9_$]*|[^\S\r\n]+|\n|[^\s\w]+)/g;

  let match;
  while ((match = regex.exec(code)) !== null) {
    const val = match[0];
    if (val.startsWith('//') || val.startsWith('/*')) {
      tokens.push({ type: 'comment', value: val });
    } else if (val.startsWith('"') || val.startsWith("'") || val.startsWith('`')) {
      tokens.push({ type: 'string', value: val });
    } else if (
      /^(const|let|var|import|from|export|default|async|await|return|function|class|new|if|else|try|catch|finally|throw|type|interface|extends|implements|as|in|of|typeof|keyof|readonly|static|get|set)$/.test(
        val
      )
    ) {
      tokens.push({ type: 'keyword', value: val });
    } else if (
      /^(string|number|boolean|any|void|unknown|never|Record|Promise|Array|true|false|null|undefined)$/.test(
        val
      )
    ) {
      tokens.push({ type: 'type', value: val });
    } else if (/^\d+(?:\.\d+)?$/.test(val)) {
      tokens.push({ type: 'number', value: val });
    } else if (
      /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(val) &&
      code.slice(regex.lastIndex).trim().startsWith('(')
    ) {
      tokens.push({ type: 'call', value: val });
    } else if (
      /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(val) &&
      code.slice(regex.lastIndex).trim().startsWith(':') &&
      !code.slice(regex.lastIndex).trim().startsWith('::')
    ) {
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

const renderSyntaxLine = (line: string, theme: ThemeTokens) => {
  if (!line) return <span>&nbsp;</span>;
  const tokens = tokenizeTypeScript(line);

  return tokens.map((token, idx) => {
    switch (token.type) {
      case 'comment':
        return (
          <span key={idx} style={{ color: theme.syntax_comment, fontStyle: 'italic' }}>
            {token.value}
          </span>
        );
      case 'string':
        return (
          <span key={idx} style={{ color: theme.syntax_string }}>
            {token.value}
          </span>
        );
      case 'keyword':
        return (
          <span key={idx} style={{ color: theme.syntax_keyword, fontWeight: 600 }}>
            {token.value}
          </span>
        );
      case 'type':
        return (
          <span key={idx} style={{ color: theme.syntax_type, fontWeight: 600 }}>
            {token.value}
          </span>
        );
      case 'number':
        return (
          <span key={idx} style={{ color: theme.syntax_number }}>
            {token.value}
          </span>
        );
      case 'call':
        return (
          <span key={idx} style={{ color: theme.syntax_function, fontWeight: 600 }}>
            {token.value}
          </span>
        );
      case 'property':
        return (
          <span key={idx} style={{ color: '#E2E8F0', fontWeight: 500 }}>
            {token.value}
          </span>
        );
      case 'operator':
        return (
          <span key={idx} style={{ color: theme.syntax_operator }}>
            {token.value}
          </span>
        );
      case 'punctuation':
        return (
          <span key={idx} style={{ color: theme.syntax_punctuation }}>
            {token.value}
          </span>
        );
      case 'whitespace':
        return <span key={idx}>{token.value}</span>;
      default:
        return (
          <span key={idx} style={{ color: theme.syntax_identifier }}>
            {token.value}
          </span>
        );
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
  const theme = brand.theme;
  const localFrame = Math.max(0, frame - sceneStartFrame);

  const rawCode = scene?.code || scene?.code_snippet || '';
  if (!rawCode.trim()) {
    throw new Error(
      `[CodeSpotlightScene] Validation Error: 'code' or 'code_snippet' is required and must not be empty. Scene: "${scene?.title || 'untitled'}"`
    );
  }

  const lines = rawCode.split('\n');
  const filename = scene?.filename || 'snippet.ts';
  const language = scene?.language?.toUpperCase() || 'TYPESCRIPT';
  const highlightLines = new Set<number>(scene?.highlight_lines || []);

  const headline = cleanProse(scene?.title || 'Code Implementation');
  const headlineNorm = normalizeForComparison(headline);

  // Derive a clean, contextual category label without title repetition
  const deriveCategoryLabel = (): string => {
    if (scene?.badge?.label) return cleanProse(scene.badge.label).toUpperCase();
    if (scene?.badge?.type) {
      const t = scene.badge.type.toLowerCase();
      if (t === 'code') return 'CODE IMPLEMENTATION';
      if (t === 'accent') return 'CORE PRIMITIVE';
      if (t === 'success') return 'VERIFIED BEHAVIOR';
      return t.toUpperCase();
    }
    if (scene?.domain) {
      const d = scene.domain.toLowerCase();
      if (d === 'code') return 'CODE IMPLEMENTATION';
      return d.toUpperCase();
    }
    const rawBadgeText = scene?.badge?.text;
    if (rawBadgeText) {
      const clean = cleanProse(rawBadgeText);
      const cleanNorm = normalizeForComparison(clean);
      if (clean.length <= 22 && cleanNorm !== headlineNorm) {
        return clean.toUpperCase();
      }
    }
    return 'CODE IMPLEMENTATION';
  };

  const categoryLabel = deriveCategoryLabel();

  // Evaluate genuine supporting content (zero fake verification strings)
  const rawCallout = scene?.callout;
  const calloutBody = cleanProse(typeof rawCallout === 'string' ? rawCallout : rawCallout?.body);
  const calloutTitle = cleanProse(typeof rawCallout === 'object' ? rawCallout?.title : undefined);
  const explanation = cleanProse(scene?.explanation || scene?.description);
  const proofCard = scene?.proof_card;
  const focusPhrase = cleanProse(scene?.focus_phrase);

  const hasExplicitCallout = Boolean(calloutBody && normalizeForComparison(calloutBody) !== headlineNorm);
  const hasExplanation = Boolean(explanation && normalizeForComparison(explanation) !== headlineNorm);
  const hasProofCard = Boolean(proofCard?.body && normalizeForComparison(proofCard.body) !== headlineNorm);
  const hasFocusCard = Boolean(focusPhrase && normalizeForComparison(focusPhrase) !== headlineNorm);

  const hasSupportingContent = hasExplicitCallout || hasExplanation || hasProofCard || hasFocusCard;

  // Resolve supporting card display data
  const resolveSupportingData = () => {
    if (!hasSupportingContent) return null;

    let tag = 'PRIMITIVE FOCUS';
    let tagColor = '#93C5FD';
    let title = focusPhrase ? `${focusPhrase}()` : 'Target Operation';
    let body: string | null = null;
    let provenance: string | null = null;

    if (hasProofCard) {
      const isObserved = proofCard?.tag === 'observed_execution';
      tag = isObserved ? 'OBSERVED EXECUTION' : 'DOCUMENTED SPECIFICATION';
      tagColor = isObserved ? theme.status_success : theme.status_warning;
      title = cleanProse(proofCard?.title) || 'Specification Details';
      body = cleanProse(proofCard?.body);
      provenance = isObserved ? 'Verified against traceable execution artifact' : 'Documented in primary official reference';
    } else if (hasExplicitCallout) {
      tag = calloutTitle ? calloutTitle.toUpperCase() : 'CODE CONTEXT';
      tagColor = '#93C5FD';
      title = calloutTitle || (focusPhrase ? `${focusPhrase}()` : 'Operation Focus');
      body = calloutBody;
    } else if (hasExplanation) {
      tag = 'KEY BEHAVIOR';
      tagColor = '#93C5FD';
      title = focusPhrase ? `${focusPhrase}()` : 'Implementation Note';
      body = explanation;
    } else if (hasFocusCard) {
      tag = 'PRIMITIVE FOCUS';
      tagColor = '#93C5FD';
      title = `${focusPhrase}()`;
      if (highlightLines.size > 0) {
        const sortedLines = Array.from(highlightLines).sort((a, b) => a - b);
        body = `Scoped execution within lines ${sortedLines[0]}–${sortedLines[sortedLines.length - 1]} of ${filename}`;
      } else {
        body = `Isolated step checkpoint definition in ${filename}`;
      }
    }

    const citations = scene?.evidence_ids && scene.evidence_ids.length > 0 ? scene.evidence_ids.join(', ') : null;

    return { tag, tagColor, title, body, provenance, citations };
  };

  const supportingData = resolveSupportingData();

  // Dynamic code font sizing and responsive layout ratios
  const maxLineLength = Math.max(...lines.map((l) => l.length), 1);
  const isLongCode = maxLineLength > 65;

  // Responsive code font sizing (agreed target 22-26px):
  // 16:9 Widescreen: 24px base (22px for tall snippets > 14 lines) balances crisp readability with safe headroom.
  // 9:16 Vertical: 22px base preserves > 60px safe clearance above bottom subtitles, preventing card collision.
  const lineCount = lines.length;
  const baseFontSize = isWidescreen ? (lineCount > 14 ? 22 : 24) : 22;
  const fontSize = baseFontSize;

  const ideFlex = isWidescreen
    ? hasSupportingContent
      ? '0 0 74%'
      : '1 1 100%'
    : '1 1 auto';

  const ideMaxWidth = isWidescreen
    ? hasSupportingContent
      ? '1260px'
      : '1440px'
    : '960px';

  const sideFlex = isWidescreen
    ? hasSupportingContent
      ? '0 0 26%'
      : 'none'
    : 'none';

  const sideMaxWidth = isWidescreen
    ? '400px'
    : '960px';

  // Smooth entrance interpolation
  const titleOpacity = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleY = interpolate(localFrame, [0, 8], [10, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageOpacity = interpolate(localFrame, [2, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stageY = interpolate(localFrame, [2, 10], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isWidescreen ? '16px 40px' : '20px 16px',
        boxSizing: 'border-box',
        fontFamily: brand.font_sans,
      }}
    >
      {/* Level 1 & 2: Restrained Scene Heading & Contextual Pill */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          marginBottom: isWidescreen ? '20px' : '22px',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 14px',
            borderRadius: '999px',
            backgroundColor: 'rgba(147, 197, 253, 0.08)',
            border: '1px solid rgba(147, 197, 253, 0.22)',
            color: '#93C5FD',
            fontSize: isWidescreen ? '13px' : '13px',
            fontWeight: 700,
            fontFamily: brand.font_mono,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: '12px',
          }}
        >
          <SparklesIcon size={13} color="#93C5FD" />
          {categoryLabel}
        </div>

        <h1
          style={{
            fontSize: isWidescreen ? '34px' : '36px',
            fontWeight: 800,
            color: theme.text_primary,
            lineHeight: 1.25,
            letterSpacing: '-0.02em',
            margin: 0,
            maxWidth: isWidescreen ? '1320px' : '920px',
            textShadow: '0 4px 16px rgba(0, 0, 0, 0.85)',
          }}
        >
          {headline}
        </h1>
      </div>

      {/* Main Visual Stage: Code Editor Panel & Supporting Panel */}
      <div
        style={{
          width: '100%',
          maxWidth: isWidescreen ? '1580px' : '960px',
          display: 'flex',
          flexDirection: isWidescreen ? 'row' : 'column',
          alignItems: isWidescreen ? 'flex-start' : 'center',
          justifyContent: 'center',
          gap: isWidescreen ? '28px' : '20px',
          opacity: stageOpacity,
          transform: `translateY(${stageY}px)`,
          boxSizing: 'border-box',
        }}
      >
        {/* Primary Code Editor Window */}
        <div
          style={{
            flex: ideFlex,
            maxWidth: ideMaxWidth,
            width: '100%',
            backgroundColor: theme.surface_elevated,
            borderRadius: '16px',
            border: `1px solid ${theme.border_subtle}`,
            boxShadow: '0 24px 48px -12px rgba(0, 0, 0, 0.8)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            boxSizing: 'border-box',
          }}
        >
          {/* Editor Header Bar */}
          <div
            style={{
              height: '42px',
              backgroundColor: '#141720',
              borderBottom: `1px solid ${theme.border_subtle}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 18px',
              boxSizing: 'border-box',
            }}
          >
            {/* Window action indicators (subtle, restrained) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(239, 68, 68, 0.65)',
                }}
              />
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(245, 158, 11, 0.65)',
                }}
              />
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(16, 185, 129, 0.65)',
                }}
              />
            </div>

            {/* Active File Tab */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 12px',
                borderRadius: '6px',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: '#E2E8F0',
                fontFamily: brand.font_mono,
                fontSize: '13px',
                fontWeight: 600,
              }}
            >
              <CodeIcon size={14} color="#93C5FD" />
              {filename}
            </div>

            {/* Language Tag */}
            <span
              style={{
                fontFamily: brand.font_mono,
                fontSize: '11px',
                fontWeight: 600,
                color: theme.text_muted,
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}
            >
              {language}
            </span>
          </div>

          {/* Code Editor Body */}
          <div
            style={{
              padding: isWidescreen ? '22px 24px' : '18px 16px',
              fontFamily: brand.font_mono,
              fontSize: `${fontSize}px`,
              lineHeight: 1.55,
              overflowX: 'visible',
              boxSizing: 'border-box',
              backgroundColor: '#161922',
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
                    alignItems: 'flex-start',
                    backgroundColor: isHighlighted ? 'rgba(96, 165, 250, 0.08)' : 'transparent',
                    borderLeft: isHighlighted ? '3px solid rgba(96, 165, 250, 0.75)' : '3px solid transparent',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    opacity: highlightLines.size === 0 || isHighlighted ? 1.0 : 0.62,
                    transition: 'opacity 0.2s ease, background-color 0.2s ease',
                    position: 'relative',
                  }}
                >
                  {/* Line Number */}
                  <span
                    style={{
                      width: '38px',
                      minWidth: '38px',
                      color: isHighlighted ? '#93C5FD' : theme.text_disabled,
                      fontSize: `${Math.max(12, fontSize - 8)}px`,
                      userSelect: 'none',
                      fontWeight: isHighlighted ? 700 : 400,
                      lineHeight: 1.55,
                    }}
                  >
                    {lineNum}
                  </span>

                  {/* Syntax Highlighted Line */}
                  <div
                    style={{
                      flex: 1,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word',
                      lineHeight: 1.5,
                      textIndent: '-1.5em',
                      paddingLeft: '1.5em',
                    }}
                  >
                    {renderSyntaxLine(line, theme)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Supporting Information Panel (rendered only when meaningful data exists) */}
        {hasSupportingContent && supportingData ? (
          <div
            style={{
              flex: sideFlex,
              width: isWidescreen ? 'auto' : '100%',
              maxWidth: sideMaxWidth,
              backgroundColor: theme.surface,
              borderRadius: '16px',
              border: `1px solid ${theme.border_subtle}`,
              boxShadow: '0 20px 40px -8px rgba(0, 0, 0, 0.7)',
              padding: isWidescreen ? '22px 24px' : '18px 20px',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              boxSizing: 'border-box',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Top Accent Line */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '3px',
                backgroundColor: supportingData.tagColor,
                opacity: 0.85,
              }}
            />

            {/* Badge Header Row */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '14px',
              }}
            >
              <div
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(147, 197, 253, 0.12)',
                  border: '1px solid rgba(147, 197, 253, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <LightningIcon size={14} color={supportingData.tagColor} />
              </div>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: supportingData.tagColor,
                  letterSpacing: '0.07em',
                  textTransform: 'uppercase',
                  fontFamily: brand.font_mono,
                }}
              >
                {supportingData.tag}
              </span>
            </div>

            {/* Primary Heading */}
            <div
              style={{
                fontSize: isWidescreen ? '20px' : '20px',
                fontWeight: 700,
                color: theme.text_primary,
                lineHeight: 1.35,
                fontFamily: brand.font_sans,
                marginBottom: supportingData.body ? '10px' : '0px',
              }}
            >
              {supportingData.title}
            </div>

            {/* Secondary Body / Explanation */}
            {supportingData.body ? (
              <div
                style={{
                  fontSize: isWidescreen ? '15px' : '14px',
                  color: theme.text_secondary,
                  lineHeight: 1.5,
                  marginBottom: supportingData.provenance || supportingData.citations ? '14px' : '0px',
                }}
              >
                {supportingData.body}
              </div>
            ) : null}

            {/* Provenance or Source Citation Footer */}
            {supportingData.provenance ? (
              <div
                style={{
                  fontSize: '13px',
                  color: theme.text_muted,
                  lineHeight: 1.45,
                  borderTop: `1px solid ${theme.border_subtle}`,
                  paddingTop: '10px',
                  marginTop: '4px',
                }}
              >
                {supportingData.provenance}
              </div>
            ) : null}

            {supportingData.citations ? (
              <div
                style={{
                  fontSize: '12px',
                  color: theme.text_disabled,
                  fontFamily: brand.font_mono,
                  letterSpacing: '0.04em',
                  borderTop: supportingData.provenance ? 'none' : `1px solid ${theme.border_subtle}`,
                  paddingTop: supportingData.provenance ? '4px' : '10px',
                  marginTop: supportingData.provenance ? '0px' : '4px',
                }}
              >
                Citation: {supportingData.citations}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default CodeSpotlightScene;
