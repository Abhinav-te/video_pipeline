import React, { createContext, useContext, useMemo } from 'react';

export interface ThemeTokens {
  // Canvas and surfaces
  canvas: string;
  surface: string;
  surface_elevated: string;
  surface_active: string;
  border_subtle: string;
  border_strong: string;

  // Typography colours
  text_primary: string;
  text_secondary: string;
  text_muted: string;
  text_disabled: string;

  // Semantic status colours
  status_success: string;
  status_warning: string;
  status_error: string;

  // Syntax highlighting colours (restrained monochrome-first code palette)
  syntax_keyword: string;
  syntax_string: string;
  syntax_function: string;
  syntax_type: string;
  syntax_number: string;
  syntax_comment: string;
  syntax_operator: string;
  syntax_punctuation: string;
  syntax_identifier: string;
}

export interface BrandTokens {
  company_name: string;
  logo_text: string;
  primary_color: string;
  secondary_color: string;
  warning_color: string;
  danger_color: string;
  bg_canvas: string;
  bg_surface: string;
  font_sans: string;
  font_mono: string;
  docs_url_display: string;
  theme: ThemeTokens;
}

export const DEFAULT_THEME: ThemeTokens = {
  canvas: '#090B0F',
  surface: '#11141A',
  surface_elevated: '#191D25',
  surface_active: '#222832',
  border_subtle: '#303640',
  border_strong: '#424A56',

  text_primary: '#F4F4F0',
  text_secondary: '#B4BAC4',
  text_muted: '#858D9A',
  text_disabled: '#606875',

  status_success: '#36A982',
  status_warning: '#E5A743',
  status_error: '#E15A5A',

  syntax_keyword: '#818CF8',
  syntax_string: '#6EE7B7',
  syntax_function: '#93C5FD',
  syntax_type: '#7DD3FC',
  syntax_number: '#FCD34D',
  syntax_comment: '#858D9A',
  syntax_operator: '#B4BAC4',
  syntax_punctuation: '#858D9A',
  syntax_identifier: '#F4F4F0',
};

export const DEFAULT_BRAND: BrandTokens = {
  company_name: 'Inngest',
  logo_text: 'INNGEST',
  primary_color: '#6366F1',
  secondary_color: '#10B981',
  warning_color: '#F59E0B',
  danger_color: '#EF4444',
  bg_canvas: '#090B0F',
  bg_surface: '#11141A',
  font_sans: 'Inter, system-ui, -apple-system, sans-serif',
  font_mono: 'JetBrains Mono, Fira Code, monospace',
  docs_url_display: 'inngest.com/docs/step-run',
  theme: DEFAULT_THEME,
};

const BrandContext = createContext<BrandTokens>(DEFAULT_BRAND);

export interface BrandProviderProps {
  brand?: (Partial<Omit<BrandTokens, 'theme'>> & { theme?: Partial<ThemeTokens> }) | null;
  children: React.ReactNode;
}

export const BrandProvider: React.FC<BrandProviderProps> = ({ brand, children }) => {
  const value = useMemo(() => {
    if (!brand) return DEFAULT_BRAND;
    return {
      ...DEFAULT_BRAND,
      ...brand,
      theme: {
        ...DEFAULT_THEME,
        ...(brand.theme || {}),
      },
    };
  }, [brand]);

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>;
};

export const useBrand = (): BrandTokens => useContext(BrandContext);
export const useTheme = (): ThemeTokens => useContext(BrandContext).theme;

export default BrandContext;

