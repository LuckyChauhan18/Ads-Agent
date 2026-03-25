# Runway API Billing & Model Selection Guide

Complete guide to Runway pricing, models, and which one to use for your LangGraph ad generation app.

---

## 💰 Runway Billing System Explained

### **How Credits Work:**

Runway uses a **credit-based billing system** where credits can be purchased for **$0.01 per credit** ($10 for 1,000 credits)

**Key Points:**
- 1 credit = $0.01 (one cent)
- Credits are consumed based on: **model used** + **video duration** + **resolution**
- Formula: `Total Cost = (Credits per second) × (Video duration) × ($0.01)`

---

## 🎬 Available Models & Pricing (API)

### **Gen-3 Models (Older Generation)**

| Model                 | Credits/Second | Cost/Second | T2V | I2V | Best For                          |
| --------------------- | -------------- | ----------- | --- | --- | --------------------------------- |
| **Gen-3 Alpha**       | 10 credits     | $0.10       | ✅   | ✅   | High quality, text-only prompts   |
| **Gen-3 Alpha Turbo** | 5 credits      | $0.05       | ❌   | ✅   | **Budget option, requires image** |

**Key Differences:**
- Gen-3 Alpha Turbo requires an input image (Image-to-Video only)
- Gen-3 Alpha supports Text-to-Video without image
- Turbo is "7× faster and at half the price" of Alpha

---

### **Gen-4 Models (Latest Generation - 2025)**

| Model           | Credits/Second | Cost/Second | T2V | I2V | Best For                            |
| --------------- | -------------- | ----------- | --- | --- | ----------------------------------- |
| **Gen-4 Aleph** | 15 credits     | $0.15       | ✅   | ✅   | **Premium quality, highest detail** |
| **Gen-4 Video** | 12 credits     | $0.12       | ✅   | ✅   | High quality, standard choice       |
| **Gen-4 Turbo** | 5 credits      | $0.05       | ✅   | ✅   | **Fast & affordable**               |
| **Gen-4.5**     | ~25 credits    | $0.25       | ✅   | ✅   | Latest, highest quality             |

**Gen-4 Advantages:**
- Better consistency and controllability, especially for persistent characters/locations when guided by input image
- All Gen-4 models support both Text-to-Video and Image-to-Video
- 24 fps output

---

### **Image Generation**

| Model                   | Credits/Image | Cost/Image | Resolution     |
| ----------------------- | ------------- | ---------- | -------------- |
| **Gen-4 Image (1080p)** | 8 credits     | $0.08      | 1080p          |
| **Gen-4 Image (720p)**  | 5 credits     | $0.05      | 720p           |
| **Gen-4 Image Turbo**   | 2 credits     | $0.02      | Any resolution |

---

### **Additional Features**

| Feature                           | Credits                    | Cost               |
| --------------------------------- | -------------------------- | ------------------ |
| **4K Upscaling**                  | 2 credits/second           | $0.02/sec          |
| **Text-to-Speech**                | 1 credit per 50 characters | $0.01 per 50 chars |
| **Act-Two (performance capture)** | 5 credits/second           | $0.05/sec          |

---

## 💡 Which Model Should YOU Use?

### **For Your LangGraph Ad Generation App:**

Based on your requirements (30s ads, 4-5 scenes, brand quality):

### **🏆 RECOMMENDED: Gen-3 Alpha Turbo**

**Why This is Best:**
- ✅ **Cheapest option:** 5 credits/second = $0.05/second
- ✅ **Perfect for I2V:** Requires image input = exactly what you need for product/logo scenes
- ✅ **7x faster** than Gen-3 Alpha
- ✅ **Same quality** for Image-to-Video use cases
- ✅ **Best value for money**

**Limitations:**
- ❌ Requires input image (but that's what you want for I2V anyway!)
- ❌ Cannot do pure Text-to-Video

**Solution:**
Use **hybrid approach**:
- **Gen-3 Alpha Turbo** for product/logo scenes (I2V) = $0.05/sec
- **Gen-3 Alpha** for lifestyle/problem scenes (T2V) = $0.10/sec

---

### **Alternative: Gen-4 Turbo (If You Want Latest Tech)**

**Why Consider:**
- ✅ Latest generation model
- ✅ Better character/location consistency
- ✅ Still affordable at 5 credits/second
- ✅ Supports both T2V and I2V

**When to Use:**
- If you need absolute best quality
- If brand consistency is CRITICAL
- If budget allows slightly higher cost

**Cost:** Same as Gen-3 Alpha Turbo ($0.05/sec)

---

## 📊 Cost Comparison: Your 30s Ad

### **Scenario: 30-second ad with 5 scenes (6s each)**

**Option 1: Pure Gen-3 Alpha (T2V only)**
```
5 scenes × 6 seconds × 10 credits/sec = 300 credits
Cost: 300 × $0.01 = $3.00 per ad
```

**Option 2: Hybrid Gen-3 (Alpha + Turbo) - RECOMMENDED**
```
Lifestyle scenes (2 scenes, T2V with Alpha):
2 × 6s × 10 credits/sec = 120 credits = $1.20

Product scenes (3 scenes, I2V with Turbo):
3 × 6s × 5 credits/sec = 90 credits = $0.90

Total: 210 credits = $2.10 per ad ✅
Savings: 30% cheaper than pure Alpha
```

**Option 3: Pure Gen-3 Alpha Turbo (I2V only)**
```
5 scenes × 6 seconds × 5 credits/sec = 150 credits
Cost: 150 × $0.01 = $1.50 per ad ✅ CHEAPEST
```

**Option 4: Gen-4 Turbo (Latest)**
```
5 scenes × 6 seconds × 5 credits/sec = 150 credits
Cost: 150 × $0.01 = $1.50 per ad
Same cost as Gen-3 Turbo, better quality
```

**Option 5: Gen-4 Aleph (Premium)**
```
5 scenes × 6 seconds × 15 credits/sec = 450 credits
Cost: 450 × $0.01 = $4.50 per ad ❌ EXPENSIVE
```

---

## 🎯 My Recommendation for Your App

### **Use Gen-3 Alpha Turbo (Primary) + Gen-3 Alpha (Fallback)**

**Implementation Strategy:**

```python
# agents/production/runway_renderer/base.py

MODEL_CONFIG = {
    "primary_i2v": "gen3a_turbo",      # 5 credits/sec - for product/logo
    "fallback_t2v": "gen3a",           # 10 credits/sec - for lifestyle
    "premium": "gen4_turbo"             # 5 credits/sec - optional upgrade
}

def select_model(self, scene_data: dict) -> str:
    """
    Smart model selection based on scene type.
    """
    
    # If we have product/logo asset → Use Turbo (I2V)
    if self._should_use_i2v(scene_data):
        return MODEL_CONFIG["primary_i2v"]  # gen3a_turbo
    
    # If no asset, need T2V → Use Alpha
    else:
        return MODEL_CONFIG["fallback_t2v"]  # gen3a
    
    # Optional: Premium scenes
    # if scene_data.get("premium_quality"):
    #     return MODEL_CONFIG["premium"]  # gen4_turbo
```

---

## 💰 Monthly Cost Projections

### **Based on Your Usage:**

**Assumptions:**
- Average 30s ad per generation
- Mix of T2V (40%) and I2V (60%) scenes
- Using Gen-3 Turbo for I2V, Gen-3 Alpha for T2V

| Daily Ads | Monthly Ads | Credits/Month | Cost/Month | Annual Cost |
| --------- | ----------- | ------------- | ---------- | ----------- |
| 1 ad      | 30 ads      | 6,300         | $63        | $756        |
| 5 ads     | 150 ads     | 31,500        | $315       | $3,780      |
| 10 ads    | 300 ads     | 63,000        | $630       | $7,560      |
| 20 ads    | 600 ads     | 126,000       | $1,260     | $15,120     |
| 50 ads    | 1,500 ads   | 315,000       | $3,150     | $37,800     |

**Calculation:**
```
Per ad: 210 credits (hybrid approach)
Monthly: Daily ads × 30 × 210 credits × $0.01
```

---

## 📦 Runway Subscription Plans (For Reference)

**Note:** For API usage, you can just buy credits directly. Plans are for web UI users.

| Plan           | Monthly Cost       | Credits/Month                  | Best For                    |
| -------------- | ------------------ | ------------------------------ | --------------------------- |
| **Free**       | $0                 | 125 (one-time)                 | Testing only                |
| **Standard**   | $12/month (annual) | 625 credits                    | Hobbyists (~3 ads/month)    |
| **Pro**        | $28/month (annual) | 2,250 credits                  | Small teams (~10 ads/month) |
| **Unlimited**  | $76/month (annual) | 2,250 credits + Unlimited slow | Power users                 |
| **Enterprise** | Custom             | Custom                         | Large orgs                  |

**For API Users:**
You can purchase credits directly in the developer portal for $0.01 per credit

---

## 🚨 Important Billing Notes

### **Credits Don't Roll Over:**
Monthly credits reset at the beginning of each billing cycle - unused credits expire and don't roll over

**Exception:** Purchased credits (bought separately) have no expiration date

### **Shared Workspace Credits:**
Credits are shared across your workspace (not per user)

---

## 🔧 API Implementation

### **Example: Calling Runway API**

```python
import requests
import os

RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
API_URL = "https://api.runwayml.com/v1"

def generate_video(prompt: str, duration: int, model: str = "gen3a_turbo", image: str = None):
    """
    Generate video using Runway API.
    
    Args:
        prompt: Text prompt or motion description
        duration: Video duration in seconds (max 10s for single gen)
        model: "gen3a", "gen3a_turbo", "gen4_turbo", etc.
        image: Base64 image (required for Turbo models)
    """
    
    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
    }
    
    # Add image for I2V models
    if image and "turbo" in model.lower():
        payload["image"] = image
    
    # Submit generation request
    response = requests.post(
        f"{API_URL}/generate",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        raise Exception(f"Runway API error: {response.text}")
    
    task_id = response.json()["id"]
    
    # Poll for completion
    return poll_runway_result(task_id)


def poll_runway_result(task_id: str, max_wait: int = 600) -> str:
    """
    Poll Runway API until video is ready.
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{API_URL}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {RUNWAY_API_KEY}"}
        )
        
        data = response.json()
        status = data["status"]
        
        if status == "succeeded":
            return data["output"]["url"]
        elif status == "failed":
            raise Exception(f"Generation failed: {data.get('error')}")
        
        time.sleep(10)  # Check every 10 seconds
    
    raise Exception(f"Timeout after {max_wait}s")


# Example usage
video_url = generate_video(
    prompt="Product rotating on clean background",
    duration=6,
    model="gen3a_turbo",
    image="base64_encoded_product_image_here"
)
```

---

## 📊 Cost Optimization Tips

### **1. Use the Right Model:**
- ✅ **Gen-3 Alpha Turbo** for I2V (product shots) = 50% cheaper
- ✅ **Gen-4 Turbo** for premium quality at same Turbo price
- ❌ Avoid Gen-4 Aleph unless absolutely necessary (3x more expensive)

### **2. Optimize Video Length:**
- Generate minimum viable lengths
- Use 5-6 second scenes instead of 8-10 seconds
- Extensions cost the same as initial generation, so generate once

### **3. Avoid Unnecessary Upscaling:**
- 4K upscaling costs 2 credits/second extra
- Only upscale final approved videos
- Export at 1080p for social media (no upscale needed)

### **4. Batch Processing:**
- Generate multiple variants at once
- Take advantage of parallel API calls
- Reduce iteration overhead

---

## 🎯 Final Recommendation Summary

### **For Your LangGraph App:**

**Primary Model:** **Gen-3 Alpha Turbo**
- Best value: $0.05/second
- Perfect for Image-to-Video (product/logo scenes)
- 7x faster than regular Gen-3 Alpha

**Fallback Model:** **Gen-3 Alpha**
- For Text-to-Video (lifestyle/problem scenes)
- $0.10/second
- When no product image available

**Optional Upgrade:** **Gen-4 Turbo**
- Latest technology
- Same price as Gen-3 Alpha Turbo ($0.05/sec)
- Better consistency for characters/locations

**Expected Cost:**
- **Per 30s ad:** $1.50 - $2.10
- **Monthly (10 ads/day):** ~$630
- **Annual (10 ads/day):** ~$7,560

**Implementation Priority:**
1. ✅ Implement Gen-3 Alpha Turbo for I2V scenes
2. ✅ Keep Gen-3 Alpha for T2V scenes
3. ✅ Add model selection logic based on scene type
4. ⏭️ Later: Upgrade to Gen-4 Turbo for better quality

---

## 📝 Quick Reference

**Model Selection Cheat Sheet:**

```
Product shot → Gen-3 Alpha Turbo (I2V) → $0.05/sec
Logo reveal → Gen-3 Alpha Turbo (I2V) → $0.05/sec
Lifestyle scene → Gen-3 Alpha (T2V) → $0.10/sec
Problem scene → Gen-3 Alpha (T2V) → $0.10/sec
Premium quality → Gen-4 Turbo → $0.05/sec
```

**Your 30s Ad Cost:**
```
Hybrid approach: $2.10 per ad
Pure Turbo: $1.50 per ad (if all I2V)
Pure Alpha: $3.00 per ad (if all T2V)
```

**Compared to Google Veo:**
```
Veo 3.1: Unknown pricing (likely $0.08-0.15/sec)
Runway Turbo: $0.05/sec ✅ BETTER
```

---

**Want me to implement the Runway integration with Gen-3 Alpha Turbo in your code?** 🚀
