from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.trendyol.com/",
    "Origin": "https://www.trendyol.com",
}

class SearchRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {"status": "NetKarar Backend Çalışıyor"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/search")
async def search(q: str):
    try:
        url = f"https://public.trendyol.com/discovery-web-searchgw-service/api/infinite-scroll/v2/search?q={q}&pi=1&culture=tr-TR"
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                products = data.get("result", {}).get("products", [])
                if products:
                    p = products[0]
                    price = p.get("price", {})
                    rating = p.get("ratingScore", {})
                    images = p.get("images", [])
                    return {
                        "success": True,
                        "product": {
                            "title": p.get("name", ""),
                            "price": price.get("discountedPrice", price.get("sellingPrice", 0)),
                            "originalPrice": price.get("originalPrice", 0),
                            "rating": rating.get("averageRating", 0),
                            "reviewCount": rating.get("totalCount", 0),
                            "sellerName": p.get("merchantName", ""),
                            "brand": p.get("brand", {}).get("name", p.get("brandName", "")),
                            "imageUrl": f"https://cdn.dsmcdn.com{images[0]}" if images else "",
                            "url": f"https://www.trendyol.com{p.get('url', '')}",
                        }
                    }
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/product")
async def product_detail(url: str):
    try:
        import re
        content_id_match = re.search(r'-p-(\d+)', url)
        if not content_id_match:
            return {"success": False, "error": "Geçersiz URL"}
        
        content_id = content_id_match.group(1)
        api_url = f"https://public.trendyol.com/discovery-web-productgw-service/api/productDetail/{content_id}"
        
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            response = await client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                price_info = result.get("priceInfo", {})
                rating = result.get("ratingScore", {})
                images = result.get("images", [])
                merchant = result.get("merchant", {})
                
                return {
                    "success": True,
                    "product": {
                        "title": result.get("name", ""),
                        "price": price_info.get("discountedPrice", price_info.get("price", 0)),
                        "originalPrice": price_info.get("originalPrice", 0),
                        "rating": rating.get("averageRating", 0),
                        "reviewCount": rating.get("totalCount", 0),
                        "sellerName": merchant.get("name", ""),
                        "sellerScore": merchant.get("score", 0),
                        "brand": result.get("brand", {}).get("name", ""),
                        "imageUrl": f"https://cdn.dsmcdn.com{images[0]}" if images else "",
                        "url": url,
                        "description": result.get("description", ""),
                    }
                }
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
