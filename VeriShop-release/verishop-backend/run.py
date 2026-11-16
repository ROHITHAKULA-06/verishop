"""VeriShop Backend — Dev Server Launcher"""
import uvicorn
from app.config import Settings

settings = Settings()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
