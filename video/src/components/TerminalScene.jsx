import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneBadge } from './SceneBadge';
import { TerminalIcon, CheckIcon } from './SvgIcons';

// Blinking terminal cursor at ~2Hz (every 15 frames at 30fps)
export const TerminalCursor = () => {
  const frame = useCurrentFrame();
  const isVisible = Math.floor(frame / 15) % 2 === 0;

  return (
    <span
      style={{
        display: 'inline-block',
        width: '10px',
        height: '1.1em',
        backgroundColor: '#38bdf8',
        marginLeft: '4px',
        verticalAlign: 'text-bottom',
        borderRadius: '2px',
        opacity: isVisible ? 0.95 : 0.05,
        boxShadow: isVisible ? '0 0 8px rgba(56, 189, 248, 0.7)' : 'none',
        pointerEvents: 'none',
      }}
    />
  );
};

/**
 * TerminalScene (Phase A DevTool Primitive)
 * Authentic dark terminal window (zsh — 80x24) simulator:
 *   - macOS traffic lights + terminal title header
 *   - Animated typewriter typing of CLI commands ($ npm install ...)
 *   - Progressive reveal of stdout lines with duration/status badges
 *   - Dynamic font auto-scaling and zero text overflow
 */
export const TerminalScene = ({
  scene,
  sceneStartFrame = 0,
  nextSceneStartTime = null,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Normalize commands array
  const commandsData = React.useMemo(() => {
    if (Array.isArray(scene?.commands) && scene.commands.length > 0) {
      return scene.commands.map((c) => ({
        cmd: c.cmd || '',
        output: Array.isArray(c.output) ? c.output : (c.output ? [String(c.output)] : []),
        status: c.status || null,
      }));
    }

    // Fallback: parse code_snippet or code
    const rawSnippet = scene?.code_snippet || scene?.code || '$ npm install @acme/sdk\n+ @acme/sdk@2.0.0\n✓ Installed in 140ms';
    const lines = rawSnippet.split('\n');
    const cmds = [];
    let currentCmd = null;

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('$ ') || trimmed.startsWith('> ')) {
        if (currentCmd) cmds.push(currentCmd);
        currentCmd = {
          cmd: trimmed.replace(/^[$>]\s*/, ''),
          output: [],
          status: null,
        };
      } else if (trimmed.startsWith('✓') || trimmed.startsWith('✔') || trimmed.toLowerCase().includes('built in') || trimmed.toLowerCase().includes('installed in')) {
        if (currentCmd) {
          currentCmd.status = trimmed;
        } else {
          cmds.push({ cmd: 'run', output: [], status: trimmed });
        }
      } else {
        if (!currentCmd) {
          currentCmd = { cmd: 'run', output: [line], status: null };
        } else {
          currentCmd.output.push(line);
        }
      }
    });
    if (currentCmd) cmds.push(currentCmd);

    return cmds.length > 0 ? cmds : [{
      cmd: 'npm install @acme/edgecache@latest',
      output: [
        '+ @acme/edgecache@2.0.0',
        'added 1 package, audited 48 packages in 140ms',
        'found 0 vulnerabilities',
      ],
      status: '✓ Package verified & ready • 140ms',
    }];
  }, [scene]);

  // Calculate total characters and line metrics for font scaling
  const allLines = [];
  commandsData.forEach((c) => {
    allLines.push(`$ ${c.cmd}`);
    c.output.forEach((o) => allLines.push(String(o)));
    if (c.status) allLines.push(c.status);
  });

  const maxLineLen = Math.max(...allLines.map((l) => l.length), 0);
  const totalLineCount = allLines.length;

  // Dynamic font scaling
  let fontSize = 26;
  if (maxLineLen > 52 || totalLineCount > 12) {
    fontSize = 20;
  } else if (maxLineLen > 44 || totalLineCount > 10) {
    fontSize = 22;
  } else if (maxLineLen > 36 || totalLineCount > 8) {
    fontSize = 24;
  }

  // Animation timeline: typewriter typing speed = 2 chars per frame
  const relFrame = Math.max(0, frame - sceneStartFrame);
  const charsPerFrame = 1.6;

  // Distribute timing across commands
  let cumulativeFrame = 6; // brief initial delay

  const renderedCommands = commandsData.map((cmdItem, cIdx) => {
    const cmdLen = cmdItem.cmd.length;
    const typeDuration = Math.max(12, Math.round(cmdLen / charsPerFrame));
    const typeStart = cumulativeFrame;
    const typeEnd = typeStart + typeDuration;

    // Characters revealed so far
    let revealedChars = 0;
    if (relFrame >= typeStart) {
      revealedChars = Math.min(cmdLen, Math.floor((relFrame - typeStart) * charsPerFrame));
    }
    const isTypingActive = relFrame >= typeStart && relFrame <= typeEnd + 6;

    // Output reveal starts after typing completes
    const outputStart = typeEnd + 6;
    const outputLinesRevealed = [];
    cmdItem.output.forEach((outLine, oIdx) => {
      const lineRevealFrame = outputStart + oIdx * 5;
      if (relFrame >= lineRevealFrame) {
        outputLinesRevealed.push({ text: outLine, visible: true });
      }
    });

    const statusRevealFrame = outputStart + cmdItem.output.length * 5 + 4;
    const showStatus = Boolean(cmdItem.status && relFrame >= statusRevealFrame);

    cumulativeFrame = statusRevealFrame + 10;

    return {
      cmd: cmdItem.cmd,
      revealedChars,
      isTypingActive,
      typeStart,
      outputLines: outputLinesRevealed,
      status: cmdItem.status,
      showStatus,
      isStarted: relFrame >= typeStart,
    };
  });

  return (
    <div
      style={{
        backgroundColor: '#0c1017',
        borderRadius: '26px',
        border: '1.5px solid rgba(56, 189, 248, 0.28)',
        boxShadow: '0 32px 64px -16px rgba(0, 0, 0, 0.95), 0 0 32px rgba(56, 189, 248, 0.10)',
        width: '960px',
        height: 'fit-content',
        maxHeight: '1160px',
        overflow: 'hidden',
        boxSizing: 'border-box',
        transform: 'none',
        backfaceVisibility: 'hidden',
        position: 'relative',
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
        fontFamily: "'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, monospace",
        margin: 'auto 0',
      }}
    >
      {/* 1. macOS TERMINAL WINDOW HEADER (110px) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '90px',
          paddingBottom: '16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Traffic light window controls */}
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ff5f56', display: 'inline-block', boxShadow: '0 0 8px rgba(255,95,86,0.6)' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#ffbd2e', display: 'inline-block', boxShadow: '0 0 8px rgba(255,189,46,0.6)' }} />
          <span style={{ width: 14, height: 14, borderRadius: '50%', backgroundColor: '#27c93f', display: 'inline-block', boxShadow: '0 0 8px rgba(39,201,63,0.6)' }} />

          <div
            style={{
              marginLeft: '14px',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              padding: '6px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <TerminalIcon size={18} color="#38bdf8" />
            <span
              style={{
                fontSize: '20px',
                color: '#e2e8f0',
                fontWeight: '600',
                letterSpacing: '0.3px',
              }}
            >
              zsh — 80×24
            </span>
          </div>
        </div>

        {/* Scene Badge */}
        {scene?.badge ? (
          <SceneBadge badge={scene.badge} startFrame={sceneStartFrame} />
        ) : (
          <div
            style={{
              padding: '6px 14px',
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '8px',
              fontSize: '16px',
              color: '#38bdf8',
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}
          >
            CLI WORKFLOW
          </div>
        )}
      </div>

      {/* 2. TERMINAL BODY / CANVAS (1080px) */}
      <div
        style={{
          flex: 1,
          margin: '20px 0',
          backgroundColor: '#070a0f',
          borderRadius: '18px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          padding: '28px 24px',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          overflow: 'hidden',
          fontSize: `${fontSize}px`,
          lineHeight: 1.55,
        }}
      >
        {renderedCommands.map((item, idx) => {
          if (!item.isStarted) return null;

          const typedPart = item.cmd.slice(0, item.revealedChars);
          const isDoneTyping = item.revealedChars >= item.cmd.length;

          return (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {/* Command line */}
              <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap' }}>
                <span style={{ color: '#38bdf8', fontWeight: 800, marginRight: '10px', userSelect: 'none' }}>
                  $
                </span>
                <span style={{ color: '#f8fafc', fontWeight: 600, wordBreak: 'break-all' }}>
                  {typedPart}
                </span>
                {!isDoneTyping && <TerminalCursor />}
              </div>

              {/* Stdout lines */}
              {item.outputLines.map((outLine, oIdx) => (
                <div
                  key={oIdx}
                  style={{
                    color: '#94a3b8',
                    paddingLeft: '22px',
                    wordBreak: 'break-all',
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: '6px',
                  }}
                >
                  <span style={{ color: '#475569', userSelect: 'none' }}>›</span>
                  <span>{outLine.text}</span>
                </div>
              ))}

              {/* Status / Success Badge */}
              {item.showStatus && (
                <div
                  style={{
                    marginTop: '6px',
                    marginLeft: '22px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    backgroundColor: 'rgba(52, 211, 153, 0.12)',
                    border: '1px solid rgba(52, 211, 153, 0.35)',
                    borderRadius: '8px',
                    padding: '6px 14px',
                    color: '#34d399',
                    fontSize: `${Math.max(18, fontSize - 2)}px`,
                    fontWeight: 700,
                    width: 'fit-content',
                  }}
                >
                  <CheckIcon size={18} color="#34d399" />
                  <span>{item.status}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 3. TERMINAL COMPACT TECHNICAL STATUS BAR */}
      <div
        style={{
          height: '56px',
          backgroundColor: '#0a0e17',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '0 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
          marginTop: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#34d399', display: 'inline-block', boxShadow: '0 0 8px rgba(52,211,153,0.7)' }} />
          <span style={{ fontSize: '16px', color: '#e2e8f0', fontWeight: 700, letterSpacing: '0.5px' }}>
            CLI RUNTIME ACTIVE
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '15px', color: '#94a3b8', fontFamily: 'monospace' }}>
          <span>BUFFER: 80×24</span>
          <span>•</span>
          <span>NODE v20.11.0</span>
          <span>•</span>
          <span style={{ color: '#34d399', fontWeight: 'bold' }}>EXIT 0 (140ms)</span>
        </div>
      </div>
    </div>
  );
};

export default TerminalScene;

