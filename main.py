#!/usr/bin/env python3
"""
Local Admin API for 進行垢・引退垢・BOX公開アカウントサイト
Run on Windows 11:
  pip install -r requirements.txt
  uvicorn main:app --reload --host 127.0.0.1 --port 8000

Then open:
  http://127.0.0.1:8000/          → 公開ページ
  http://127.0.0.1:8000/admin     → 管理ページ
  http://127.0.0.1:8000/docs      → APIドキュメント
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from pathlib import Path
import json
import uuid
import subprocess
from datetime import datetime
from contextlib import asynccontextmanager

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
GAMES_FILE = DATA_DIR / "games.json"
PRODUCTS_FILE = DATA_DIR / "products.json"

DATA_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

# Fallback data (used only when JSON files are missing)
FALLBACK_GAMES = [
    {"id": "monst", "name": "モンスト", "fullName": "モンスターストライク", "icon": "M"},
    {"id": "prospi", "name": "プロスピA", "fullName": "プロ野球スピリッツA", "icon": "⚾"},
    {"id": "fanpare", "name": "ファンパレ", "fullName": "呪術廻戦 ファントムパレード", "icon": "呪"},
    {"id": "bounty", "name": "バウンティ", "fullName": "バウンティラッシュ", "icon": "☠"},
]

FALLBACK_PRODUCTS = [
    {
        "id": "monst-001",
        "gameId": "monst",
        "gameName": "モンスターストライク",
        "title": "限定キャラ多数・オーブ4,417個",
        "description": "ネオ、マサムネ、ルシファーなど人気限定キャラを多数所持。BOX画像はすべて確認できます。",
        "price": 7500,
        "images": [],
        "xUrl": "https://x.com/tools_A_",
        "lineUrl": "#",
    },
    {
        "id": "prospi-001",
        "gameId": "prospi",
        "gameName": "プロ野球スピリッツA",
        "title": "Sランク選手多数・育成済みオーダー",
        "description": "リーグ・リアタイの両方に使いやすい選手を複数所持。育成状況は詳細画像で確認できます。",
        "price": 12800,
        "images": [],
        "xUrl": "https://x.com/tools_A_",
        "lineUrl": "#",
    },
    {
        "id": "bounty-001",
        "gameId": "bounty",
        "gameName": "バウンティラッシュ",
        "title": "超フェス複数・育成済みキャラ多数",
        "description": "主要キャラクターのレベル・メダル・サポート編成を画像で確認できます。",
        "price": 9800,
        "images": [],
        "xUrl": "https://x.com/tools_A_",
        "lineUrl": "#",
    },
    {
        "id": "fanpare-001",
        "gameId": "fanpare",
        "gameName": "呪術廻戦 ファントムパレード",
        "title": "限定SSR複数・高戦力編成",
        "description": "育成済みキャラクターと廻想残滓を複数所持。画像をタップすると登録画像を確認できます。",
        "price": 6500,
        "images": [],
        "xUrl": "https://x.com/tools_A_",
        "lineUrl": "#",
    },
]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 8 * 1024 * 1024  # 8MB


def atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically using a temporary file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def load_json(path: Path, fallback: list) -> list:
    if not path.exists():
        atomic_write_json(path, fallback)
        return [item.copy() for item in fallback]
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        atomic_write_json(path, fallback)
        return [item.copy() for item in fallback]


def save_games(games: list) -> None:
    atomic_write_json(GAMES_FILE, games)


def save_products(products: list) -> None:
    atomic_write_json(PRODUCTS_FILE, products)


# ============ Pydantic Models ============
class GameCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    fullName: Optional[str] = Field(default=None, max_length=200)
    icon: str = Field(default="●", max_length=10)


class GameUpdate(BaseModel):
    name: Optional[str] = None
    fullName: Optional[str] = None
    icon: Optional[str] = None


class ProductBase(BaseModel):
    gameId: str
    gameName: str
    title: str
    description: str
    price: int = Field(..., ge=0)
    images: List[str] = []
    xUrl: str = "#"
    lineUrl: str = "#"


class ProductCreate(ProductBase):
    id: Optional[str] = None  # auto-generate if missing


class ProductUpdate(BaseModel):
    gameId: Optional[str] = None
    gameName: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    xUrl: Optional[str] = None
    lineUrl: Optional[str] = None


# ============ App lifespan ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure initial data files exist (do not overwrite existing with data URLs)
    if not GAMES_FILE.exists():
        load_json(GAMES_FILE, FALLBACK_GAMES)
    if not PRODUCTS_FILE.exists():
        load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)
    yield


app = FastAPI(
    title="Account Sales Local Admin API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static images
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


# ============ API: Games ============
@app.get("/api/games")
async def get_games():
    return load_json(GAMES_FILE, FALLBACK_GAMES)


@app.post("/api/games")
async def create_game(game: GameCreate):
    games = load_json(GAMES_FILE, FALLBACK_GAMES)
    if any(g["id"] == game.id for g in games):
        raise HTTPException(status_code=400, detail=f"Game id '{game.id}' already exists")
    new_game = game.model_dump()
    games.append(new_game)
    save_games(games)
    return new_game


@app.put("/api/games/{game_id}")
async def update_game(game_id: str, update: GameUpdate):
    games = load_json(GAMES_FILE, FALLBACK_GAMES)
    for i, g in enumerate(games):
        if g["id"] == game_id:
            data = update.model_dump(exclude_unset=True)
            games[i].update(data)
            save_games(games)
            return games[i]
    raise HTTPException(status_code=404, detail="Game not found")


@app.delete("/api/games/{game_id}")
async def delete_game(game_id: str):
    games = load_json(GAMES_FILE, FALLBACK_GAMES)
    products = load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)
    if any(p.get("gameId") == game_id for p in products):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete game that has products. Delete products first.",
        )
    new_games = [g for g in games if g["id"] != game_id]
    if len(new_games) == len(games):
        raise HTTPException(status_code=404, detail="Game not found")
    save_games(new_games)
    return {"ok": True, "deleted": game_id}


# ============ API: Products ============
@app.get("/api/products")
async def get_products():
    return load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)


@app.post("/api/products")
async def create_product(product: ProductCreate):
    products = load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)
    new_id = product.id or f"{product.gameId}-{uuid.uuid4().hex[:6]}"
    if any(p["id"] == new_id for p in products):
        raise HTTPException(status_code=400, detail=f"Product id '{new_id}' already exists")
    data = product.model_dump()
    data["id"] = new_id
    products.append(data)
    save_products(products)
    return data


@app.put("/api/products/{product_id}")
async def update_product(product_id: str, update: ProductUpdate):
    products = load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)
    for i, p in enumerate(products):
        if p["id"] == product_id:
            data = update.model_dump(exclude_unset=True)
            products[i].update(data)
            save_products(products)
            return products[i]
    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str):
    products = load_json(PRODUCTS_FILE, FALLBACK_PRODUCTS)
    target = next((p for p in products if p["id"] == product_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Product not found")

    # Remove associated image files if under images/
    for img_path in target.get("images", []):
        if isinstance(img_path, str) and img_path.startswith("images/"):
            full = BASE_DIR / img_path
            if full.exists() and full.is_file():
                try:
                    full.unlink()
                except Exception:
                    pass

    new_products = [p for p in products if p["id"] != product_id]
    save_products(new_products)
    return {"ok": True, "deleted": product_id}


# ============ API: Upload (drag & drop / multi) ============
@app.post("/api/upload")
async def upload_images(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    saved_paths: List[str] = []
    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest = IMAGES_DIR / unique_name

        try:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)",
                )
            with open(dest, "wb") as f:
                f.write(content)
            saved_paths.append(f"images/{unique_name}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}: {str(e)}")

    return {"paths": saved_paths}


# ============ Git / GitHub publish helpers ============
def run_git(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "git コマンドが見つかりません。Git for Windows をインストールしてください。"
    except subprocess.TimeoutExpired:
        return 124, "", "git コマンドがタイムアウトしました。"
    except Exception as e:
        return 1, "", str(e)


def is_git_repo() -> bool:
    code, out, _ = run_git(["rev-parse", "--is-inside-work-tree"])
    return code == 0 and out.lower() == "true"


class PublishRequest(BaseModel):
    message: Optional[str] = None


@app.get("/api/git/status")
async def git_status():
    if not is_git_repo():
        return {
            "is_repo": False,
            "dirty": False,
            "message": "このフォルダは Git リポジトリではありません。先に git init と remote 設定を行ってください。",
            "files": [],
        }
    code, out, err = run_git(["status", "--porcelain", "--", "data/", "images/"])
    files = [line for line in out.splitlines() if line.strip()] if code == 0 else []
    return {
        "is_repo": True,
        "dirty": len(files) > 0,
        "files": files,
        "message": "変更があります" if files else "公開待ちの変更はありません",
        "error": err if code != 0 else None,
    }


@app.post("/api/git/publish")
async def git_publish(payload: PublishRequest = Body(default=PublishRequest())):
    if not is_git_repo():
        raise HTTPException(
            status_code=400,
            detail="このフォルダは Git リポジトリではありません。先に `git init` と `git remote add origin ...` を実行してください。",
        )

    message = (payload.message or "").strip()
    if not message:
        message = f"Update products via admin - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    logs: list[str] = []

    # 1. add only data/ and images/
    code, out, err = run_git(["add", "data/", "images/"])
    logs.append(f"[git add] code={code}")
    if out:
        logs.append(out)
    if err:
        logs.append(err)
    if code != 0:
        raise HTTPException(status_code=500, detail="git add に失敗しました:\n" + "\n".join(logs))

    # 2. check if there is anything to commit
    code, out, err = run_git(["status", "--porcelain", "--", "data/", "images/"])
    if code == 0 and not out.strip():
        return {
            "ok": True,
            "committed": False,
            "pushed": False,
            "message": "変更がありませんでした。既に最新の状態です。",
            "logs": logs,
        }

    # 3. commit
    code, out, err = run_git(["commit", "-m", message])
    logs.append(f"[git commit] code={code}")
    if out:
        logs.append(out)
    if err:
        logs.append(err)
    if code != 0:
        # nothing to commit is sometimes exit 1
        if "nothing to commit" in (out + err).lower():
            return {
                "ok": True,
                "committed": False,
                "pushed": False,
                "message": "コミットする変更がありませんでした。",
                "logs": logs,
            }
        raise HTTPException(status_code=500, detail="git commit に失敗しました:\n" + "\n".join(logs))

    # 4. push
    code, out, err = run_git(["push"], timeout=90)
    logs.append(f"[git push] code={code}")
    if out:
        logs.append(out)
    if err:
        logs.append(err)

    if code == 0:
        return {
            "ok": True,
            "committed": True,
            "pushed": True,
            "message": "GitHub への push が完了しました。GitHub Pages の反映まで1〜3分かかることがあります。",
            "logs": logs,
        }

    # push failed → still report that commit succeeded
    return {
        "ok": True,
        "committed": True,
        "pushed": False,
        "message": (
            "コミットまでは成功しましたが、push に失敗しました。\n"
            "ターミナルで手動で `git push` を実行してください。\n\n"
            f"詳細:\n{err or out or '認証エラーの可能性があります。Git Credential Manager を確認してください。'}"
        ),
        "logs": logs,
    }


# ============ Static HTML serving ============
@app.get("/")
async def serve_index():
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/admin")
@app.get("/admin.html")
async def serve_admin():
    admin_path = BASE_DIR / "admin.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    raise HTTPException(status_code=404, detail="admin.html not found")


@app.get("/data/games.json")
async def serve_games_json():
    if GAMES_FILE.exists():
        return FileResponse(GAMES_FILE)
    return JSONResponse(FALLBACK_GAMES)


@app.get("/data/products.json")
async def serve_products_json():
    if PRODUCTS_FILE.exists():
        return FileResponse(PRODUCTS_FILE)
    return JSONResponse(FALLBACK_PRODUCTS)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
