const API_URL = process.env.REACT_APP_BACKEND_URL;

export const trackEvent = async (eventType, eventData = null) => {
  try {
    await fetch(`${API_URL}/api/analytics/track`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        event_type: eventType,
        event_data: eventData,
      }),
    });
  } catch (error) {
    console.error('Analytics tracking error:', error);
  }
};

// Predefined event types
export const EVENTS = {
  HERO_CTA_CLICK: 'hero_cta_click',
  DEMO_CLICK: 'demo_click',
  DOMAIN_HOVER: 'domain_hover',
  DOMAIN_SELECT: 'domain_select',
  FAQ_EXPAND: 'faq_expand',
  FASE2_CLICK: 'fase2_click',
  PRICING_CTA_CLICK: 'pricing_cta_click',
  REGISTER_OPEN: 'register_open',
  REGISTER_SUBMIT: 'register_submit',
  REGISTER_SUCCESS: 'register_success',
  NAV_CLICK: 'nav_click',
};
