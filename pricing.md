# Pricing & Strategy Guide: Video Generation (Gemini vs Runway)

This guide outlines the costs and performance tradeoffs between using the Google Gemini (Veo) API and **Runway Gen-3 Alpha** for your ad generation workflow.

## 1. Google Gemini (Veo) Pricing
Gemini Veo is the current engine used in your codebase (`veo-3.1-generate-preview`).

| Model Tier | Cost per Second | Estimated Cost (30s Ad) | Daily Cost (10 Ads) |
| :--- | :--- | :--- | :--- |
| **Veo 3.1 Fast** | $0.15 | **$4.50** | $45.00 |
| **Veo 3.1 Standard** | $0.40 | **$12.00** | $120.00 |

### Recommended Plan for 10 Ads/Day:
Use the **Pay-As-You-Go** model in Google AI Studio or Vertex AI. 
- **Monthly Spend:** ~$1,350 (Fast) to ~$3,600 (Standard).

---

## 2. Runway Gen-3 Alpha Pricing
Runway is a highly competitive alternative, especially for high-volume testing of 10 ads/day.

| Model Tier | Credits/Sec | Cost per Second | Estimated Cost (30s Ad) | Daily Cost (10 Ads) |
| :--- | :--- | :--- | :--- | :--- |
| **Gen-3 Alpha Turbo** | 5 | **$0.05** | **$1.50** | $15.00 |
| **Gen-3 Alpha** | 10 | **$0.10** | **$3.00** | $30.00 |

### Runway Model Comparison: Turbo vs. Standard

| Feature | Gen-3 Alpha **Turbo** | Gen-3 Alpha **Standard** |
| :--- | :--- | :--- |
| **Render Speed** | **7x Faster** (Real-time feel) | Standard Speed |
| **Cost** | **50% Cheaper** (5 credits/sec) | 10 credits/sec |
| **Primary Input** | **Image-to-Video** (Best results) | Text-to-Video & Image-to-Video |
| **Consistency** | High (follows input image closely) | High (better for complex physics) |
| **Best Use Case** | **Product Ads**, E-commerce Reels | Cinematic Brand Films, Complex Characters |

**Why choose Turbo?** For your project (10 ads/day), Turbo is the superior choice because it is designed for Image-to-Video. Since your agents already gather product and lifestyle images, Turbo will transform those images into high-quality videos faster and cheaper than the standard model.

### Profit / Cost Advantage:
Switching to Runway Gen-3 Alpha Turbo can save you **66% to 88%** on generation costs.
- **Gemini (10 ads/day):** ~$1,350/mo.
- **Runway Turbo (10 ads/day):** **~$450/mo.**
- **Performance:** Runway Gen-3 Turbo is significantly faster than Gemini Veo 3.1 Standard and is specifically optimized for high-speed, image-to-video, and text-to-video workloads.

---

## 3. How to Buy & Setup
### Option A: Gemini API (Current)
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Enable Billing and generate an API Key.
3. Save to `.env` as `GEMINI_API_KEY`.

### Option B: Runway API (Recommended for Cost)
1. Sign up at [RunwayML](https://runwayml.com/).
2. Buy a **Standard or Pro Plan** (includes monthly credits) or purchase **Credits** as needed ($0.01 per credit).
3. Generate an API Key from the Runway Developer Portal.
4. Update the code to use the Runway SDK or HTTP API.

> [!TIP]
> **Suggested Strategy:** For testing 10 ads/day, **Runway Gen-3 Alpha Turbo** is the most cost-effective solution ($15/day). It offers a professional look at a fraction of the cost of Gemini Standard ($120/day).
