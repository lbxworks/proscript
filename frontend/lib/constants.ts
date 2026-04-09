export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export const LANGUAGE_OPTIONS = [
  "中文 (Chinese)",
  "English",
  "Español (Spanish)",
  "Português (Portuguese)",
  "Français (French)",
  "Deutsch (German)",
  "العربية (Arabic)",
  "日本語 (Japanese)",
];

export const MARKET_OPTIONS = [
  { code: "US", label: "United States" },
  { code: "CA", label: "Canada" },
  { code: "MX", label: "Mexico" },
  { code: "BR", label: "Brazil" },
  { code: "AR", label: "Argentina" },
  { code: "GB", label: "United Kingdom" },
  { code: "ES", label: "Spain" },
  { code: "DE", label: "Germany" },
  { code: "FR", label: "France" },
  { code: "IT", label: "Italy" },
  { code: "PT", label: "Portugal" },
  { code: "DK", label: "Denmark" },
  { code: "FI", label: "Finland" },
  { code: "SE", label: "Sweden" },
  { code: "NO", label: "Norway" },
  { code: "AE", label: "United Arab Emirates" },
  { code: "SA", label: "Saudi Arabia" },
];

export const PLATFORM_OPTIONS = [
  { value: "tiktok", label: "TikTok (International)" },
  { value: "youtube", label: "YouTube Shorts" },
  { value: "instagram", label: "Instagram Reels" },
  { value: "x", label: "X / Twitter" },
  { value: "reddit", label: "Reddit" },
  { value: "discord", label: "Discord" },
  { value: "douyin", label: "Douyin / WeChat Channels" },
];

export const DISTRIBUTION_OPTIONS = [
  { value: "organic", label: "Organic Post" },
  { value: "branded_content", label: "Branded Content" },
  { value: "paid_ads", label: "Paid Ads" },
];

export const PRODUCT_OPTIONS = [
  { value: "general", label: "General Merchandise" },
  { value: "beauty", label: "Beauty & Personal Care" },
  { value: "electronics", label: "Electronics" },
  { value: "fashion", label: "Fashion" },
  { value: "food_beverage", label: "Food & Beverage" },
  { value: "health_supplement", label: "Health / Supplement" },
];

export const DURATION_OPTIONS = [
  "15s (Flash)",
  "30s (Standard)",
  "60s (Immersive)",
  "3min (Deep Dive)",
];

export const LIBRARY_CATEGORY_OPTIONS = [
  { value: "platform_policy", label: "Platform Policy" },
  { value: "market_law", label: "Market Law" },
  { value: "brand_policy", label: "Brand Policy" },
  { value: "campaign_brief", label: "Campaign Brief" },
  { value: "brand_history", label: "Brand History" },
  { value: "technical_reference", label: "Technical Reference" },
];

export const LIBRARY_REGION_OPTIONS = [
  { value: "GLOBAL", label: "Global" },
  { value: "AMER", label: "Americas" },
  { value: "EU", label: "Europe" },
  { value: "APAC", label: "Asia Pacific" },
  { value: "MENA", label: "Middle East / Africa" },
  { value: "INTERNAL", label: "Internal" },
];

export const LIBRARY_LANGUAGE_OPTIONS = [
  { value: "en", label: "English" },
  { value: "zh", label: "Chinese" },
  { value: "es", label: "Spanish" },
  { value: "pt", label: "Portuguese" },
  { value: "de", label: "German" },
  { value: "fr", label: "French" },
  { value: "ar", label: "Arabic" },
  { value: "ja", label: "Japanese" },
];

export const LIBRARY_PRIORITY_OPTIONS = [
  { value: "P0", label: "P0" },
  { value: "P1", label: "P1" },
  { value: "P2", label: "P2" },
  { value: "P3", label: "P3" },
];
