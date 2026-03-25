"""
Asset Verification Script — Checks if product images and logos
are correctly stored in MongoDB GridFS and retrievable by the renderer.
NO API calls (no Veo, no ElevenLabs).
"""
import asyncio, os, sys, json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asset_check.json")

async def check():
    from api.services.db_mongo_service import connect_to_mongo, close_mongo_connection, mongo, get_user_assets, get_file_from_gridfs

    r = {"campaigns": [], "assets": [], "test_downloads": [], "renderer_simulation": {}}

    await connect_to_mongo()
    if mongo.db is None:
        r["error"] = "MongoDB connection failed"
        json.dump(r, open(RESULT, "w"), indent=2)
        return

    # 1. List campaigns to get user_id
    print("[1] Listing campaigns...")
    async for c in mongo.db.campaigns.find({}):
        cid = c.get("campaign_id", str(c.get("_id","")))
        uid = str(c.get("user_id", ""))
        r["campaigns"].append({"campaign_id": cid, "user_id": uid})
        print(f"    Campaign: {cid} | User: {uid}")

    if not r["campaigns"]:
        print("    No campaigns found!")

    # 2. List ALL assets in user_assets (GridFS metadata)
    print("\n[2] Checking user_assets collection...")
    cursor = mongo.db["fs.files"].find({})
    async for doc in cursor:
        meta = doc.get("metadata", {})
        entry = {
            "file_id": str(doc["_id"]),
            "filename": doc.get("filename", "?"),
            "size_bytes": doc.get("length", 0),
            "asset_type": meta.get("asset_type"),
            "type": meta.get("type"),
            "campaign_id": meta.get("campaign_id"),
            "user_id": meta.get("user_id"),
            "content_type": meta.get("content_type"),
        }
        r["assets"].append(entry)
        effective_type = entry["asset_type"] or entry["type"] or "unknown"
        print(f"    {entry['filename']} | type={effective_type} | campaign={entry['campaign_id']} | size={entry['size_bytes']//1024}KB")

    if not r["assets"]:
        print("    NO ASSETS FOUND in GridFS!")

    # 3. Test download first asset of each type
    print("\n[3] Test downloading assets from GridFS...")
    for asset in r["assets"][:5]:
        fid = asset["file_id"]
        try:
            data, content_type = await get_file_from_gridfs(fid)
            ok = data is not None and len(data) > 0
            r["test_downloads"].append({
                "file_id": fid,
                "filename": asset["filename"],
                "download_ok": ok,
                "bytes": len(data) if data else 0,
                "content_type": content_type
            })
            print(f"    {asset['filename']}: {'OK' if ok else 'FAIL'} ({len(data)//1024}KB)" if data else f"    {asset['filename']}: FAIL (None)")
        except Exception as e:
            r["test_downloads"].append({"file_id": fid, "error": str(e)})
            print(f"    {asset['filename']}: ERROR - {e}")

    # 4. Simulate renderer _load_assets
    print("\n[4] Simulating renderer asset loading...")
    if r["campaigns"]:
        uid = r["campaigns"][0]["user_id"]
        cid = r["campaigns"][0]["campaign_id"]
        
        loaded = {"product": [], "logo": [], "lifestyle": []}
        try:
            items = await get_user_assets(uid)
            print(f"    get_user_assets({uid}) returned {len(items)} items")
            for item in items:
                metadata = item.get("metadata", {})
                item_campaign_id = metadata.get("campaign_id")
                
                if cid and item_campaign_id and str(item_campaign_id) != str(cid):
                    print(f"    SKIP: {item.get('filename')} (campaign mismatch: {item_campaign_id} != {cid})")
                    continue
                
                a_type = metadata.get("asset_type") or metadata.get("type")
                file_id = str(item["_id"])
                if a_type in loaded:
                    loaded[a_type].append(file_id)
                    print(f"    LOADED: {item.get('filename')} as '{a_type}' -> {file_id}")
                else:
                    print(f"    IGNORED: {item.get('filename')} (type={a_type}, not in [product,logo,lifestyle])")
            
            r["renderer_simulation"] = {
                "user_id": uid,
                "campaign_id": cid,
                "products_found": len(loaded["product"]),
                "logos_found": len(loaded["logo"]),
                "lifestyle_found": len(loaded["lifestyle"]),
            }
            print(f"\n    RESULT: {len(loaded['product'])} products, {len(loaded['logo'])} logos, {len(loaded['lifestyle'])} lifestyle")
        except Exception as e:
            r["renderer_simulation"]["error"] = str(e)
            print(f"    ERROR: {e}")

    # Save
    with open(RESULT, "w") as f:
        json.dump(r, f, indent=2)
    
    print(f"\nFull results: {RESULT}")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(check())
