import React, { createContext, useContext, useMemo } from 'react';

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
}

export const DEFAULT_BRAND: BrandTokens = {
  company_name: 'Inngest',
  logo_text: 'INNGEST',
  primary_color: '#6366F1',
  secondary_color: '#10B981',
  warning_color: '#F59E0B',
  danger_color: '#EF4444',
  bg_canvas: '#090A0F',
  bg_surface: '#11131C',
  font_sans: 'Inter, system-ui, -apple-system, sans-serif',
  font_mono: 'JetBrains Mono, Fira Code, monospace',
  docs_url_display: 'inngest.com/docs/step-run',
};

const BrandContext = createContext<BrandTokens>(DEFAULT_BRAND);

export interface BrandProviderProps {
  brand?: Partial<BrandTokens> | null;
  children: React.ReactNode;
}

export const BrandProvider: React.FC<BrandProviderProps> = ({ brand, children }) => {
  const value = useMemo(() => {
    if (!brand) return DEFAULT_BRAND;
    return {
      ...DEFAULT_BRAND,
      ...brand,
    };
  }, [brand]);

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>;
};

export const useBrand = (): BrandTokens => useContext(BrandContext);

export default BrandContext;

